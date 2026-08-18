import hashlib
import re
import uuid
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models import CVAnalizRecord
from app.services.pdf_parser import extract_text_from_pdf
from app.services.llm import (
    llm_client,
    CV_ANALYSIS_SYSTEM_PROMPT,
    CV_ANALYSIS_USER_TEMPLATE,
    POSITION_CRITERIA_SYSTEM_PROMPT,
    POSITION_CRITERIA_USER_TEMPLATE,
)
from app.services.cv_analiz import cv_analiz_et

logger = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# Criteria Caching (Single-Pass mimarisi)
# ---------------------------------------------------------------------------
# Basit bellek içi (in-process) cache. Proje raporunda tarif edilen hedef
# mimaride bu, Redis'e (cache.py / CacheService) taşınabilir; ancak
# CacheService şu an cv.py'ye entegre değil (bkz. proje raporu Bölüm 7).
# Bu yüzden burada minimal, bağımlılıksız bir sözlük kullanıyoruz.
# Süreç yeniden başlatıldığında cache sıfırlanır — kalıcılık gerekiyorsa
# CRITERIA_CACHE, cache_service.set_session ile aynı desende Redis'e
# taşınmalıdır (bkz. Öncelik 1 yol haritası).
CRITERIA_CACHE: Dict[str, Dict[str, Any]] = {}


def _normalize_for_hash(text: str) -> str:
    """Metni hash'lemeden önce normalize eder: baş/son boşlukları kırpar,
    küçük harfe çevirir ve ardışık boşluk/satır sonlarını tek boşluğa
    indirger. Böylece aynı iş ilanı metni, kopyala-yapıştır sırasında
    oluşan fazladan boşluk/satır sonu/büyük-küçük harf farkları yüzünden
    gereksiz yere farklı bir cache anahtarına düşmez."""
    return re.sub(r"\s+", " ", text.strip().lower())


def _criteria_cache_key(job_position: str, job_description: Optional[str] = None) -> str:
    """Cache anahtarını hem pozisyon adından HEM DE (varsa) iş ilanı
    metninden üretir.

    BUG FIX (kod incelemesinde tespit edildi): Eski sürümde anahtar
    yalnızca pozisyon adına dayanıyordu. Bu durumda örn. "Backend
    Developer" + Python ilanı ile "Backend Developer" + Java ilanı aynı
    cache girdisini paylaşıyor, ikinci istekte YANLIŞ kriterler (ilk
    isteğin kriterleri) sessizce kullanılıyordu. Artık job_description da
    (normalize edilip hash'lenerek) anahtara dahil ediliyor; böylece
    farklı ilan içerikleri kesinlikle farklı cache girdileri üretir,
    aynı ilan farklı şekilde yapıştırılsa bile (boşluk/case farkları)
    gereksiz cache MISS oluşmaz."""
    pos_key = job_position.strip().lower()
    if job_description and job_description.strip():
        desc_hash = hashlib.md5(
            _normalize_for_hash(job_description).encode("utf-8")
        ).hexdigest()[:8]
        return f"{pos_key}:{desc_hash}"
    return pos_key


async def _get_or_create_position_criteria(
    job_position: str, job_description: Optional[str]
) -> Dict[str, Any]:
    """
    Single-Pass + Criteria Caching:
      - Cache HIT: kriterleri LLM'e gitmeden doğrudan bellekten döner (0ms).
      - Cache MISS: LLM'e TEK bir istek atarak pozisyona özel 5 kritik
        kriteri, anahtar kelimeleri ve seviye göstergelerini tek seferde
        (single-pass) ürettirir, sonucu cache'e yazar ve döner.

    LLM çağrısı başarısız olursa (timeout, geçersiz JSON vb.) istisna
    yutulmaz; çağıran taraf (cv_analiz_endpoint) bunu genel CV analizi
    fallback akışına dahil edecek şekilde ele alır.
    """
    cache_key = _criteria_cache_key(job_position, job_description)

    cached = CRITERIA_CACHE.get(cache_key)
    if cached is not None:
        logger.info("Kriter cache HIT: '%s'", cache_key)
        return cached

    logger.info("Kriter cache MISS: '%s' — LLM'den single-pass kriter üretiliyor.", cache_key)
    prompt = POSITION_CRITERIA_USER_TEMPLATE.format(
        job_position=job_position,
        job_description=job_description or "(İş ilanı metni verilmedi — pozisyon adına göre çıkarım yap.)",
    )
    criteria = await llm_client.generate_json(
        prompt=prompt,
        system_prompt=POSITION_CRITERIA_SYSTEM_PROMPT,
    )
    CRITERIA_CACHE[cache_key] = criteria
    return criteria


def _build_job_context(
    job_position: Optional[str],
    job_description: Optional[str],
    position_criteria: Optional[Dict[str, Any]],
) -> str:
    """CV analizi promptuna eklenecek pozisyon bağlamını oluşturur.
    position_criteria mevcutsa (cache HIT ya da taze üretim), LLM'e ham
    iş ilanı yerine ÖNCEDEN ÜRETİLMİŞ, odaklı kriterleri veririz — bu hem
    daha hızlı hem de daha tutarlı bir CV puanlaması sağlar."""
    if not job_position or not job_position.strip():
        return (
            "\nHedef Pozisyon: Belirtilmedi (Genel CV Analizi)\n"
            "NOT: Hedef pozisyon boş/null olduğu için pozisyona özel değil, GENEL CV OPTİMİZASYONU "
            "(Genel ATS kuralları, metrik kullanımı, düzen, eylem fiilleri) yapın. "
            "Geliştirme önerilerinin ilk adımında 'Hedef pozisyon belirtilmediği için genel analiz yapılmıştır.' notunu mutlaka düşsün.\n"
        )

    parts = [f"\nHedef Pozisyon: {job_position}"]

    if position_criteria:
        key_criteria = position_criteria.get("key_criteria", [])
        keywords = position_criteria.get("keywords", [])
        seniority_signals = position_criteria.get("seniority_signals", [])

        if key_criteria:
            parts.append("\nBu Pozisyon İçin Kritik Değerlendirme Kriterleri:")
            parts.extend(f"- {c}" for c in key_criteria)
        if keywords:
            parts.append(f"\nAranan Anahtar Kelimeler: {', '.join(keywords)}")
        if seniority_signals:
            parts.append(f"\nDeneyim Seviyesi Göstergeleri: {', '.join(seniority_signals)}")

        parts.append(
            "\nBu CV'yi yukarıdaki pozisyona özel kriterlere göre değerlendir: "
            "CV'nin kriterlerle ve anahtar kelimelerle örtüşmesini dikkate al, "
            "eksik ya da eklenmesi önerilen unsurları spesifik olarak belirt."
        )
    else:
        # Kriter üretimi başarısız olduysa (LLM hatası) ham iş ilanına düş.
        if job_description:
            parts.append(f"\nİş İlanı / İstenen Profil:\n{job_description}")
        parts.append(
            "\nBu CV'yi yukarıdaki pozisyon için değerlendir: "
            "CV ile iş ilanı arasındaki anahtar kelime ve beceri örtüşmesini dikkate al, "
            "eksik ya da eklenmesi önerilen unsurları spesifik olarak belirt."
        )

    return "\n".join(parts) + "\n"


# Yanıt şeması
class CVAnalysisResponse(BaseModel):
    filename: str
    file_type: str
    character_count: int
    extracted_text: str
    job_position: Optional[str]  # Pozisyona özel analiz yapıldıysa hedef pozisyon
    parsed_skills: List[str]
    suggested_improvements: List[str]
    ats_score: int
    final_score: int
    score_breakdown: Dict[str, int]
    score_summary: Dict[str, int]


def _sanitize_llm_cv_output(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    LLM çıktısını temizler ve halüsinasyon gören anahtarları/puanları düzeltir.

    Özellikle küçük/lokal modeller bazen "ats_score: 75" veya "score_breakdown"
    gibi anahtar adlarını 'suggested_improvements' dizisinin içine eleman olarak
    koyabilir. Bu fonksiyon:
      1) 'suggested_improvements' içindeki "ats_score: XX" ifadelerini yakalayıp
         kök seviyedeki ats_score'a aktarır (eğer üst seviyede 0 veya eksikse).
      2) 'suggested_improvements' içinden meta anahtar kelimeleri ve puan metinlerini temizler.
      3) Temizlenmiş sözlüğü döner.
    """
    if not isinstance(data, dict):
        return {}

    raw_improvements = data.get("suggested_improvements", [])
    if not isinstance(raw_improvements, list):
        raw_improvements = []

    cleaned_improvements = []
    extracted_score = None

    for item in raw_improvements:
        if not isinstance(item, str):
            continue

        item_str = item.strip()

        # ats_score: 75 veya ats_score = 75 veya ats_score 75 kalıbını yakala
        score_match = re.search(r"ats_score\s*[:=]?\s*(\d+)", item_str, re.IGNORECASE)
        if score_match:
            try:
                extracted_score = int(score_match.group(1))
            except ValueError:
                pass
            continue  # Bu elemanı öneri listesinden çıkar

        # Diğer meta anahtar kelimeleri ve başlıkları önerilerden temizle
        if re.match(r"^(score_breakdown|parsed_skills|score_summary|ats_score)$", item_str, re.IGNORECASE):
            continue

        cleaned_improvements.append(item_str)

    data["suggested_improvements"] = cleaned_improvements

    # Üst seviyede ats_score yoksa veya 0 ise, diziden çıkarılan puanı kullan
    current_ats = data.get("ats_score")
    try:
        current_ats = int(current_ats)
    except (TypeError, ValueError):
        current_ats = 0

    if current_ats <= 0 and extracted_score is not None and extracted_score > 0:
        data["ats_score"] = extracted_score
        logger.info(f"suggested_improvements içinden kurtarılan ats_score: {extracted_score}")

    return data


def _filter_skills_against_cv_text(parsed_skills: List[str], cv_text: str) -> List[str]:
    """
    LLM'in halüsinasyon görüp iş ilanı kriterlerinden kopyaladığı, ancak
    adayın CV metninde HİÇ GEÇMEYEN becerileri temizler.
    """
    if not cv_text or not parsed_skills:
        return parsed_skills

    cv_text_lower = cv_text.lower()
    valid_skills: List[str] = []

    # Bilinen eşanlamlı/kısaltma/Türkçe karşılık haritası
    skill_aliases = {
        "reactjs": ["react", "reactjs"],
        "react.js": ["react", "reactjs"],
        "vuejs": ["vue", "vuejs"],
        "node.js": ["node", "nodejs"],
        "javascript": ["js", "javascript"],
        "typescript": ["ts", "typescript"],
        "postgresql": ["postgres", "postgresql"],
        "asp.net": [".net", "asp.net"],
        "asp.net core": [".net", "asp.net"],
        "c#": ["c#", "c sharp"],
        "c++": ["c++"],
        "llms": ["llm", "llms", "büyük dil modelleri", "large language models"],
        "rag systems": ["rag", "retrieval"],
        "agent-based systems": ["agent", "ajan"],
        "asynchronous programming patterns": ["asenkron", "async", "asynchronous"],
        "prompt engineering": ["prompt"],
    }

    for skill in parsed_skills:
        skill_clean = skill.strip()
        skill_lower = skill_clean.lower()

        # 1. Doğrudan alt dize kontrolü (örn: "Python" -> "python" in cv_text_lower)
        if skill_lower in cv_text_lower:
            valid_skills.append(skill_clean)
            continue

        # 2. Alias / Türkçe Karşılık kontrolü
        aliases = skill_aliases.get(skill_lower, [skill_lower])
        if any(alias in cv_text_lower for alias in aliases):
            valid_skills.append(skill_clean)
            continue

        # 3. Çok kelimeli becerilerin anlamlı parçalarının kontrolü
        words = [w for w in re.split(r"[\s\-_/]+", skill_lower) if len(w) > 2]
        if words and any(word in cv_text_lower for word in words):
            valid_skills.append(skill_clean)
            continue

        logger.info(f"CV metninde bulunamayan halüsinasyon beceri elendi: '{skill_clean}'")

    # Eğer filtreleme sonrasında hiç beceri kalmadıysa güvenlik amacıyla orijinal listeyi koru
    return valid_skills if valid_skills else parsed_skills


@router.post("/analyze", response_model=CVAnalysisResponse)
async def cv_analiz_endpoint(
    file: UploadFile = File(...),
    first_name: str = Form(...),      # DB tablosunda NOT NULL (Zorunlu)
    last_name: str = Form(...),       # DB tablosunda NOT NULL (Zorunlu)
    university: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    job_position: Optional[str] = Form(None),
    job_description: Optional[str] = Form(None),
    db: Session = Depends(get_db),    # PostgreSQL oturumu
):
    """
    Bir CV (PDF) yükleyerek metnini çıkarır, tespit edilen becerileri listeler,
    geliştirme önerileri sunar ve LLM ile ATS puanını hesaplar.

    job_position verilirse:
      1) Pozisyona özel kriterler cache'ten okunur (HIT) ya da LLM ile
         tek seferde (single-pass) üretilip cache'e yazılır (MISS).
      2) CV, bu odaklı kriterlere göre değerlendirilir.
    job_position verilmezse genel CV analizi gerçekleştirilir.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Geçersiz dosya türü. Şu anda yalnızca metin çıkarımı için PDF dosyaları desteklenmektedir.",
        )

    # ---------------------------------------------------------------------------
    # 1. Kullanıcı ve Okul Bilgilerini PostgreSQL Veritabanına Kaydetme
    # ---------------------------------------------------------------------------
    try:
        user_record = CVAnalizRecord(
            session_id=str(uuid.uuid4()),
            first_name=first_name,
            last_name=last_name,
            university=university,
            department=department,
            job_position=job_position,
        )
        db.add(user_record)
        db.commit()
        db.refresh(user_record)
    except Exception as db_err:
        db.rollback()
        logger.error(f"Veritabanına kayıt sırasında hata oluştu: {db_err}")

    # ---------------------------------------------------------------------------
    # 2. CV Analiz İşlemleri
    # ---------------------------------------------------------------------------
    content = await file.read()
    extracted_text = extract_text_from_pdf(content)
    character_count = len(extracted_text)

    parsed_skills: List[str] = []
    suggested_improvements: List[str] = []
    ats_score = 0
    score_breakdown: Optional[Dict[str, int]] = None

    try:
        position_criteria: Optional[Dict[str, Any]] = None
        if job_position and job_position.strip():
            try:
                position_criteria = await _get_or_create_position_criteria(
                    job_position, job_description
                )
            except Exception as criteria_err:
                # Kriter üretimi başarısız olsa bile CV analizi genel/ham
                # iş ilanı bağlamıyla devam edebilmeli.
                logger.warning(
                    "Pozisyon kriteri üretilemedi, ham iş ilanı bağlamına düşülüyor: %s",
                    criteria_err,
                )

        job_context = _build_job_context(job_position, job_description, position_criteria)

        prompt = CV_ANALYSIS_USER_TEMPLATE.format(
            cv_text=extracted_text,
            job_context=job_context,
        )
        llm_analiz_sonucu = await llm_client.generate_json(
            prompt=prompt,
            system_prompt=CV_ANALYSIS_SYSTEM_PROMPT,
        )
        llm_analiz_sonucu = _sanitize_llm_cv_output(llm_analiz_sonucu)

        raw_parsed_skills = llm_analiz_sonucu.get("parsed_skills", []) or []
        parsed_skills = _filter_skills_against_cv_text(raw_parsed_skills, extracted_text)
        suggested_improvements = llm_analiz_sonucu.get("suggested_improvements", []) or []
        ats_score = llm_analiz_sonucu.get("ats_score", 0) or 0
        score_breakdown = llm_analiz_sonucu.get("score_breakdown") or None

        if ats_score == 0:
            raise ValueError("LLM boş veya geçersiz analiz sonucu döndürdü (ats_score=0).")

    except Exception as e:
        logger.error(f"LLM CV analizi başarısız oldu, yedek ayrıştırıcı kullanılıyor: {e}")
        extracted_text_lower = extracted_text.lower()
        mock_skills: List[str] = []
        possible_skills = [
            "python", "fastapi", "django", "react", "docker", "kubernetes",
            "sql", "machine learning", "git",
        ]
        for skill in possible_skills:
            if skill in extracted_text_lower:
                mock_skills.append(skill.title())

        if not mock_skills:
            mock_skills = ["Genel Teknik Beceri"]

        parsed_skills = mock_skills
        if not job_position or not job_position.strip():
            suggested_improvements = [
                "Hedef pozisyon belirtilmediği için genel analiz yapılmıştır.",
                "Deneyim bölümünüze daha fazla nicel etki ifadesi (metrikler) ekleyin.",
                "ATS uyumluluğunu artırmak için genel bölüm başlıklarını ve düzeni optimize edin.",
            ]
        else:
            suggested_improvements = [
                "Deneyim bölümünüze daha fazla nicel etki ifadesi ekleyin.",
                "ATS eşleşmesini artırmak için hedef iş ilanlarındaki anahtar kelimeleri ekleyin.",
            ]
        ats_score = 85 if len(mock_skills) > 3 else 60
        score_breakdown = None  # Fallback: cv_analiz_et matematiksel dağılım kullanır

    analiz_sonucu = cv_analiz_et(
        cv_metni=extracted_text,
        parsed_skills=parsed_skills,
        llm_puani=ats_score if ats_score else None,
        score_breakdown=score_breakdown,
    )

    return CVAnalysisResponse(
        filename=file.filename or "bilinmeyen_dosya",
        file_type=file.content_type,
        character_count=character_count,
        extracted_text=extracted_text,
        job_position=job_position,
        parsed_skills=parsed_skills,
        suggested_improvements=suggested_improvements,
        ats_score=ats_score,
        final_score=analiz_sonucu["final_score"],
        score_breakdown=analiz_sonucu["breakdown"],
        score_summary=analiz_sonucu["summary"],
    )
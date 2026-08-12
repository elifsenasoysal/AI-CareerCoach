from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

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


def _criteria_cache_key(job_position: str) -> str:
    """Pozisyon adını normalize ederek cache anahtarı üretir.
    Böylece 'React Developer', 'react developer', ' React Developer ' gibi
    varyasyonlar aynı cache girdisini kullanır."""
    return job_position.strip().lower()


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
    cache_key = _criteria_cache_key(job_position)

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
    if not job_position:
        return ""  # Genel analiz

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


@router.post("/analyze", response_model=CVAnalysisResponse)
async def cv_analiz_endpoint(
    file: UploadFile = File(...),
    job_position: Optional[str] = Form(None),
    job_description: Optional[str] = Form(None),
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

    content = await file.read()
    extracted_text = extract_text_from_pdf(content)
    character_count = len(extracted_text)

    parsed_skills: List[str] = []
    suggested_improvements: List[str] = []
    ats_score = 0
    score_breakdown: Optional[Dict[str, int]] = None

    try:
        position_criteria: Optional[Dict[str, Any]] = None
        if job_position:
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

        parsed_skills = llm_analiz_sonucu.get("parsed_skills", []) or []
        suggested_improvements = llm_analiz_sonucu.get("suggested_improvements", []) or []
        ats_score = llm_analiz_sonucu.get("ats_score", 0) or 0
        score_breakdown = llm_analiz_sonucu.get("score_breakdown") or None

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
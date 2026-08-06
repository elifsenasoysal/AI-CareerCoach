from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import hashlib
from app.services.pdf_parser import extract_text_from_pdf
from app.services.llm import llm_client
from app.services.cache import cache_service
from app.services.cv_analiz import cv_analiz_et

logger = logging.getLogger(__name__)

router = APIRouter()

# Yanıt şeması
class CVAnalysisResponse(BaseModel):
    filename: str
    file_type: str
    character_count: int
    extracted_text: str
    parsed_skills: List[str]
    suggested_improvements: List[str]
    ats_score: int
    final_score: int
    score_breakdown: Dict[str, int]
    score_summary: Dict[str, int]
    applied_criteria: Optional[List[Dict[str, Any]]] = None

@router.post("/analyze", response_model=CVAnalysisResponse)
async def cv_analiz_endpoint(
    file: UploadFile = File(...),
    job_position: Optional[str] = Form(None),
    job_description: Optional[str] = Form(None)
):
    """
    Bir CV (PDF) yükleyerek metnini çıkarır, hedef pozisyon ve/veya iş tanımına göre 
    LLM ile analiz ve ATS puanlaması yapar. Kriterler sonraki istekler için önbelleğe alınır.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Geçersiz dosya türü. Şu anda yalnızca metin çıkarımı için PDF dosyaları desteklenmektedir."
        )

    content = await file.read()
    extracted_text = extract_text_from_pdf(content)
    character_count = len(extracted_text)

    # Önbellek anahtarı belirleme
    cache_key = None
    is_specific_jd = False

    if job_description and job_description.strip():
        # İş tanımı metninin hash'ini alarak benzersiz bir key oluşturuyoruz
        jd_hash = hashlib.sha256(job_description.strip().encode('utf-8')).hexdigest()
        cache_key = f"jd:{jd_hash}"
        is_specific_jd = True
    elif job_position and job_position.strip():
        # Pozisyon ismini küçük harfe çevirip normalize ediyoruz
        normalized_position = job_position.strip().lower().replace(" ", "_")
        cache_key = f"pos:{normalized_position}"

    # Cache sorgulama
    criteria = None
    if cache_key:
        try:
            criteria = await cache_service.get(cache_key)
        except Exception as e:
            logger.error(f"Önbellekten veri okurken hata oluştu: {e}")

    parsed_skills: List[str] = []
    suggested_improvements: List[str] = []
    ats_score = 0
    applied_criteria: Optional[List[Dict[str, Any]]] = None

    try:
        if criteria:
            logger.info(f"Cache HIT for key: {cache_key}")
            # Cache Hit: Kriterler zaten var, LLM'e sadece CV'yi bu kriterlere göre puanlatıyoruz.
            llm_response = await llm_client.evaluate_cv_with_criteria(
                cv_text=extracted_text,
                criteria=criteria
            )
            parsed_skills = llm_response.get("parsed_skills", []) or []
            suggested_improvements = llm_response.get("suggested_improvements", []) or []
            ats_score = llm_response.get("ats_score", 0) or 0
            applied_criteria = criteria
        else:
            logger.info(f"Cache MISS for key: {cache_key}")
            # Cache Miss: Tek geçişte (Single-Pass) kriter üretimi ve CV puanlama
            llm_response = await llm_client.analyze_cv_single_pass(
                cv_text=extracted_text,
                job_position=job_position,
                job_description=job_description
            )
            
            extracted_criteria = llm_response.get("criteria", [])
            analysis_data = llm_response.get("analysis", {})
            
            parsed_skills = analysis_data.get("parsed_skills", []) or []
            suggested_improvements = analysis_data.get("suggested_improvements", []) or []
            ats_score = analysis_data.get("ats_score", 0) or 0
            applied_criteria = extracted_criteria

            # Kriterleri sonraki kullanımlar için önbelleğe yazıyoruz
            if cache_key and extracted_criteria:
                try:
                    await cache_service.set(cache_key, extracted_criteria)
                    logger.info(f"Cached criteria under key: {cache_key}")
                except Exception as e:
                    logger.error(f"Önbelleğe veri yazarken hata oluştu: {e}")

    except Exception as e:
        logger.error(f"LLM CV analizi başarısız oldu, yedek ayrıştırıcı kullanılıyor: {e}")

        extracted_text_lower = extracted_text.lower()
        mock_skills: List[str] = []
        possible_skills = ["python", "fastapi", "django", "react", "docker", "kubernetes", "sql", "machine learning", "git"]
        for skill in possible_skills:
            if skill in extracted_text_lower:
                mock_skills.append(skill.title())

        if not mock_skills:
            mock_skills = ["Genel Teknik Beceri"]

        parsed_skills = mock_skills
        suggested_improvements = [
            "Deneyim bölümünüze daha fazla nicel etki ifadesi ekleyin.",
            "ATS eşleşmesini artırmak için hedef iş ilanlarındaki anahtar kelimeleri ekleyin."
        ]
        ats_score = 85 if len(mock_skills) > 3 else 60
        applied_criteria = [{"name": "Temel Teknik Beceriler", "weight": 1.0}]

    analiz_sonucu = cv_analiz_et(
        cv_metni=extracted_text,
        parsed_skills=parsed_skills,
        llm_puani=ats_score if ats_score else None,
    )

    return CVAnalysisResponse(
        filename=file.filename or "bilinmeyen_dosya",
        file_type=file.content_type,
        character_count=character_count,
        extracted_text=extracted_text,
        parsed_skills=parsed_skills,
        suggested_improvements=suggested_improvements,
        ats_score=ats_score,
        final_score=analiz_sonucu["final_score"],
        score_breakdown=analiz_sonucu["breakdown"],
        score_summary=analiz_sonucu["summary"],
        applied_criteria=applied_criteria
    )


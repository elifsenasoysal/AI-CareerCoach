from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import logging
from app.services.pdf_parser import extract_text_from_pdf
from app.services.llm import (
    llm_client,
    CV_ANALYSIS_SYSTEM_PROMPT,
    CV_ANALYSIS_USER_TEMPLATE,
)
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

@router.post("/analyze", response_model=CVAnalysisResponse)
async def cv_analiz_endpoint(file: UploadFile = File(...)):
    """
    Bir CV (PDF) yükleyerek metnini çıkarır, tespit edilen becerileri listeler, geliştirme önerileri sunar ve LLM ile ATS puanını hesaplar.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Geçersiz dosya türü. Şu anda yalnızca metin çıkarımı için PDF dosyaları desteklenmektedir."
        )

    content = await file.read()
    extracted_text = extract_text_from_pdf(content)
    character_count = len(extracted_text)

    parsed_skills: List[str] = []
    suggested_improvements: List[str] = []
    ats_score = 0

    try:
        prompt = CV_ANALYSIS_USER_TEMPLATE.format(cv_text=extracted_text)
        llm_analiz_sonucu = await llm_client.generate_json(
            prompt=prompt,
            system_prompt=CV_ANALYSIS_SYSTEM_PROMPT
        )

        parsed_skills = llm_analiz_sonucu.get("parsed_skills", []) or []
        suggested_improvements = llm_analiz_sonucu.get("suggested_improvements", []) or []
        ats_score = llm_analiz_sonucu.get("ats_score", 0) or 0
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
    )

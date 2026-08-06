from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid
from app.services.cache import cache_service
from app.services.llm import (
    llm_client,
    INTERVIEW_START_SYSTEM_PROMPT,
    INTERVIEW_START_USER_TEMPLATE,
    INTERVIEW_FEEDBACK_SYSTEM_PROMPT,
    INTERVIEW_FEEDBACK_USER_TEMPLATE,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Şemalar
class StartInterviewRequest(BaseModel):
    role: str
    experience_level: str  # örn. Junior, Mid, Senior
    focus_areas: Optional[List[str]] = None

class InterviewSessionResponse(BaseModel):
    session_id: str
    role: str
    first_question: str

class SubmitAnswerRequest(BaseModel):
    session_id: str
    question: str
    answer: str

class SubmitAnswerResponse(BaseModel):
    feedback: str
    score: int  # 1 ila 10 arasında puan
    next_question: Optional[str] = None

@router.post("/start", response_model=InterviewSessionResponse)
async def mulakat_baslat(request: StartInterviewRequest):
    """
    Belirli bir rol ve deneyim düzeyi için LLM kullanarak bir mülakat simülasyonu başlatır.
    """
    # Varsayılan yedek soru
    role_lower = request.role.lower()
    if "python" in role_lower or "backend" in role_lower:
        fallback_question = "Python'da liste ve tuple arasındaki farkı açıklayabilir misiniz ve her birini ne zaman kullanırsınız?"
    else:
        fallback_question = f"{request.role} alanındaki deneyiminizden bahsedebilir misiniz?"

    first_question = fallback_question

    try:
        # Prompt oluştur ve LLM'ye sorgu gönder
        focus_areas_str = ", ".join(request.focus_areas) if request.focus_areas else "Genel teknik beceriler"
        prompt = INTERVIEW_START_USER_TEMPLATE.format(
            role=request.role,
            experience_level=request.experience_level,
            focus_areas=focus_areas_str
        )
        
        result = await llm_client.generate_json(
            prompt=prompt,
            system_prompt=INTERVIEW_START_SYSTEM_PROMPT
        )
        first_question = result.get("first_question", fallback_question)
        
    except Exception as e:
        logger.error(f"LLM ilk soruyu üretemedi, statik sorulara geçiliyor: {e}")

    session_id = f"session_{uuid.uuid4()}"
    try:
        await cache_service.set(
            f"session:{session_id}",
            {
                "role": request.role,
                "experience_level": request.experience_level,
                "focus_areas": request.focus_areas
            }
        )
    except Exception as ce:
        logger.error(f"Oturum önbelleğe kaydedilemedi: {ce}")

    return InterviewSessionResponse(
        session_id=session_id,
        role=request.role,
        first_question=first_question
    )

@router.post("/respond", response_model=SubmitAnswerResponse)
async def yanit_gonder(request: SubmitAnswerRequest):
    """
    Bir soruya yanıt gönderin ve LLM kullanarak dinamik geri bildirim ve sonraki soruyu alın.
    """
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Geçersiz oturum kimliği")

    # LLM başarısız olursa kullanılacak yedek mantık
    fallback_feedback = "İyi bir açıklama. Ana kavramları net şekilde ifade ettiniz ve sağlam bir cevap verdiniz."
    fallback_score = 8
    fallback_next_question = "FastAPI uygulamalarınızda hata yönetimini ve logging'i nasıl ele alıyorsunuz?"

    feedback = fallback_feedback
    score = fallback_score
    next_question = fallback_next_question

    role = "Yazılım Mühendisi"
    experience_level = "Mid/Senior"
    try:
        session_data = await cache_service.get(f"session:{request.session_id}")
        if session_data:
            role = session_data.get("role", role)
            experience_level = session_data.get("experience_level", experience_level)
    except Exception as ce:
        logger.error(f"Oturum verileri önbellekten okunamadı: {ce}")

    try:
        # Prompt oluştur ve LLM'ye sorgu gönder
        prompt = INTERVIEW_FEEDBACK_USER_TEMPLATE.format(
            role=role,
            experience_level=experience_level,
            question=request.question,
            answer=request.answer
        )
        
        result = await llm_client.generate_json(
            prompt=prompt,
            system_prompt=INTERVIEW_FEEDBACK_SYSTEM_PROMPT
        )
        feedback = result.get("feedback", fallback_feedback)
        score = result.get("score", fallback_score)
        next_question = result.get("next_question", fallback_next_question)
        
    except Exception as e:
        logger.error(f"LLM yanıtı değerlendiremedi, yedek kullanılıyor: {e}")

    return SubmitAnswerResponse(
        feedback=feedback,
        score=score,
        next_question=next_question
    )

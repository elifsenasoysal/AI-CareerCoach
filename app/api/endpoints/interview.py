from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid

from app.services.llm import (
    llm_client,
    INTERVIEW_START_SYSTEM_PROMPT,
    INTERVIEW_START_USER_TEMPLATE,
    INTERVIEW_FEEDBACK_SYSTEM_PROMPT,
    INTERVIEW_FEEDBACK_USER_TEMPLATE,
)
from app.services.cache import cache_service, SessionData

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Şemalar
# ---------------------------------------------------------------------------
class StartInterviewRequest(BaseModel):
    role: str
    experience_level: str  # örn. Junior, Mid, Senior
    focus_areas: Optional[List[str]] = None


class InterviewSessionResponse(BaseModel):
    # NOT: Bu şemada TEK bir session_id alanı vardır. Önceki sürümlerde
    # bazı akışlarda hem endpoint fonksiyonunun döndürdüğü hem de
    # SessionData/cache içinde ayrıca üretilen iki farklı kimlik
    # (bir tanesi hardcoded "session_abc123_xyz", diğeri varsa uuid)
    # karışabiliyordu. Artık kimlik SADECE burada, tek noktada
    # (`session_id = str(uuid.uuid4())`) üretiliyor ve hem cache'e hem
    # yanıta aynı değer yazılıyor — çakışma imkânı kalmıyor.
    session_id: str
    role: str
    first_question: str


class SubmitAnswerRequest(BaseModel):
    session_id: str
    question: str
    answer: str


class SubmitAnswerResponse(BaseModel):
    feedback: str  # Gradio gr.Markdown ile doğrudan render edilebilecek markdown metni
    score: int  # 1 ila 10 arasında puan
    next_question: Optional[str] = None


def _clamp_score(value, min_val: int = 1, max_val: int = 10, default: int = 5) -> int:
    """LLM'den gelen score alanını güvenli bir tam sayıya indirger.
    Beklenmedik tip (string, float, None) veya aralık dışı değer gelirse
    API'nin 500 dönmesini engeller."""
    try:
        value = int(round(float(value)))
    except (TypeError, ValueError):
        return default
    return max(min_val, min(max_val, value))


@router.post("/start", response_model=InterviewSessionResponse)
async def mulakat_baslat(request: StartInterviewRequest):
    """
    Belirli bir rol ve deneyim düzeyi için LLM kullanarak bir mülakat simülasyonu başlatır.
    """
    # Varsayılan yedek soru
    role_lower = request.role.lower()
    if "python" in role_lower or "backend" in role_lower:
        fallback_question = (
            "Python'da liste ve tuple arasındaki farkı açıklayabilir misiniz ve "
            "her birini ne zaman kullanırsınız?"
        )
    else:
        fallback_question = f"{request.role} alanındaki deneyiminizden bahsedebilir misiniz?"

    first_question = fallback_question

    try:
        focus_areas_str = (
            ", ".join(request.focus_areas) if request.focus_areas else "Genel teknik beceriler"
        )
        prompt = INTERVIEW_START_USER_TEMPLATE.format(
            role=request.role,
            experience_level=request.experience_level,
            focus_areas=focus_areas_str,
        )
        result = await llm_client.generate_json(
            prompt=prompt,
            system_prompt=INTERVIEW_START_SYSTEM_PROMPT,
        )
        first_question = result.get("first_question", fallback_question)
    except Exception as e:
        logger.error(f"LLM ilk soruyu üretemedi, statik sorulara geçiliyor: {e}")

    # Tek, kanonik session_id üretimi — hem cache hem yanıt bu değeri kullanır.
    session_id = str(uuid.uuid4())
    session_data = SessionData(
        role=request.role,
        experience_level=request.experience_level,
        focus_areas=request.focus_areas or [],
    )
    cache_service.set_session(session_id, session_data)

    logger.info(
        "Yeni mülakat oturumu oluşturuldu: %s | Rol: %s | Seviye: %s",
        session_id, request.role, request.experience_level,
    )

    return InterviewSessionResponse(
        session_id=session_id,
        role=request.role,
        first_question=first_question,
    )


@router.post("/respond", response_model=SubmitAnswerResponse)
async def yanit_gonder(request: SubmitAnswerRequest):
    """Bir soruya yanıt gönderin ve LLM kullanarak dinamik geri bildirim ve sonraki soruyu alın."""
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Geçersiz oturum kimliği")

    session_data = cache_service.get_session(request.session_id)
    if not session_data:
        raise HTTPException(
            status_code=404,
            detail=f"Oturum bulunamadı: '{request.session_id}'. Lütfen önce /start endpoint'ini çağırın.",
        )

    session_role = session_data.role
    session_level = session_data.experience_level

    # LLM başarısız olursa kullanılacak yedek mantık (Gradio Markdown ile uyumlu format)
    fallback_feedback = (
        "### 🟢 Doğrular\n"
        "- Ana kavramları net şekilde ifade ettiniz.\n\n"
        "### 🔴 Eksikler\n"
        "- Şu anda otomatik değerlendirme yapılamadı, bu yüzden detaylı eksik analizi sunulamıyor.\n\n"
        "### 💡 Öneriler\n"
        "- Cevabınızı somut bir örnekle desteklemeyi deneyin."
    )
    fallback_score = 5
    fallback_next_question = (
        "FastAPI uygulamalarınızda hata yönetimini ve logging'i nasıl ele alıyorsunuz?"
    )

    feedback = fallback_feedback
    score = fallback_score
    next_question = fallback_next_question

    try:
        prompt = INTERVIEW_FEEDBACK_USER_TEMPLATE.format(
            role=session_role,
            experience_level=session_level,
            question=request.question,
            answer=request.answer,
        )
        result = await llm_client.generate_json(
            prompt=prompt,
            system_prompt=INTERVIEW_FEEDBACK_SYSTEM_PROMPT,
        )
        feedback = result.get("feedback", fallback_feedback)
        score = _clamp_score(result.get("score", fallback_score), default=fallback_score)
        next_question = result.get("next_question", fallback_next_question)
    except Exception as e:
        logger.error(f"LLM yanıtı değerlendiremedi, yedek kullanılıyor: {e}")

    return SubmitAnswerResponse(
        feedback=feedback,
        score=score,
        next_question=next_question,
    )
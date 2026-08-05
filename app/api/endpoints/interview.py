from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
from app.services.llm import (
    llm_client,
    INTERVIEW_START_SYSTEM_PROMPT,
    INTERVIEW_START_USER_TEMPLATE,
    INTERVIEW_FEEDBACK_SYSTEM_PROMPT,
    INTERVIEW_FEEDBACK_USER_TEMPLATE,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Schemas
class StartInterviewRequest(BaseModel):
    role: str
    experience_level: str  # e.g., Junior, Mid, Senior
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
    score: int  # 1 to 10 rating
    next_question: Optional[str] = None

@router.post("/start", response_model=InterviewSessionResponse)
async def start_interview(request: StartInterviewRequest):
    """
    Start an interview simulation session for a specific role and experience level using LLM.
    """
    # Fallback default question
    role_lower = request.role.lower()
    if "python" in role_lower or "backend" in role_lower:
        fallback_question = "Can you explain the difference between a list and a tuple in Python, and when you would use each?"
    else:
        fallback_question = f"Tell me about your experience working with {request.role}."

    first_question = fallback_question

    try:
        # Build prompt & query LLM
        focus_areas_str = ", ".join(request.focus_areas) if request.focus_areas else "General technical skills"
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
        logger.error(f"LLM failed to generate first question, falling back to static questions: {e}")

    return InterviewSessionResponse(
        session_id="session_abc123_xyz",  # Mock session ID for now, can be updated later if a database/state store is added
        role=request.role,
        first_question=first_question
    )

@router.post("/respond", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """
    Submit an answer to a question and receive dynamic feedback along with the next question using LLM.
    """
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    # Fallback logic in case LLM fails
    fallback_feedback = "Good explanation. You clearly articulated the core concepts and gave a solid response."
    fallback_score = 8
    fallback_next_question = "How do you handle error handling and logging in your FastAPI applications?"

    feedback = fallback_feedback
    score = fallback_score
    next_question = fallback_next_question

    try:
        # Build prompt & query LLM
        prompt = INTERVIEW_FEEDBACK_USER_TEMPLATE.format(
            role="Software Engineer",  # Note: Session state could be loaded from db if we had one. Using placeholder for now.
            experience_level="Mid/Senior",
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
        logger.error(f"LLM failed to evaluate answer, falling back: {e}")

    return SubmitAnswerResponse(
        feedback=feedback,
        score=score,
        next_question=next_question
    )

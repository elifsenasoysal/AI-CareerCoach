from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

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
    Start an interview simulation session for a specific role and experience level.
    """
    # Simple hardcoded questions based on role
    role_lower = request.role.lower()
    if "python" in role_lower or "backend" in role_lower:
        question = "Can you explain the difference between a list and a tuple in Python, and when you would use each?"
    else:
        question = f"Tell me about your experience working with {request.role}."

    return InterviewSessionResponse(
        session_id="session_abc123_xyz",
        role=request.role,
        first_question=question
    )

@router.post("/respond", response_model=SubmitAnswerResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """
    Submit an answer to a question and receive immediate feedback along with the next question.
    """
    if not request.session_id:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    # Mocked feedback logic
    answer_length = len(request.answer.split())
    if answer_length < 10:
        feedback = "Your answer was a bit short. Try to elaborate on technical details and provide concrete examples."
        score = 5
    else:
        feedback = "Good explanation. You clearly articulated the core concepts and gave a solid response."
        score = 8

    return SubmitAnswerResponse(
        feedback=feedback,
        score=score,
        next_question="How do you handle error handling and logging in your FastAPI applications?"
    )

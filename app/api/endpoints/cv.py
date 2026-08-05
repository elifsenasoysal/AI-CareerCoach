from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter()

# Schema for the response
class CVAnalysisResponse(BaseModel):
    filename: str
    file_type: str
    parsed_skills: List[str]
    suggested_improvements: List[str]
    ats_score: int

@router.post("/analyze", response_model=CVAnalysisResponse)
async def analyze_cv(file: UploadFile = File(...)):
    """
    Upload a CV (PDF or DOCX) to extract skills, suggest enhancements, and calculate a mock ATS score.
    """
    # Verify file type
    allowed_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only PDF and DOCX files are allowed."
        )
    
    # Read the file content (in a real app, you would parse the PDF/DOCX)
    content = await file.read()
    
    # Mocked response for demonstration
    return CVAnalysisResponse(
        filename=file.filename or "unknown_file",
        file_type=file.content_type,
        parsed_skills=["Python", "FastAPI", "Docker", "Machine Learning"],
        suggested_improvements=[
            "Add more quantitative impact statements in your experience section.",
            "Include keywords from your target job descriptions to improve ATS matching."
        ],
        ats_score=78
    )

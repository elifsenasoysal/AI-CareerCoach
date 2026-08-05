from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
import logging
from app.services.pdf_parser import extract_text_from_pdf
from app.services.llm import (
    llm_client,
    CV_ANALYSIS_SYSTEM_PROMPT,
    CV_ANALYSIS_USER_TEMPLATE,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Schema for the response
class CVAnalysisResponse(BaseModel):
    filename: str
    file_type: str
    character_count: int
    extracted_text: str
    parsed_skills: List[str]
    suggested_improvements: List[str]
    ats_score: int

@router.post("/analyze", response_model=CVAnalysisResponse)
async def analyze_cv(file: UploadFile = File(...)):
    """
    Upload a CV (PDF) to extract text, list parsed skills, suggest enhancements, and calculate an ATS score using LLM.
    """
    # Verify file type - restrict to PDF for text extraction
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Only PDF files are supported for text extraction at the moment."
        )
    
    # Read the file content
    content = await file.read()
    
    # Parse PDF content
    extracted_text = extract_text_from_pdf(content)
    character_count = len(extracted_text)
    
    # Initialize response fields
    parsed_skills = []
    suggested_improvements = []
    ats_score = 0
    
    try:
        # Build prompt and query the LLM
        prompt = CV_ANALYSIS_USER_TEMPLATE.format(cv_text=extracted_text)
        analysis_result = await llm_client.generate_json(
            prompt=prompt,
            system_prompt=CV_ANALYSIS_SYSTEM_PROMPT
        )
        
        parsed_skills = analysis_result.get("parsed_skills", [])
        suggested_improvements = analysis_result.get("suggested_improvements", [])
        ats_score = analysis_result.get("ats_score", 0)
        
    except Exception as e:
        logger.error(f"LLM CV Analysis failed, falling back to mock parser: {e}")
        
        # Simple logic to mock parsing some skills based on extracted text content
        extracted_text_lower = extracted_text.lower()
        mock_skills = []
        possible_skills = ["python", "fastapi", "django", "react", "docker", "kubernetes", "sql", "machine learning", "git"]
        for skill in possible_skills:
            if skill in extracted_text_lower:
                mock_skills.append(skill.title())
                
        # Fallback if no skills matched
        if not mock_skills:
            mock_skills = ["Generic Technical Skill"]
            
        parsed_skills = mock_skills
        suggested_improvements = [
            "Add more quantitative impact statements in your experience section (Fallback).",
            "Include keywords from your target job descriptions to improve ATS matching (Fallback)."
        ]
        ats_score = 85 if len(mock_skills) > 3 else 60

    return CVAnalysisResponse(
        filename=file.filename or "unknown_file",
        file_type=file.content_type,
        character_count=character_count,
        extracted_text=extracted_text,
        parsed_skills=parsed_skills,
        suggested_improvements=suggested_improvements,
        ats_score=ats_score
    )


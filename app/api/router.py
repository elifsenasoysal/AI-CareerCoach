from fastapi import APIRouter
from app.api.endpoints import cv, interview

api_router = APIRouter()

# Include CV endpoints
api_router.include_router(cv.router, prefix="/cv", tags=["CV Analysis"])

# Include Interview endpoints
api_router.include_router(interview.router, prefix="/interview", tags=["Interview Simulation"])

from fastapi import APIRouter
from app.api.endpoints import cv, interview

api_router = APIRouter()

# CV endpointlerini ekle
api_router.include_router(cv.router, prefix="/cv", tags=["CV Analizi"])

# Mülakat endpointlerini ekle
api_router.include_router(interview.router, prefix="/interview", tags=["Mülakat Simülasyonu"])

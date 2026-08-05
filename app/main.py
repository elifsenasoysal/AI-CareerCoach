from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS ara katmanı yapılandırması (ön yüz uygulamalarıyla bağlantı için zorunludur)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Üretimde ön yüz alanınızı belirtin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sağlık kontrolü için kök endpoint
@app.get("/")
def read_root():
    return {
        "message": "AI Kariyer Koçu API'sine hoş geldiniz!",
        "status": "sağlıklı",
        "docs_url": "/docs"
    }

# Include all V1 API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

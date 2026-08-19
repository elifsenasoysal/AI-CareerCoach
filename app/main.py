from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.router import api_router
from app.database.session import engine, Base
import app.database.models  # noqa: F401 (modelleri kaydeder)

# Veritabanı tablolarını otomatik oluştur (engine varsa)
if engine is not None:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as db_init_err:
        import logging
        logging.getLogger(__name__).warning(f"Veritabanı tabloları otomatik oluşturulamadı: {db_init_err}")

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

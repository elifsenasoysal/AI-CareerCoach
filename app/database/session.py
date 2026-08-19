import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

DATABASE_URL = settings.DATABASE_URL

engine = None
SessionLocal = None

if DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    except Exception as e:
        logger.error(f"Veritabanı motoru oluşturulurken hata: {e}")
else:
    logger.warning("DATABASE_URL tanımlı değil. Veritabanı işlemleri pasif durumda.")

def get_db():
    if not SessionLocal:
        raise ValueError("DATABASE_URL tanımlanmadığı için veritabanı oturumu açılamıyor. Lütfen .env dosyasını kontrol edin.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
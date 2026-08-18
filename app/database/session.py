import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# .env dosyasındaki değişkenleri ortama yükler
load_dotenv()

# Şifre içermeyen güvenli çekim
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL ortam değişkeni .env dosyasında bulunamadı!")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# FastAPI endpoint'lerine veritabanı oturumu sağlayan fonksiyon
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
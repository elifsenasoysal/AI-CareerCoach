import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from app.database.session import Base

class CVAnalizRecord(Base):
    __tablename__ = "cv_analizleri"

    # session_id metin tabanlı (VARCHAR) ve birincil anahtar
    session_id = Column(String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    university = Column(String(250), nullable=True)
    department = Column(String(250), nullable=True)
    job_position = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
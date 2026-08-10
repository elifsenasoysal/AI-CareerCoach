"""
app/services/cache.py

Session verisini yöneten cache servisi.

Şu an: In-memory dict (sıfır kurulum, geliştirme için ideal)
İleride: Redis ile aynı arayüzü koruyarak değiştirilebilir — çağıran kod
(interview.py, cv.py vb.) hiç değişmez, sadece bu dosya güncellenir.

Arayüz:
    cache_service.set_session(session_id, data)   → None
    cache_service.get_session(session_id)          → dict | None
    cache_service.delete_session(session_id)       → None
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Bir mülakat oturumunun tuttuğu veriler."""
    role: str
    experience_level: str
    focus_areas: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "experience_level": self.experience_level,
            "focus_areas": self.focus_areas,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        return cls(
            role=data["role"],
            experience_level=data["experience_level"],
            focus_areas=data.get("focus_areas", []),
        )


class SessionCache:
    """
    Oturum verilerini saklayan ve okuyan cache servisi.

    Şu an in-memory dict tabanlıdır.
    Redis'e geçmek için bu sınıfın implementasyonunu değiştirin;
    dışarıya açık arayüz (set_session / get_session / delete_session) aynı kalır.
    """

    def __init__(self) -> None:
        # Backend: in-memory dict
        # Redis'e geçince bu satır: self._store = redis.asyncio.from_url(settings.REDIS_URL)
        self._store: Dict[str, Dict[str, Any]] = {}
        logger.info("SessionCache başlatıldı (in-memory backend).")

    def set_session(self, session_id: str, data: SessionData) -> None:
        """Oturum verisini kaydet."""
        self._store[session_id] = data.to_dict()
        logger.debug(f"Session kaydedildi: {session_id} | Rol: {data.role} | Seviye: {data.experience_level}")

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Oturum verisini getir.
        Bulunamazsa None döner — çağıran kod 404 fırlatmalı.
        """
        raw = self._store.get(session_id)
        if raw is None:
            logger.debug(f"Session bulunamadı: {session_id}")
            return None
        return SessionData.from_dict(raw)

    def delete_session(self, session_id: str) -> None:
        """Oturumu sonlandır ve cache'ten sil."""
        if session_id in self._store:
            del self._store[session_id]
            logger.debug(f"Session silindi: {session_id}")

    def session_exists(self, session_id: str) -> bool:
        """Oturumun var olup olmadığını kontrol et."""
        return session_id in self._store


# ---------------------------------------------------------------------------
# Uygulama genelinde tek bir örnek (singleton) — her modül bunu import eder.
#
# İleride Redis'e geçince:
#   from app.services.cache import cache_service
#   Hiçbir çağıran kodu değiştirmene gerek yok.
# ---------------------------------------------------------------------------
cache_service = SessionCache()

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # ── Uygulama ─────────────────────────────────────────────────────────
    PROJECT_NAME: str = "AI Kariyer Koçu API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # ── Ollama / LLM ──────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Ollama sunucusunun base URL'i",
    )
    LLM_MODEL: str = Field(
        default="llama3",
        description="Kullanılacak Ollama model adı (örn. llama3, mistral)",
    )
    LLM_TIMEOUT: float = Field(
        default=60.0,
        description="LLM isteği için maksimum bekleme süresi (saniye)",
    )

    # ── Redis (opsiyonel — şu an in-memory cache kullanılıyor) ───────────
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis bağlantı URL'i. SessionCache Redis'e taşındığında kullanılır.",
    )

    model_config = {
        # .env dosyasından otomatik oku (yoksa varsayılan değerler kullanılır)
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        # Büyük/küçük harf duyarlılığı
        "case_sensitive": True,
        # .env'de tanımsız alanlar hata fırlatmasın
        "extra": "ignore",
    }


settings = Settings()

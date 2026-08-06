from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Kariyer Koçu API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Burada daha sonra LLM (Ollama), STT, TTS ayarları ekleyebiliriz
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3"
    LLM_TIMEOUT: float = 60.0

    # Redis Caching Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_EXPIRE_SECONDS: int = 86400  # 1 day

    class Config:
        case_sensitive = True


settings = Settings()

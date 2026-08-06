from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Kariyer Koçu API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Burada daha sonra LLM (Ollama), STT, TTS ayarları ekleyebiliriz
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    LLM_MODEL: str = "llama3"
    LLM_TIMEOUT: float = 60.0
    
    class Config:
        case_sensitive = True

settings = Settings()

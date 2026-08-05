from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Career Coach API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # We can add LLM (Ollama), STT, TTS settings here later
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    class Config:
        case_sensitive = True

settings = Settings()

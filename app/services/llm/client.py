import json
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.LLM_MODEL
        self.timeout = settings.LLM_TIMEOUT

    async def generate_json(self, prompt: str, system_prompt: str) -> dict:
        """
        Ollama sohbet API'sine sistem ve kullanıcı promptları gönderir,
        çıkış formatını JSON olarak zorlar.
        """
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "format": "json"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Ollama'nın /api/chat yanıt şeması:
                # {
                #   "message": {
                #     "role": "assistant",
                #     "content": "{...}"
                #   }
                # }
                content_str = data.get("message", {}).get("content", "").strip()
                if not content_str:
                    raise ValueError("LLM'den boş içerik alındı.")
                
                return json.loads(content_str)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama sunucusu HTTP hatası döndürdü: {e.response.status_code} - {e.response.text}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"LLM yanıtı JSON olarak çözümlenemedi. İçerik: {content_str}. Hata: {e}")
            raise
        except Exception as e:
            logger.error(f"LLMClient iletişim hatası: {str(e)}")
            raise

# Singleton instance for easy import
llm_client = LLMClient()

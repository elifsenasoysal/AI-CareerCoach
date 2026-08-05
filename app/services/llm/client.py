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
        Sends a request to Ollama's chat API with system and user prompts,
        forcing the output format to be JSON.
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
                
                # Ollama's /api/chat response schema:
                # {
                #   "message": {
                #     "role": "assistant",
                #     "content": "{...}"
                #   }
                # }
                content_str = data.get("message", {}).get("content", "").strip()
                if not content_str:
                    raise ValueError("Received empty content from LLM.")
                
                return json.loads(content_str)
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama server returned HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode LLM response as JSON. Content: {content_str}. Error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in LLMClient communication: {str(e)}")
            raise

# Singleton instance for easy import
llm_client = LLMClient()

import json
import logging
import re
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


def _strip_markdown_json(text: str) -> str:
    """
    LLM yanıtındaki Markdown JSON bloğunu soyar.

    Bazı modeller (Llama 3 dahil) JSON'u şu formatta sarmalayabilir:
        ```json
        { ... }
        ```
    veya sadece:
        ```
        { ... }
        ```

    Bu fonksiyon sarmalayıcıyı kaldırır ve saf JSON metnini döndürür.
    Sarmalayıcı yoksa metni olduğu gibi döndürür.
    """
    # ```json ... ``` veya ``` ... ``` kalıbını yakala
    match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if match:
        extracted = match.group(1).strip()
        logger.debug("Markdown JSON bloğu soyuldu, ham JSON ayrıştırılıyor.")
        return extracted
    return text


class LLMClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.LLM_MODEL
        self.timeout = settings.LLM_TIMEOUT

    async def generate_json(self, prompt: str, system_prompt: str) -> dict:
        """
        Ollama sohbet API'sine sistem ve kullanıcı promptları gönderir,
        çıkış formatını JSON olarak zorlar.

        LLM yanıtı Markdown bloğuyla sarmalıysa (```json ... ```)
        otomatik olarak temizlenir.
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

        # content_str'yi try dışında tanımla: JSONDecodeError bloğunda
        # erişilebilir olması için (aksi hâlde NameError riski).
        content_str = ""

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

                # Markdown sarmalayıcıyı temizle, ardından parse et
                clean_str = _strip_markdown_json(content_str)
                return json.loads(clean_str)

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Ollama sunucusu HTTP hatası döndürdü: "
                f"{e.response.status_code} - {e.response.text}"
            )
            raise
        except json.JSONDecodeError as e:
            logger.error(
                f"LLM yanıtı JSON olarak çözümlenemedi. "
                f"Ham içerik: {content_str!r}. Hata: {e}"
            )
            raise
        except Exception as e:
            logger.error(f"LLMClient iletişim hatası: {str(e)}")
            raise


# Singleton instance for easy import
llm_client = LLMClient()

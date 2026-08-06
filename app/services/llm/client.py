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
                
                # Robustness: Strip markdown code fences if present
                if content_str.startswith("```"):
                    if content_str.startswith("```json"):
                        content_str = content_str[7:]
                    else:
                        content_str = content_str[3:]
                    if content_str.endswith("```"):
                        content_str = content_str[:-3]
                    content_str = content_str.strip()

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

    async def analyze_cv_single_pass(
        self,
        cv_text: str,
        job_position: str = None,
        job_description: str = None
    ) -> dict:
        from app.services.llm.prompts import (
            CV_SINGLE_PASS_SYSTEM_PROMPT,
            CV_SINGLE_PASS_POSITION_USER_TEMPLATE,
            CV_SINGLE_PASS_JD_USER_TEMPLATE
        )
        if job_description and job_description.strip():
            prompt = CV_SINGLE_PASS_JD_USER_TEMPLATE.format(
                job_description=job_description,
                cv_text=cv_text
            )
        elif job_position and job_position.strip():
            prompt = CV_SINGLE_PASS_POSITION_USER_TEMPLATE.format(
                job_position=job_position,
                cv_text=cv_text
            )
        else:
            prompt = CV_SINGLE_PASS_POSITION_USER_TEMPLATE.format(
                job_position="Genel CV Analizi ve ATS Optimizasyonu",
                cv_text=cv_text
            )
            
        return await self.generate_json(
            prompt=prompt,
            system_prompt=CV_SINGLE_PASS_SYSTEM_PROMPT
        )

    async def evaluate_cv_with_criteria(self, cv_text: str, criteria: list) -> dict:
        from app.services.llm.prompts import (
            CV_EVALUATION_WITH_CRITERIA_SYSTEM_PROMPT,
            CV_EVALUATION_WITH_CRITERIA_USER_TEMPLATE
        )
        criteria_str = json.dumps(criteria, indent=2, ensure_ascii=False)
        prompt = CV_EVALUATION_WITH_CRITERIA_USER_TEMPLATE.format(
            criteria=criteria_str,
            cv_text=cv_text
        )
        return await self.generate_json(
            prompt=prompt,
            system_prompt=CV_EVALUATION_WITH_CRITERIA_SYSTEM_PROMPT
        )

# Singleton instance for easy import
llm_client = LLMClient()


from typing import Any, Dict, List, Optional


def cv_analiz_et(cv_metni: str, parsed_skills: List[str], llm_puani: Optional[int] = None) -> Dict[str, Any]:
    """
    Şu an için basit bir stub fonksiyonudur.
    Gerçek CV analizini ileride daha sağlıklı bir şekilde dolduracağız.
    """
    return {
        "final_score": llm_puani or 0,
        "breakdown": {
            "skill_score": 0,
            "keyword_score": 0,
            "formatting_score": 0,
        },
        "summary": {
            "skill_count": len(parsed_skills),
            "llm_score": llm_puani or 0,
        },
    }

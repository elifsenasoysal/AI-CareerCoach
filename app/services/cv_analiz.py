from typing import Any, Dict, List, Optional


def cv_analiz_et(cv_metni: str, parsed_skills: List[str], llm_puani: Optional[int] = None) -> Dict[str, Any]:
    """
    CV metnini, çıkarılan becerileri ve LLM puanını analiz ederek
    detaylı bir alt kırılım ve özet raporu hazırlar.
    """
    base_score = llm_puani or 0
    
    if base_score > 0:
        # LLM puanı mevcutsa, alt kırılımları bu puana oranlayarak dağıtır
        skill_score = round(base_score * 0.4)
        keyword_score = round(base_score * 0.3)
        formatting_score = round(base_score * 0.3)
    else:
        # LLM puanı yoksa (yedek akışta), basit kural tabanlı bir hesaplama yapar
        skill_score = min(100, len(parsed_skills) * 10)
        keyword_score = min(100, len(cv_metni) // 50)
        formatting_score = 70
        base_score = round((skill_score * 0.4) + (keyword_score * 0.3) + (formatting_score * 0.3))

    return {
        "final_score": base_score,
        "breakdown": {
            "skill_score": skill_score,
            "keyword_score": keyword_score,
            "formatting_score": formatting_score,
        },
        "summary": {
            "skill_count": len(parsed_skills),
            "llm_score": llm_puani or 0,
        },
    }


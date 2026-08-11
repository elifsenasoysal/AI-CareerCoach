from typing import Any, Dict, List, Optional


def cv_analiz_et(
    cv_metni: str,
    parsed_skills: List[str],
    llm_puani: Optional[int] = None,
    score_breakdown: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """
    LLM'den gelen CV analiz sonuçlarını birleştirir ve normalize eder.

    Seçenek A uygulaması: score_breakdown doğrudan LLM'den alınır.
    LLM breakdown döndürmemişse (eski davranış / fallback) matematiksel
    dağılıma (B seçeneği) otomatik olarak geçer; böylece breakdown
    hiçbir zaman sıfır dönmez.

    Args:
        cv_metni:        Ham CV metni (ileride yerel analiz için kullanılabilir).
        parsed_skills:   LLM'nin çıkardığı beceri listesi.
        llm_puani:       LLM'nin ürettiği genel ATS puanı (0-100).
        score_breakdown: LLM'den gelen alt puan kırılımı:
                         {"skills_score": int, "keywords_score": int, "formatting_score": int}

    Returns:
        {
            "final_score": int,        # Genel ATS puanı
            "breakdown": {
                "skill_score":      int,   # max 40
                "keyword_score":    int,   # max 30
                "formatting_score": int,   # max 30
            },
            "summary": {
                "skill_count": int,
                "llm_score":   int,
            },
        }
    """
    base = llm_puani or 0

    if score_breakdown:
        # --- Seçenek A: LLM'den gelen gerçek kırılım ---
        skills_score      = _clamp(score_breakdown.get("skills_score", 0),      max_val=40)
        keywords_score    = _clamp(score_breakdown.get("keywords_score", 0),    max_val=30)
        formatting_score  = _clamp(score_breakdown.get("formatting_score", 0),  max_val=30)

        # LLM bazen yuvarlama hatası yapabilir; toplamı ats_score'a kilitle.
        total = skills_score + keywords_score + formatting_score
        if total != base and base > 0:
            # Oransal olarak yeniden ölçekle
            ratio = base / total if total > 0 else 1
            skills_score     = round(skills_score     * ratio)
            keywords_score   = round(keywords_score   * ratio)
            formatting_score = base - skills_score - keywords_score  # kalan fark son kaleme gider
    else:
        # --- Seçenek B fallback: matematiksel dağılım ---
        # LLM score_breakdown döndürmediyse (eski model, timeout vb.) buraya düşer.
        skills_score      = round(base * 0.40)  # %40
        keywords_score    = round(base * 0.30)  # %30
        formatting_score  = base - skills_score - keywords_score  # kalan (yuvarlama hatasını telafi eder)

    return {
        "final_score": base,
        "breakdown": {
            "skill_score":      skills_score,
            "keyword_score":    keywords_score,
            "formatting_score": formatting_score,
        },
        "summary": {
            "skill_count": len(parsed_skills),
            "llm_score":   base,
        },
    }


def _clamp(value: int, min_val: int = 0, max_val: int = 100) -> int:
    """Değeri [min_val, max_val] aralığına sıkıştır."""
    return max(min_val, min(max_val, int(value)))

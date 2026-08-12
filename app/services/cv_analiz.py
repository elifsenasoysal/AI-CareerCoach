from typing import Any, Dict, List, Optional


def cv_analiz_et(
    cv_metni: str,
    parsed_skills: List[str],
    llm_puani: Optional[int] = None,
    score_breakdown: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """
    LLM'den gelen CV analiz sonuçlarını birleştirir ve normalize eder.

    Seçenek A uygulaması: score_breakdown mümkün olduğunda doğrudan LLM'den
    alınır. Aşağıdaki durumlarda Seçenek B'ye (matematiksel dağılım: %40 /
    %30 / %30) otomatik olarak düşülür — böylece breakdown hiçbir zaman
    sıfır ya da tutarsız dönmez:
      1) LLM score_breakdown döndürmediyse (eski model / timeout / hata).
      2) LLM score_breakdown döndürdü ama üç alan da 0 ise (boş kırılım).
      3) LLM'in kırılım toplamı ile ats_score birbirinden çok farklıysa ve
         oransal ölçekleme sonrasında bile negatif/tutarsız bir sonuç
         oluşuyorsa (aşırı yuvarlama sapması durumunda güvenli tarafta kal).

    Args:
        cv_metni: Ham CV metni (ileride yerel analiz için kullanılabilir).
        parsed_skills: LLM'nin çıkardığı beceri listesi.
        llm_puani: LLM'nin ürettiği genel ATS puanı (0-100).
        score_breakdown: LLM'den gelen alt puan kırılımı:
            {"skills_score": int, "keywords_score": int, "formatting_score": int}

    Returns:
        {
            "final_score": int,       # Genel ATS puanı
            "breakdown": {
                "skill_score": int,       # max 40
                "keyword_score": int,     # max 30
                "formatting_score": int,  # max 30
            },
            "summary": {
                "skill_count": int,
                "llm_score": int,
            },
        }
    """
    base = _clamp(llm_puani or 0, max_val=100)

    skills_score, keywords_score, formatting_score = _resolve_breakdown(
        base=base, score_breakdown=score_breakdown
    )

    return {
        "final_score": base,
        "breakdown": {
            "skill_score": skills_score,
            "keyword_score": keywords_score,
            "formatting_score": formatting_score,
        },
        "summary": {
            "skill_count": len(parsed_skills),
            "llm_score": base,
        },
    }


def _resolve_breakdown(
    base: int, score_breakdown: Optional[Dict[str, int]]
) -> tuple[int, int, int]:
    """score_breakdown'ı güvenli biçimde 3 alana (skills/keywords/formatting)
    çözümler; LLM verisi eksik/tutarsız/boşsa matematiksel dağılıma düşer."""

    if score_breakdown:
        skills_score = _clamp(score_breakdown.get("skills_score", 0), max_val=40)
        keywords_score = _clamp(score_breakdown.get("keywords_score", 0), max_val=30)
        formatting_score = _clamp(score_breakdown.get("formatting_score", 0), max_val=30)
        total = skills_score + keywords_score + formatting_score

        # LLM boş/sıfır bir kırılım döndürdüyse (örn. tüm alanlar 0) ama
        # genel puan (base) mevcutsa -> matematiksel dağılıma düş.
        if total == 0:
            return _mathematical_fallback(base)

        # Kırılım toplamı ats_score ile birebir uyuşuyorsa doğrudan kullan.
        if total == base:
            return skills_score, keywords_score, formatting_score

        # Kırılım var ama toplam base'den farklı (yuvarlama hatası vb.) ->
        # oranı koruyarak base'e yeniden ölçekle.
        if base > 0:
            ratio = base / total
            # BUG FIX (kod incelemesinde tespit edildi): ratio > 1 olduğunda
            # (örn. base=90, total=50 -> ratio=1.8) round(skills_score * ratio)
            # 40 üst sınırını rahatlıkla aşabiliyordu (örn. 40 * 1.8 = 72).
            # Ölçekleme sonrasında alan bazlı üst sınırları TEKRAR uygulamak
            # zorunlu — aksi halde API sözleşmesi (skill_score <= 40 vb.)
            # ihlal edilir.
            skills_score = _clamp(round(skills_score * ratio), max_val=40)
            keywords_score = _clamp(round(keywords_score * ratio), max_val=30)
            # Kalan farkı formatting_score'a yükle.
            formatting_score = base - skills_score - keywords_score
            # Kalan değer negatifse VEYA kendi üst sınırını (30) aşıyorsa,
            # (yani skills/keywords'e clamp uygulanması formatting'e aşırı
            # yük bindirdiyse) tutarsız bir dağılım üretmek yerine güvenli
            # tarafta kal: matematiksel dağılıma düş.
            if formatting_score < 0 or formatting_score > 30:
                return _mathematical_fallback(base)
            return skills_score, keywords_score, formatting_score

        # base == 0 ama kırılım toplamı > 0 ise (tutarsız veri) -> güvenli
        # taraf: her şeyi sıfırlamak yerine LLM'in verdiği kırılımı olduğu
        # gibi kabul et (kullanıcıya en azından anlamlı bir dağılım göster).
        return skills_score, keywords_score, formatting_score

    # score_breakdown hiç gelmediyse (None) -> Seçenek B fallback.
    return _mathematical_fallback(base)


def _mathematical_fallback(base: int) -> tuple[int, int, int]:
    """Seçenek B: %40 / %30 / %30 matematiksel dağılım.
    Yuvarlama farkını formatting_score'a yükleyerek toplamın her zaman
    base'e eşit kalmasını garanti eder."""
    skills_score = round(base * 0.40)
    keywords_score = round(base * 0.30)
    formatting_score = base - skills_score - keywords_score
    return skills_score, keywords_score, formatting_score


def _clamp(value: Any, min_val: int = 0, max_val: int = 100) -> int:
    """Değeri [min_val, max_val] aralığına sıkıştırır; geçersiz/eksik
    değerlerde (None, string, vb.) sessizce 0'a düşer."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 0
    return max(min_val, min(max_val, value))
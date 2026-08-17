from app.api.endpoints.cv import _sanitize_llm_cv_output, _filter_skills_against_cv_text, _build_job_context
from app.services.llm.prompts import CV_ANALYSIS_SYSTEM_PROMPT
from app.services.cv_analiz import cv_analiz_et


def test_filter_skills_against_cv_text_removes_hallucinated_job_skills():
    cv_text = """
    Sakarya Üniversitesi Bilgisayar Mühendisliği adayı.
    Python, FastAPI, ReactJS ve Docker projeleri geliştirdi.
    LLM (Büyük Dil Modelleri) ve RAG tabanlı retrieval mimarisi uyguladı.
    """

    llm_skills = [
        "Python", "FastAPI", "ReactJS", "Docker", "LLMs", "RAG systems",
        "Qdrant", "pgvector", "Kubernetes", "pytest", "vitest"
    ]

    filtered = _filter_skills_against_cv_text(llm_skills, cv_text)

    # Skills in CV text must be kept
    assert "Python" in filtered
    assert "FastAPI" in filtered
    assert "ReactJS" in filtered
    assert "Docker" in filtered
    assert "LLMs" in filtered
    assert "RAG systems" in filtered

    # Skills NOT in CV text must be filtered out
    assert "Qdrant" not in filtered
    assert "pgvector" not in filtered
    assert "Kubernetes" not in filtered
    assert "pytest" not in filtered
    assert "vitest" not in filtered
    assert len(filtered) == 6


def test_sanitize_llm_cv_output_recovers_score_and_cleans_meta_strings():
    raw_llm_output = {
        "parsed_skills": ["Python", "FastAPI", "ReactJS"],
        "suggested_improvements": [
            "CV'de Senior AI Engineer pozisyona uygunluğunu vurgulayın.",
            "Pytest ve vitest kullanarak test coverage geliştirin.",
            "ats_score: 75",
            "score_breakdown"
        ],
        "ats_score": 0,
        "score_breakdown": None
    }

    sanitized = _sanitize_llm_cv_output(raw_llm_output)

    # 1. ats_score MUST be extracted from suggested_improvements
    assert sanitized["ats_score"] == 75

    # 2. Meta strings must be removed from suggested_improvements
    assert "ats_score: 75" not in sanitized["suggested_improvements"]
    assert "score_breakdown" not in sanitized["suggested_improvements"]
    assert len(sanitized["suggested_improvements"]) == 2
    assert "CV'de Senior AI Engineer" in sanitized["suggested_improvements"][0]


def test_sanitize_llm_cv_output_handles_variations():
    raw_llm_output = {
        "parsed_skills": ["Python"],
        "suggested_improvements": [
            "ATS_SCORE = 80",
            "score_breakdown",
            "parsed_skills",
            "Kıdem düzeyinize uygun projeler ekleyin."
        ],
        "ats_score": None
    }

    sanitized = _sanitize_llm_cv_output(raw_llm_output)
    assert sanitized["ats_score"] == 80
    assert sanitized["suggested_improvements"] == ["Kıdem düzeyinize uygun projeler ekleyin."]


def test_sanitize_llm_cv_output_preserves_valid_output():
    valid_output = {
        "parsed_skills": ["Python", "Docker"],
        "suggested_improvements": ["Projelerinize metrik ekleyin."],
        "ats_score": 82,
        "score_breakdown": {"skills_score": 35, "keywords_score": 25, "formatting_score": 22}
    }

    sanitized = _sanitize_llm_cv_output(valid_output)
    assert sanitized["ats_score"] == 82
    assert len(sanitized["suggested_improvements"]) == 1
    assert sanitized["suggested_improvements"][0] == "Projelerinize metrik ekleyin."


def test_cv_analiz_et_calculates_mathematical_fallback():
    result = cv_analiz_et(
        cv_metni="Sample CV text",
        parsed_skills=["Python", "FastAPI"],
        llm_puani=75,
        score_breakdown=None
    )

    assert result["final_score"] == 75
    assert result["breakdown"]["skill_score"] == 30  # round(75 * 0.40) = 30
    assert result["breakdown"]["keyword_score"] == 22 # round(75 * 0.30) = 22 in Python 3
    assert result["breakdown"]["formatting_score"] == 23 # 75 - 30 - 22 = 23
    assert result["summary"]["skill_count"] == 2


def test_build_job_context_when_position_is_empty():
    # Test None, empty string, and whitespace
    ctx_none = _build_job_context(None, None, None)
    ctx_empty = _build_job_context("", None, None)
    ctx_space = _build_job_context("   ", None, None)

    for ctx in (ctx_none, ctx_empty, ctx_space):
        assert "Hedef Pozisyon: Belirtilmedi" in ctx
        assert "Hedef pozisyon belirtilmediği için genel analiz yapılmıştır" in ctx
        assert "Genel ATS kuralları" in ctx


def test_system_prompt_contains_no_target_position_rule():
    assert "IF NO TARGET POSITION IS PROVIDED" in CV_ANALYSIS_SYSTEM_PROMPT
    assert "Hedef pozisyon belirtilmediği için genel analiz yapılmıştır." in CV_ANALYSIS_SYSTEM_PROMPT


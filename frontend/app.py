import gradio as gr
import requests

API_BASE_URL = "http://localhost:8000/api/v1"

# ---------------------------------------------------------------------------
# GSB Mavisi Zemin, Beyaz Kutucuklar & Büyük Koyu Sekme CSS
# ---------------------------------------------------------------------------
custom_css = """
/* ── GRADIO GLOBAL TEMA DEĞİŞKENLERİNİ EZME (Koyu Metin Zorlaması) ── */
:root, .gradio-container {
    --body-text-color: #0f172a !important;
    --input-text-color: #0f172a !important;
    --block-label-text-color: #005999 !important;
    --block-title-text-color: #005999 !important;
    --neutral-500: #64748b !important;
    --neutral-400: #94a3b8 !important;
    --border-color-primary: #cbd5e1 !important;
}

/* ── SAYFA GENELİ: TAM GSB MAVİSİ ARKA PLAN ── */
html, body, .gradio-container, .main, .app {
    background: linear-gradient(180deg, #007bc7 0%, #005999 100%) !important;
    color: #1e293b !important;
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
}

.gradio-container {
    padding: 32px 48px !important;
    box-sizing: border-box !important;
}

/* ── MODERN, BÜYÜK VE KOYU SEKMELER (TABS) ── */
div.tabs {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

div.tab-nav {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 24px !important;
    background: rgba(255, 255, 255, 0.25) !important;
    border: 2px solid rgba(255, 255, 255, 0.4) !important;
    border-radius: 24px !important;
    padding: 14px 20px !important;
    margin-bottom: 36px !important;
    backdrop-filter: blur(16px) !important;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15) !important;
}

div.tab-nav::after, div.tab-nav::before,
div.tabs::after, div.tabs::before,
button::after, button::before {
    display: none !important;
    content: none !important;
    border: none !important;
}

/* Sekme Butonları - Koyu & Büyük */
div.tab-nav button {
    background: rgba(255, 255, 255, 0.85) !important;
    border: none !important;
    border-radius: 16px !important;
    color: #0c2340 !important;
    font-size: 1.4rem !important;
    font-weight: 800 !important;
    padding: 20px 42px !important;
    cursor: pointer !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    display: flex !important;
    align-items: center !important;
    gap: 14px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}

div.tab-nav button:hover {
    color: #007bc7 !important;
    background: #ffffff !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 20px rgba(0,0,0,0.15) !important;
}

/* Seçili Sekme */
div.tab-nav button.selected {
    background: #ffffff !important;
    color: #007bc7 !important;
    font-weight: 900 !important;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.25) !important;
    transform: translateY(-3px) !important;
    border-bottom: 4px solid #005999 !important;
}

.tabitem {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

/* ── HERO SECTION ── */
/* ── HERO SECTION (Başlık Beyaz Metin Düzeltmesi) ── */
.hero-section {
    background: rgba(12, 35, 64, 0.85) !important;
    border-radius: 20px !important;
    padding: 40px 48px !important;
    margin-bottom: 32px !important;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.2) !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    border-left: 8px solid #38bdf8 !important;
    color: #ffffff !important;
    backdrop-filter: blur(10px) !important;
}

/* Başlık ve içindeki tüm elemanları BEYAZ yap */
.hero-title, 
.hero-title *, 
.hero-title span {
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    margin-bottom: 0 !important;
}

.hero-title {
    margin-bottom: 24px !important;
    display: flex !important;
    align-items: center !important;
    gap: 14px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2) !important;
    padding-bottom: 18px !important;
}

.hero-title {
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    margin-bottom: 24px !important;
    display: flex !important;
    align-items: center !important;
    gap: 14px !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2) !important;
    padding-bottom: 18px !important;
}

.hero-grid {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 36px !important;
    margin-bottom: 24px !important;
}

.hero-col h3 {
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    color: #7dd3fc !important;
    margin-bottom: 12px !important;
}

.hero-col p {
    font-size: 1.1rem !important;
    line-height: 1.8 !important;
    color: #f1f5f9 !important;
    margin: 0 !important;
}

.hero-bottom {
    border-top: 1px solid rgba(255, 255, 255, 0.2) !important;
    padding-top: 20px !important;
    margin-top: 20px !important;
}

.hero-bottom h3 {
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: #bae6fd !important;
    margin-bottom: 12px !important;
}

.hero-bottom ul {
    list-style-type: disc !important;
    padding-left: 20px !important;
    margin: 0 !important;
}

.hero-bottom li {
    font-size: 1.05rem !important;
    line-height: 1.8 !important;
    color: #ffffff !important;
    margin-bottom: 8px !important;
}

/* ── BEYAZ KUTUCUKLAR (FORM & YÜKLEME ALANLARI) ── */
.form-card, .upload-card, .result-card {
    background: #ffffff !important;
    border-radius: 20px !important;
    border: 1px solid #e2e8f0 !important;
    padding: 32px !important;
    margin-bottom: 24px !important;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.12) !important;
    color: #0f172a !important;
}

/* İç kapsayıcıların arka plan ve kenarlıklarını sıfırla */
.form-card .block, .form-card .form, .form-card fieldset, 
.form-card label, .form-card .gr-box,
.upload-card .block, .upload-card .form, .upload-card label,
.upload-card .gr-box {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

/* Başlıklar (AD, SOYAD, CV DOSYANIZI YÜKLEYİN vb.) */
.form-card label span, 
.upload-card label span,
.upload-card [data-testid="block-label"],
.upload-card .label-text {
    color: #005999 !important;
    font-size: 0.9rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    margin-bottom: 8px !important;
    display: block !important;
}

/* Input ve Textarea Kutuları */
.form-card input[type="text"], 
.form-card textarea, 
.form-card select {
    background-color: #f8fafc !important;
    color: #0f172a !important;
    border: 1.5px solid #cbd5e1 !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
    font-size: 1rem !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
}

/* Silik İpucu Yazıları (Placeholder) */
.form-card input::placeholder, 
.form-card textarea::placeholder,
input::placeholder, textarea::placeholder {
    color: #64748b !important;
    opacity: 1 !important;
}

.form-card input[type="text"]:focus, .form-card textarea:focus {
    border-color: #007bc7 !important;
    box-shadow: 0 0 0 4px rgba(0, 123, 199, 0.2) !important;
    outline: none !important;
    background-color: #ffffff !important;
}

/* ── SAYI VE INPUT OKLARINI TAMAMEN KALDIRMA ── */
input::-webkit-outer-spin-button,
input::-webkit-inner-spin-button,
.form-card input::-webkit-outer-spin-button,
.form-card input::-webkit-inner-spin-button {
    -webkit-appearance: none !important;
    margin: 0 !important;
}

input[type="number"],
.form-card input[type="number"] {
    -moz-appearance: textfield !important;
    appearance: textfield !important;
}

/* ── CV YÜKLEME ALANI VE DÜZELTMELERİ ── */
.upload-card [data-testid="file-upload"], 
.upload-card .dropzone,
.upload-card .file-upload,
.upload-card [data-testid="file-upload"] > div {
    background-color: #f0f9ff !important;
    background: #f0f9ff !important;
    border: 2px dashed #007bc7 !important;
    border-radius: 14px !important;
    padding: 32px !important;
    transition: all 0.3s ease !important;
}

.upload-card [data-testid="file-upload"]:hover, 
.upload-card .dropzone:hover {
    border-color: #005999 !important;
    background-color: #e0f2fe !important;
}

/*Yükleme alanı içindeki zeminleri temizle */
.upload-card *, 
.upload-card [data-testid="file-upload"] * {
    background-color: transparent !important;
}

/* Yükleme alanındaki BÜTÜN metinleri ve ikonları koyu lacivert yap */
.upload-card span,
.upload-card p,
.upload-card div,
.upload-card label,
.upload-card svg,
.upload-card [data-testid="file-upload"] span,
.upload-card [data-testid="file-upload"] p {
    color: #0c2340 !important;
    fill: #0c2340 !important;
    font-weight: 600 !important;
    opacity: 1 !important;
}

/* BUTONLAR */
button.primary-btn {
    background: linear-gradient(135deg, #007bc7 0%, #005999 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    font-size: 1.15rem !important;
    padding: 16px 32px !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
    margin-top: 12px !important;
    box-shadow: 0 6px 20px rgba(0, 89, 153, 0.3) !important;
}

button.primary-btn:hover {
    background: linear-gradient(135deg, #0091ea 0%, #007bc7 100%) !important;
    box-shadow: 0 8px 25px rgba(0, 123, 199, 0.45) !important;
    transform: translateY(-2px) !important;
}

button.secondary-btn {
    background: #f1f5f9 !important;
    color: #005999 !important;
    border: 2px solid #007bc7 !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    font-size: 1.05rem !important;
    padding: 14px 28px !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
    margin-top: 12px !important;
}

button.secondary-btn:hover {
    background: #007bc7 !important;
    color: #ffffff !important;
}

/* Sonuç Kartları */
.result-card {
    border-top: 6px solid #007bc7 !important;
}

.result-card h3 {
    color: #005999 !important;
    border-bottom: 2px solid #f1f5f9 !important;
    padding-bottom: 10px !important;
}

/* Temizlik */
.clear-button, button[aria-label="Clear"], .gr-input-icon, .select-info {
    display: none !important;
}

/* ── GSB FOOTER TASARIMI ── */
#gsb-footer-container {
    width: 100% !important;
    display: block !important;
    margin-top: 60px !important;
    clear: both !important;
}

.footer_left_right {
    background-color: rgba(12, 35, 64, 0.9) !important;
    padding: 36px 24px 24px 24px !important;
    border-radius: 20px !important;
    color: #ffffff !important;
    width: 100% !important;
    box-sizing: border-box !important;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.25) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
}

.footer_left_right_logos {
    list-style: none !important;
    padding: 0 !important;
    margin: 0 0 28px 0 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 36px !important;
    flex-wrap: wrap !important;
}

.footer_left_right_logos li img {
    height: 65px !important;
    width: auto !important;
    object-fit: contain !important;
}

.footer_left_right_bottom {
    border-top: 1px dashed rgba(255, 255, 255, 0.3) !important;
    padding-top: 24px !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    gap: 18px !important;
}

.footer_left_right_bottom_copyright {
    font-size: 1.15rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.5px !important;
    color: #ffffff !important;
    text-align: center !important;
}

.footer_left_right_bottom_social {
    list-style: none !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    gap: 16px !important;
}

.footer_left_right_bottom_social li a {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 44px !important;
    height: 44px !important;
    background-color: rgba(255, 255, 255, 0.2) !important;
    border-radius: 50% !important;
    transition: all 0.3s ease !important;
}

.footer_left_right_bottom_social li a:hover {
    background-color: #ffffff !important;
    transform: translateY(-3px) !important;
}

.footer_left_right_bottom_social li a svg {
    width: 22px !important;
    height: 22px !important;
    fill: #ffffff !important;
}

.footer_left_right_bottom_social li a:hover svg {
    fill: #007bc7 !important;
}

.st0 { fill: #ffffff !important; }
"""

# ---------------------------------------------------------------------------
# CV Analiz Fonksiyonu
# ---------------------------------------------------------------------------
def cv_analiz_et(pdf_file, ad, soyad, universite, bolum, job_position, job_description):
    if not pdf_file:
        return (
            gr.update(value="⚠️ Lütfen analiz başlamadan önce bir PDF dosyası yükleyin.", visible=True),
            "", "", "", "",
            gr.update(visible=False), gr.update(visible=False)
        )

    try:
        with open(pdf_file, "rb") as f:
            files = {"file": (pdf_file, f, "application/pdf")}
            data = {
                "first_name": ad,
                "last_name": soyad,
                "university": universite,
                "department": bolum,
            }
            if job_position:
                data["job_position"] = job_position
            if job_description:
                data["job_description"] = job_description

            response = requests.post(
                f"{API_BASE_URL}/cv/analyze", files=files, data=data, timeout=90
            )

        if response.status_code != 200:
            error_detail = response.json().get("detail", response.text)
            return (
                gr.update(value=f"❌ Hata: {error_detail}", visible=True),
                "", "", "", "",
                gr.update(visible=False), gr.update(visible=False)
            )

        res = response.json()
        ats = res.get("ats_score", 0)
        final = res.get("final_score", 0)
        breakdown = res.get("score_breakdown", {})

        score_md = (
            f"### 🎯 Değerlendirme Puanı\n\n"
            f"- **ATS Uyum Puanı:** <span style='color:#007bc7; font-size:1.4rem; font-weight:bold;'>{ats} / 100</span>\n"
            f"- **Genel Skor:** <span style='color:#007bc7; font-size:1.4rem; font-weight:bold;'>{final} / 100</span>\n\n"
            f"| Puan Kriteri | Değer |\n|---|---|\n"
            f"| 🧠 Teknik Yetkinlik | **{breakdown.get('skill_score', 0)} / 40** |\n"
            f"| 🔑 Anahtar Kelimeler | **{breakdown.get('keyword_score', 0)} / 30** |\n"
            f"| 📐 Format ve Düzen | **{breakdown.get('formatting_score', 0)} / 30** |"
        )

        skills = res.get("parsed_skills", [])
        skills_md = "### 🛠️ Tespit Edilen Beceriler\n" + (
            " • ".join(skills) if skills else "Herhangi bir beceri ayrıştırılamadı."
        )

        improvements = res.get("suggested_improvements", [])
        improvements_md = "### 💡 İyileştirme Önerileri\n" + "\n".join(
            [f"- {imp}" for imp in improvements]
        )

        llm_feedback = res.get(
            "llm_review",
            res.get(
                "summary",
                "Yapay zeka analizini tamamladı. Özgeçmişiniz hedeflenen pozisyon ve standartlar doğrultusunda detaylıca değerlendirilmiştir.",
            ),
        )

        llm_feedback_md = f"### 🤖 Yapay Zeka Detaylı Analiz & Değerlendirme Raporu\n\n{llm_feedback}"

        return (
            gr.update(value="", visible=False),
            score_md, skills_md, improvements_md, llm_feedback_md,
            gr.update(visible=True), gr.update(visible=True)
        )

    except requests.exceptions.ConnectionError:
        return (
            gr.update(value="❌ Backend servisine bağlanılamadı.", visible=True),
            "", "", "", "",
            gr.update(visible=False), gr.update(visible=False)
        )
    except Exception as e:
        return (
            gr.update(value=f"❌ Beklenmeyen hata: {str(e)}", visible=True),
            "", "", "", "",
            gr.update(visible=False), gr.update(visible=False)
        )


# ---------------------------------------------------------------------------
# Mülakat Fonksiyonları
# ---------------------------------------------------------------------------
def mulakat_baslat(role, experience_level, focus_areas_str):
    if not role or not role.strip():
        return (
            "", 0,
            gr.update(value="⚠️ Lütfen bir hedef rol girin.", visible=True),
            gr.update(value=""), gr.update(visible=False), gr.update(visible=False),
            gr.update(value="", visible=False), gr.update(interactive=True)
        )

    focus_areas = [f.strip() for f in focus_areas_str.split(",") if f.strip()] if focus_areas_str else []

    payload = {
        "role": role,
        "experience_level": experience_level,
        "focus_areas": focus_areas,
    }

    try:
        res = requests.post(f"{API_BASE_URL}/interview/start", json=payload, timeout=90)
        if res.status_code == 200:
            data = res.json()
            question_md = f"### ❓ {data['first_question']}"
            return (
                data["session_id"], 1,
                gr.update(value="", visible=False),
                gr.update(value=question_md),
                gr.update(visible=True), gr.update(visible=False),
                gr.update(value="", visible=True, interactive=True),
                gr.update(interactive=True)
            )
        error_detail = res.json().get("detail", res.text)
        return (
            "", 0,
            gr.update(value=f"❌ Hata: {error_detail}", visible=True),
            gr.update(value=""), gr.update(visible=False), gr.update(visible=False),
            gr.update(value="", visible=False), gr.update(interactive=True)
        )
    except Exception as e:
        return (
            "", 0,
            gr.update(value=f"❌ Hata: {str(e)}", visible=True),
            gr.update(value=""), gr.update(visible=False), gr.update(visible=False),
            gr.update(value="", visible=False), gr.update(interactive=True)
        )


def yanit_gonder(session_id, current_question_md, user_answer, question_count):
    if not session_id or not user_answer or not user_answer.strip():
        return (
            gr.update(value="⚠️ Lütfen cevabınızı girin.", visible=True),
            gr.update(value=current_question_md), gr.update(value=user_answer),
            question_count, gr.update(interactive=True)
        )

    clean_question = current_question_md.replace("### ❓", "").strip()
    payload = {"session_id": session_id, "question": clean_question, "answer": user_answer}

    try:
        res = requests.post(f"{API_BASE_URL}/interview/respond", json=payload, timeout=90)
        if res.status_code == 200:
            data = res.json()
            score = data.get("score", 0)
            feedback = data.get("feedback", "")
            feedback_md = f"### 📊 Puan: <span style='color:#007bc7;'>{score}/10</span>\n\n{feedback}"
            next_q = data.get("next_question")
            new_count = question_count + 1

            if next_q:
                return (
                    gr.update(value=feedback_md, visible=True),
                    gr.update(value=f"### ❓ {next_q}"),
                    gr.update(value="", interactive=True),
                    new_count, gr.update(interactive=True)
                )
            else:
                return (
                    gr.update(value=feedback_md, visible=True),
                    gr.update(value="### ✅ Mülakat tamamlandı!"),
                    gr.update(value="", interactive=False),
                    new_count, gr.update(interactive=False)
                )
        return (
            gr.update(value=f"❌ Hata", visible=True),
            gr.update(value=current_question_md), gr.update(value=user_answer),
            question_count, gr.update(interactive=True)
        )
    except Exception as e:
        return (
            gr.update(value=f"❌ Hata: {str(e)}", visible=True),
            gr.update(value=current_question_md), gr.update(value=user_answer),
            question_count, gr.update(interactive=True)
        )


def mulakati_sifirla():
    return (
        "", 0, gr.update(value="", visible=False), gr.update(value=""),
        gr.update(visible=False), gr.update(visible=False),
        gr.update(value="", visible=False, interactive=True), gr.update(interactive=True)
    )


# ---------------------------------------------------------------------------
# Gradio Arayüz Tasarımı
# ---------------------------------------------------------------------------
with gr.Blocks(title="AI Kariyer Koçu", css=custom_css) as demo:

    with gr.Tabs(elem_id="main-tabs"):
        # ── Sekme 1: CV Analizi ──────────────────────────────────────────
        with gr.Tab("📄 CV Analizi"):

            # Hero Alanı
            gr.HTML(
                """
                <div class="hero-section">
                    <div class="hero-title">
                        <span>📄</span>
                        <span>CV Analiz ve Değerlendirme</span>
                    </div>
                    <div class="hero-grid">
                        <div class="hero-col">
                            <h3>CV Analizi Nedir?</h3>
                            <p>Yapay zeka destekli CV değerlendirme sistemi; özgeçmişinizi güncel sektör kriterlerine, ATS standartlarına ve başvurduğunuz pozisyona göre analiz eder. Güçlü yönlerinizi ortaya çıkarır ve eksik noktalar için somut öneriler sunar.</p>
                        </div>
                        <div class="hero-col">
                            <h3>Yönerge</h3>
                            <p>Kişisel bilgilerinizi ve hedeflediğiniz pozisyonu doldurun. PDF formatındaki CV'nizi sağdaki alana yükleyin. "CV Analizini Başlat" butonuna basarak skorunuzu ve detaylı değerlendirme raporunu görüntüleyin.</p>
                        </div>
                    </div>
                    <div class="hero-bottom">
                        <h3>Analiz İşlemi İçin Dikkat Edilmesi Gereken Hususlar</h3>
                        <ul>
                            <li>Yükleyeceğiniz dosyanın orijinal PDF formatında olmasına özen gösteriniz.</li>
                            <li>Şifreli veya kilitli dosyalar yapay zeka tarafından okunamamaktadır.</li>
                            <li>Hedef pozisyon ve varsa İlan İş Tanımı eklemek analiz doğruluğunu doğrudan artıracaktır.</li>
                        </ul>
                    </div>
                </div>
                """
            )

            # Form ve CV Yükleme Alanı
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["form-card"]):
                    with gr.Row():
                        ad_input = gr.Textbox(label="AD", placeholder="Adınız", lines=1)
                        soyad_input = gr.Textbox(label="SOYAD", placeholder="Soyadınız", lines=1)

                    with gr.Row():
                        uni_input = gr.Textbox(label="ÜNİVERSİTE", placeholder="Örn: Başkent Üniversitesi", lines=1)
                        bolum_input = gr.Textbox(label="BÖLÜM", placeholder="Örn: Yönetim Bilişim Sistemleri", lines=1)

                    pos_input = gr.Textbox(
                        label="HEDEF POZİSYON",
                        placeholder="Örn: Frontend Developer, Veri Analisti...",
                        lines=1
                    )

                    desc_input = gr.Textbox(
                        label="İLANIN İŞ TANIMI (İSTEĞE BAĞLI)",
                        lines=3,
                        placeholder="İlan detaylarını buraya yapıştırabilirsiniz...",
                    )

                with gr.Column(scale=1, elem_classes=["upload-card"]):
                    file_input = gr.File(
                        label="CV DOSYANIZI YÜKLEYİN (PDF)",
                        file_types=[".pdf"],
                        type="filepath",
                    )
                    analyze_btn = gr.Button(
                        "🔍 CV Analizini Başlat",
                        variant="primary",
                        size="lg",
                        elem_classes=["primary-btn"],
                    )
                    cv_status = gr.Markdown(visible=False)

            # Sonuç Alanları
            with gr.Row(visible=False) as result_row_1:
                with gr.Column(scale=1, elem_classes=["result-card"]):
                    score_output = gr.Markdown()
                    skills_output = gr.Markdown()
                with gr.Column(scale=1, elem_classes=["result-card"]):
                    improvements_output = gr.Markdown()

            with gr.Row(visible=False) as result_row_2:
                with gr.Column(scale=1, elem_classes=["result-card"]):
                    llm_review_output = gr.Markdown()

            analyze_btn.click(
                fn=cv_analiz_et,
                inputs=[file_input, ad_input, soyad_input, uni_input, bolum_input, pos_input, desc_input],
                outputs=[cv_status, score_output, skills_output, improvements_output, llm_review_output, result_row_1, result_row_2],
            )

        # ── Sekme 2: AI Mülakat Simülatörü ──────────────────────────────
        with gr.Tab("🎙️ AI Mülakat Simülatörü"):
            session_state = gr.State("")
            question_count_state = gr.State(0)

            # Mülakat İçin Hero
            gr.HTML(
                """
                <div class="hero-section">
                    <div class="hero-title">
                        <span>🎙️</span>
                        <span>Yapay Zeka Mülakat Simülatörü</span>
                    </div>
                    <div class="hero-grid">
                        <div class="hero-col">
                            <h3>Mülakat Simülatörü Ne Yapar?</h3>
                            <p>Yapay zeka destekli mülakat simülatörü; hedeflediğiniz rol ve deneyim seviyesine özel dinamik sorular sorar, cevaplarınızı anında puanlar ve gelişmeniz gereken noktaları vurgular.</p>
                        </div>
                        <div class="hero-col">
                            <h3>Yönerge</h3>
                            <p>Hedef rolünüzü, deneyim seviyenizi ve odak alanlarınızı seçerek mülakatı başlatın. Her soruya verdiğiniz detaylı yanıtlar yapay zeka tarafından analiz edilecektir.</p>
                        </div>
                    </div>
                    <div class="hero-bottom">
                        <h3>Mülakatta Dikkat Edilmesi Gereken Hususlar</h3>
                        <ul>
                            <li>Cevaplarınızı olabildiğince açık, somut ve teknik örneklerle destekleyerek yazınız.</li>
                            <li>Odak alanlarını virgülle ayırarak girmeniz soruların isabetini artırır.</li>
                        </ul>
                    </div>
                </div>
                """
            )

            # Mülakat Ayar Formu
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["form-card"]):
                    with gr.Row(equal_height=True):
                        role_in = gr.Textbox(
                            label="HEDEF ROL", 
                            value="Python Developer",
                            scale=1,
                            lines=1
                        )
                        level_in = gr.Dropdown(
                            label="DENEYİM SEVİYESİ",
                            choices=["Junior", "Mid", "Senior"],
                            value="Mid",
                            scale=1
                        )

                    focus_in = gr.Textbox(
                        label="İLGİ ALANLARI",
                        value="FastAPI, SQL",
                        lines=1
                    )

                    with gr.Row():
                        start_btn = gr.Button("🚀 Mülakatı Başlat", variant="primary", elem_classes=["primary-btn"])
                        reset_btn = gr.Button("🔄 Mülakatı Sıfırla", elem_classes=["secondary-btn"])

                    start_status = gr.Markdown(visible=False)

            # Soru Alanı
            with gr.Row(visible=False) as question_row:
                with gr.Column(scale=1, elem_classes=["result-card"]):
                    question_box = gr.Markdown()

            # Cevap Formu
            with gr.Row():
                with gr.Column(scale=1, elem_classes=["form-card"]):
                    answer_in = gr.Textbox(
                        label="CEVABINIZ",
                        lines=4,
                        placeholder="Cevabınızı detaylıca yazın...",
                        visible=False,
                    )
                    submit_btn = gr.Button("📤 Cevabı Gönder", elem_classes=["secondary-btn"])

            # Geri Bildirim
            with gr.Row(visible=False) as feedback_row:
                with gr.Column(scale=1, elem_classes=["result-card"]):
                    feedback_box = gr.Markdown()

            start_btn.click(
                fn=mulakat_baslat,
                inputs=[role_in, level_in, focus_in],
                outputs=[session_state, question_count_state, start_status, question_box, question_row, feedback_row, answer_in, submit_btn],
            )

            submit_btn.click(
                fn=yanit_gonder,
                inputs=[session_state, question_box, answer_in, question_count_state],
                outputs=[feedback_box, question_box, answer_in, question_count_state, submit_btn],
            ).then(
                fn=lambda: gr.update(visible=True),
                inputs=None,
                outputs=[feedback_row],
            )

            reset_btn.click(
                fn=mulakati_sifirla,
                inputs=None,
                outputs=[session_state, question_count_state, start_status, question_box, question_row, feedback_row, answer_in, submit_btn],
            )

    # =========================================================================
    # GSB FOOTER
    # =========================================================================
    gr.HTML(
        """
        <div id="gsb-footer-container">
            <div class="footer_left_right">
                <ul class="footer_left_right_logos">
                    <li><a href="https://www.gsb.gov.tr" target="_blank"><img src="https://e-rehberlik.gsb.gov.tr/dist/images/gsb-logo.svg" alt="T.C. Gençlik ve Spor Bakanlığı Logo"></a></li>
                    <li><a href="https://e-rehberlik.gsb.gov.tr" target="_blank"><img src="https://e-rehberlik.gsb.gov.tr/dist/images/e-rehberlik-logo.svg" alt="T.C. Gençlik ve Spor Bakanlığı E-rehberlik Logo"></a></li>
                    <li><a href="https://edu.gsb.gov.tr" target="_blank"><img src="https://e-rehberlik.gsb.gov.tr/dist/images/gsb-edu.svg" alt="T.C. Gençlik ve Spor Bakanlığı Edu Logo"></a></li>
                </ul>
                <div class="footer_left_right_bottom">
                    <div class="footer_left_right_bottom_copyright">T.C. GENÇLİK VE SPOR BAKANLIĞI 2024</div>
                    <ul class="footer_left_right_bottom_social">
                        <li><a href="https://www.facebook.com/gencliksporbak" target="_blank" rel="noreferrer"><svg id="Capa_1" viewBox="0 0 238.9 511.9"><path id="Facebook" class="st0" d="M51.6 99.1v70.5H0v86.2h51.6v256.1h106.1V255.8h71.2s6.7-41.3 9.9-86.5h-80.7v-58.9c0-8.8 11.6-20.7 23-20.7h57.8V0h-78.6C49-.1 51.6 86.2 51.6 99.1z"></path></svg></a></li>
                        <li><a href="https://twitter.com/gencliksporbak" target="_blank" rel="noreferrer"><svg viewBox="0 0 512.1 416"><path d="M512.1 49.2c-18.8 8.4-39.1 14-60.3 16.5 21.7-13 38.3-33.6 46.2-58.1-20.3 12-42.8 20.8-66.7 25.5C412.1 12.7 384.8 0 354.6 0c-58 0-105 47-105 105 0 8.2.9 16.3 2.7 23.9C165 124.5 87.6 82.7 35.8 19.1c-9 15.5-14.2 33.6-14.2 52.8 0 36.4 18.5 68.6 46.7 87.4-17.2-.5-33.4-5.3-47.6-13.1v1.3c0 50.9 36.2 93.3 84.3 103-8.8 2.4-18.1 3.7-27.7 3.7-6.8 0-13.3-.7-19.8-1.9 13.4 41.7 52.2 72.1 98.1 72.9-35.9 28.2-81.2 45-130.5 45-8.5 0-16.8-.5-25.1-1.5 46.6 30 101.8 47.3 161.1 47.3C354.3 416 460 255.9 460 117.1c0-4.6-.1-9.1-.3-13.6 20.5-14.7 38.3-33.2 52.4-54.3z" fill="#ffffff"></path></svg></a></li>
                        <li><a href="https://www.instagram.com/gencliksporbak/" target="_blank" rel="noreferrer"><svg viewBox="0 0 512.001 512.001"><path d="M373.406 0H138.594C62.172 0 0 62.172 0 138.594V373.41C0 449.828 62.172 512 138.594 512H373.41C449.828 512 512 449.828 512 373.41V138.594C512 62.172 449.828 0 373.406 0zM256 395.996c-77.195 0-139.996-62.8-139.996-139.996S178.804 116.004 256 116.004 395.996 178.804 395.996 256 333.196 395.996 256 395.996zM399.344 149.02c-22.813 0-41.367-18.555-41.367-41.368s18.554-41.37 41.367-41.37 41.37 18.558 41.37 41.37-18.558 41.368-41.368zm0 0" fill="#ffffff"></path></svg></a></li>
                    </ul>
                </div>
            </div>
        </div>
        """
    )

if __name__ == "__main__":
    demo.launch()
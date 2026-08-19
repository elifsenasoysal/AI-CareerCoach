# 🤖 AI Kariyer Koçu - Gradio Frontend Geliştirme Kılavuzu

Bu doküman, **AI Kariyer Koçu** projesinin Python/Gradio tabanlı ön yüz (frontend) arayüzünü **Yapay Zeka (AI Coding Assistants, LLM, Copilot vb.)** kullanarak sıfırdan geliştirmek için gereken **tüm API detaylarını, veri yapılarını, UI bileşen tasarımlarını ve AI Prompt şablonlarını** içerir.

---

## 📐 1. Mimari Genel Bakış

```
┌───────────────────────────────────────────────────────┐
│              Gradio Web UI  (frontend/app.py)         │
│  ┌───────────────────────┐ ┌───────────────────────┐  │
│  │   CV Analizi Sekmesi  │ │ Mülakat Simülatörü    │  │
│  └───────────────────────┘ └───────────────────────┘  │
└──────────────────────┬────────────────────────────────┘
                       │  HTTP POST (JSON / Multipart Form)
                       ▼
┌───────────────────────────────────────────────────────┐
│          FastAPI Backend  (http://localhost:8000)      │
│  POST /api/v1/cv/analyze                              │
│  POST /api/v1/interview/start                         │
│  POST /api/v1/interview/respond                       │
└──────────────────────┬────────────────────────────────┘
                       │  HTTP POST (JSON)
                       ▼
┌───────────────────────────────────────────────────────┐
│          Ollama LLM Sunucusu (localhost:11434)        │
│          Model: llama3 (varsayılan)                   │
└───────────────────────────────────────────────────────┘
```

- **Frontend:** Python + Gradio (`gr.Blocks`) — `frontend/app.py`
- **Backend:** Python + FastAPI — `http://localhost:8000/api/v1`
- **LLM:** Ollama üzerinden çalışan yerel LLM (varsayılan: `llama3`)
- **İletişim:** Frontend → Backend arası `requests` veya `httpx` ile HTTP istekleri

---

## 📁 2. Proje Dosya Yapısı

```
AI-CareerCoach/
├── app/
│   ├── main.py                          # FastAPI uygulama giriş noktası
│   ├── api/
│   │   ├── router.py                    # /cv ve /interview route tanımları
│   │   └── endpoints/
│   │       ├── cv.py                    # POST /cv/analyze endpoint'i
│   │       └── interview.py            # POST /interview/start & /respond
│   ├── core/
│   │   └── config.py                   # Ortam değişkenleri (Ollama URL, model adı vb.)
│   └── services/
│       ├── pdf_parser.py               # pypdf ile PDF'den metin çıkarma
│       ├── cv_analiz.py                # ATS puan hesaplama ve score breakdown
│       ├── cache.py                    # Mülakat oturum yönetimi (in-memory)
│       └── llm/
│           ├── __init__.py
│           ├── client.py               # Ollama API istemcisi (httpx, async)
│           └── prompts.py              # Tüm sistem/kullanıcı prompt şablonları
├── frontend/
│   ├── README.md                       # ← Bu dosya
│   └── app.py                          # ← Gradio arayüzü (oluşturulacak)
├── .env                                # Ortam değişkenleri (gizli, git'e eklenmez)
├── .env.example                        # .env şablonu
├── requirements.txt                    # Backend Python bağımlılıkları
├── Dockerfile
└── docker-compose.yml
```

---

## ⚙️ 3. Ortam Değişkenleri (.env)

Backend'in çalışması için `.env` dosyasında şu değişkenler tanımlıdır:

| Değişken           | Varsayılan                    | Açıklama                                   |
|--------------------|-------------------------------|---------------------------------------------|
| `OLLAMA_BASE_URL`  | `http://localhost:11434`      | Ollama LLM sunucu adresi                    |
| `LLM_MODEL`        | `llama3`                      | Kullanılacak model adı                      |
| `LLM_TIMEOUT`      | `60.0`                        | LLM isteği zaman aşımı (saniye)             |
| `REDIS_URL`        | `redis://localhost:6379`      | (Opsiyonel) Redis adresi — şu an in-memory  |

---

## 🔌 4. Backend API Detayları (API Contract)

### 📄 A. CV Analiz Endpoint'i

- **URL:** `POST http://localhost:8000/api/v1/cv/analyze`
- **İçerik Tipi:** `multipart/form-data`

#### İstek Parametreleri (Form Data)

| Alan              | Tip         | Zorunlu | Açıklama                                   |
|-------------------|-------------|---------|---------------------------------------------|
| `file`            | PDF Dosyası | ✅ Evet | Yüklenecek CV dosyası (sadece PDF kabul edilir) |
| `job_position`    | string      | ❌ Hayır | Hedef pozisyon adı (örn: `"Backend Developer"`) |
| `job_description` | string      | ❌ Hayır | İş ilanı metni (pozisyona özel analiz için)  |

#### Başarılı Yanıt (200 OK — JSON)

```json
{
  "filename": "ornek_cv.pdf",
  "file_type": "application/pdf",
  "character_count": 1420,
  "extracted_text": "CV metin içeriği...",
  "job_position": "Backend Developer",
  "parsed_skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
  "suggested_improvements": [
    "Deneyim bölümünüze '...% artış' gibi somut bir rakam ekleyin.",
    "ATS eşleşmesi için iş ilanındaki 'CI/CD' terimini CV'nize ekleyin.",
    "'Sorumluydum' ifadesini 'geliştirdim', 'optimize ettim' gibi güçlü fiillerle değiştirin.",
    "Beceriler bölümünü Deneyim bölümünden sonraya taşıyın."
  ],
  "ats_score": 78,
  "final_score": 78,
  "score_breakdown": {
    "skill_score": 32,
    "keyword_score": 24,
    "formatting_score": 22
  },
  "score_summary": {
    "skill_count": 4,
    "llm_score": 78
  }
}
```

#### Yanıt Alanlarının Açıklaması

| Alan                     | Tip              | Açıklama                                                                 |
|--------------------------|------------------|---------------------------------------------------------------------------|
| `filename`               | `string`         | Yüklenen dosya adı                                                        |
| `file_type`              | `string`         | Dosya MIME tipi (her zaman `"application/pdf"`)                            |
| `character_count`        | `int`            | Çıkarılan metin karakter sayısı                                           |
| `extracted_text`         | `string`         | PDF'den çıkarılan ham metin                                               |
| `job_position`           | `string \| null` | Belirtildiyse hedef pozisyon adı, yoksa `null`                            |
| `parsed_skills`          | `string[]`       | LLM tarafından tespit edilen beceriler listesi                            |
| `suggested_improvements` | `string[]`       | 4-5 maddelik, eyleme geçirilebilir iyileştirme önerileri                  |
| `ats_score`              | `int`            | LLM'nin verdiği ATS uyumluluk puanı (0-100)                              |
| `final_score`            | `int`            | Normalize edilmiş nihai puan (0-100)                                      |
| `score_breakdown`        | `object`         | Puan kırılımı (aşağıya bakın)                                            |
| `score_summary`          | `object`         | Özet istatistikler (aşağıya bakın)                                       |

**`score_breakdown` detayı:**

| Alt Alan              | Max Puan | Açıklama                                            |
|-----------------------|----------|------------------------------------------------------|
| `skill_score`         | 40       | Teknik yetkinlik + deneyim uyumu puanı               |
| `keyword_score`       | 30       | Anahtar kelime eşleşmesi + nicel başarılar puanı     |
| `formatting_score`    | 30       | Okunabilirlik ve biçimlendirme puanı                 |

> **Not:** `skill_score + keyword_score + formatting_score = final_score` (toplam her zaman `final_score`'a eşittir).

**`score_summary` detayı:**

| Alt Alan       | Açıklama                                 |
|----------------|-------------------------------------------|
| `skill_count`  | Tespit edilen beceri sayısı               |
| `llm_score`    | LLM'nin verdiği ham ATS puanı (0-100)     |

#### Hata Yanıtları

| Durum Kodu | Durum                  | Örnek Yanıt                                                                      |
|------------|------------------------|-----------------------------------------------------------------------------------|
| `400`      | Geçersiz dosya türü    | `{"detail": "Geçersiz dosya türü. Şu anda yalnızca PDF dosyaları desteklenmektedir."}` |
| `400`      | Metin çıkarılamadı     | `{"detail": "PDF dosyasından metin çıkarılamadı. Lütfen taranmış resim PDF'si olmadığından emin olun."}` |
| `500`      | PDF parse hatası       | `{"detail": "PDF ayrıştırılırken bir hata oluştu: ..."}`                           |

---

### 🎙️ B. Mülakat Simülatörü Endpoint'leri

#### B1. Mülakat Başlatma

- **URL:** `POST http://localhost:8000/api/v1/interview/start`
- **İçerik Tipi:** `application/json`

**İstek Gövdesi:**

```json
{
  "role": "Python Backend Developer",
  "experience_level": "Mid",
  "focus_areas": ["FastAPI", "SQL", "Sistem Tasarımı"]
}
```

| Alan               | Tip        | Zorunlu | Açıklama                                              |
|--------------------|------------|---------|--------------------------------------------------------|
| `role`             | `string`   | ✅ Evet | Hedef pozisyon / rol adı                               |
| `experience_level` | `string`   | ✅ Evet | Deneyim seviyesi: `"Junior"`, `"Mid"` veya `"Senior"` |
| `focus_areas`      | `string[]` | ❌ Hayır | Odaklanılacak teknik alanlar listesi                   |

**Başarılı Yanıt (200 OK — JSON):**

```json
{
  "session_id": "a8f3b21c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "role": "Python Backend Developer",
  "first_question": "Python'da GIL (Global Interpreter Lock) mekanizmasını ve asenkron programlamaya etkisini açıklayabilir misiniz?"
}
```

| Alan             | Tip      | Açıklama                                          |
|------------------|----------|---------------------------------------------------|
| `session_id`     | `string` | UUID formatında benzersiz oturum kimliği           |
| `role`           | `string` | Seçilen rol adı                                   |
| `first_question` | `string` | LLM tarafından üretilen ilk mülakat sorusu        |

> **⚠️ Önemli:** `session_id` değerini `gr.State` içinde saklayın. Sonraki cevap gönderme isteklerinde bu değer gereklidir.

---

#### B2. Cevap Gönderme ve Geri Bildirim Alma

- **URL:** `POST http://localhost:8000/api/v1/interview/respond`
- **İçerik Tipi:** `application/json`

**İstek Gövdesi:**

```json
{
  "session_id": "a8f3b21c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "question": "Python'da GIL mekanizmasını açıklayabilir misiniz?",
  "answer": "GIL, CPython'da aynı anda sadece tek bir thread'in Python bytecode çalıştırmasını sağlayan bir kilittir..."
}
```

| Alan         | Tip      | Zorunlu | Açıklama                             |
|--------------|----------|---------|---------------------------------------|
| `session_id` | `string` | ✅ Evet | Mülakat başlatma yanıtından alınan ID |
| `question`   | `string` | ✅ Evet | Sorulan mülakat sorusu                |
| `answer`     | `string` | ✅ Evet | Kullanıcının verdiği cevap            |

**Başarılı Yanıt (200 OK — JSON):**

```json
{
  "feedback": "### 🟢 Doğrular\n- GIL kavramını ve CPython ilişkisini doğru tanımladınız.\n\n### 🔴 Eksikler\n- Multiprocessing ve asyncio alternatiflerine değinmediniz.\n\n### 💡 Öneriler\n- I/O bound vs CPU bound senaryolarını ayırt ederek örneklendirin.",
  "score": 8,
  "next_question": "FastAPI uygulamasında veritabanı bağlantı havuzunu nasıl yönetirsiniz?"
}
```

| Alan            | Tip             | Açıklama                                                     |
|-----------------|-----------------|---------------------------------------------------------------|
| `feedback`      | `string`        | Markdown formatlı geri bildirim (aşağıdaki formata bakın)     |
| `score`         | `int`           | 1-10 arası puan (10 = mükemmel)                              |
| `next_question` | `string \| null`| Bir sonraki soru (mülakatın sonu ise `null` olabilir)         |

**`feedback` alanı Markdown formatı** (Gradio `gr.Markdown` ile doğrudan render edilebilir):

```markdown
### 🟢 Doğrular
- Doğru olan nokta 1
- Doğru olan nokta 2

### 🔴 Eksikler
- Eksik nokta 1
- Eksik nokta 2

### 💡 Öneriler
- Öneri 1
- Öneri 2
```

**Hata Yanıtları:**

| Durum Kodu | Durum                        | Örnek Yanıt                                                                  |
|------------|------------------------------|-------------------------------------------------------------------------------|
| `400`      | Geçersiz session_id          | `{"detail": "Geçersiz oturum kimliği"}`                                      |
| `404`      | Oturum bulunamadı            | `{"detail": "Oturum bulunamadı: '...'. Lütfen önce /start endpoint'ini çağırın."}` |

---

## 🤖 5. Yapay Zeka ile Arayüz Yazma Rehberi (AI Prompt Şablonu)

Aşağıdaki prompt'u herhangi bir AI modeline (Claude, ChatGPT, Copilot, Cursor vb.) vererek Gradio arayüzünü yazdırabilirsiniz:

````text
Sanal bir Python ve Gradio uzmanı olarak hareket et.
"AI Kariyer Koçu" projesi için `frontend/app.py` adında modern ve şık bir Gradio arayüzü yaz.

## Teknik Gereksinimler
1. Gradio `gr.Blocks(theme=gr.themes.Soft())` ve sekmeli (`gr.Tab`) yapı kullan.
2. Backend adresi: `http://localhost:8000/api/v1`. İstekler için `requests` kullan.
3. Tüm hata durumlarını try-except ile ele al ve kullanıcıya uygun mesaj göster.

## Arayüz — 2 Ana Sekme

### Sekme 1: 📄 CV Analizör
Backend: `POST /api/v1/cv/analyze` (multipart/form-data)

**Sol Kolon (Girdiler):**
- PDF yükleme: `gr.File(file_types=['.pdf'])`
- Hedef Pozisyon: `gr.Textbox` (opsiyonel)
- İş İlanı Metni: `gr.Textbox(lines=5)` (opsiyonel)
- "🔍 CV'yi Analiz Et" Butonu (`variant="primary"`)

**Sağ Kolon (Sonuçlar):**
- Puan Kartları: ATS Puanı ve Final Puanı — büyük ve dikkat çekici `gr.Markdown` göstergeler
- Puan Kırılımı: `skill_score` (max 40), `keyword_score` (max 30), `formatting_score` (max 30) — progress bar veya renkli Markdown ile göster
- Tespit Edilen Beceriler: `parsed_skills` listesini badge/etiket olarak göster
- İyileştirme Önerileri: `suggested_improvements` listesini madde işaretli `gr.Markdown` olarak göster
- Çıkarılan CV Metni: `gr.Accordion(open=False)` içinde `gr.TextArea(interactive=False)`

API Yanıt Şeması:
```json
{
  "filename": "str", "file_type": "str", "character_count": "int",
  "extracted_text": "str", "job_position": "str|null",
  "parsed_skills": ["str"], "suggested_improvements": ["str"],
  "ats_score": "int (0-100)", "final_score": "int (0-100)",
  "score_breakdown": {"skill_score": "int (max 40)", "keyword_score": "int (max 30)", "formatting_score": "int (max 30)"},
  "score_summary": {"skill_count": "int", "llm_score": "int"}
}
```

### Sekme 2: 🎙️ AI Mülakat Simülatörü
Backend: `POST /api/v1/interview/start` ve `POST /api/v1/interview/respond` (JSON)

**Üst Bölüm (Oturum Başlatma):**
- Rol: `gr.Textbox` (örn: "Python Developer")
- Deneyim Seviyesi: `gr.Dropdown(choices=["Junior", "Mid", "Senior"])`
- Odak Alanları: `gr.Textbox` (virgülle ayrılmış, opsiyonel)
- "🚀 Mülakatı Başlat" Butonu

**Alt Bölüm (Soru-Cevap Döngüsü):**
- `gr.State` içinde `session_id` sakla (backend'den UUID döner)
- Mevcut Soru: `gr.Markdown` kartı
- Kullanıcı Cevabı: `gr.Textbox(lines=4)`
- "📤 Cevabı Gönder" Butonu
- Geri Bildirim: `gr.Markdown` (feedback alanı zaten Markdown formatında gelir, doğrudan render et)
- Puan: 1-10 arası gösterge
- Sıradaki Soru: otomatik olarak soru kartını güncelle

Start API Yanıtı: `{"session_id": "uuid", "role": "str", "first_question": "str"}`
Respond API Yanıtı: `{"feedback": "markdown str", "score": "int 1-10", "next_question": "str|null"}`

## Önemli Notlar
- PDF dışı dosya yüklenirse backend 400 hatası döner.
- `score_breakdown` toplamı her zaman `final_score`'a eşittir.
- `feedback` alanı 3 bölümlü Markdown'dır: 🟢 Doğrular, 🔴 Eksikler, 💡 Öneriler.
- Tüm metinler Türkçe olmalı.

Kodun tamamını eksiksiz, temiz, Türkçe yorum satırları içeren tek bir `app.py` dosyası olarak üret.
````

---

## 🛠️ 6. Örnek Çalışan Kod Yapısı (`frontend/app.py`)

Aşağıda frontend klasörüne koyabileceğiniz, hazır ve çalışan temel Gradio uygulaması yer almaktadır:

```python
import gradio as gr
import requests

API_BASE_URL = "http://localhost:8000/api/v1"

# ---------------------------------------------------------------------------
# CV Analiz Fonksiyonu
# ---------------------------------------------------------------------------
def cv_analiz_et(pdf_file, job_position, job_description):
    """PDF dosyasını backend'e gönderir, ATS analiz sonuçlarını döndürür."""
    if not pdf_file:
        return "⚠️ Lütfen bir PDF dosyası yükleyin.", "", "", "", None

    try:
        with open(pdf_file.name, "rb") as f:
            files = {"file": (pdf_file.name, f, "application/pdf")}
            data = {}
            if job_position:
                data["job_position"] = job_position
            if job_description:
                data["job_description"] = job_description

            response = requests.post(
                f"{API_BASE_URL}/cv/analyze", files=files, data=data, timeout=90
            )

        if response.status_code != 200:
            error_detail = response.json().get("detail", response.text)
            return f"❌ Hata: {error_detail}", "", "", "", None

        res = response.json()

        # Puan kartları
        ats = res.get("ats_score", 0)
        final = res.get("final_score", 0)
        breakdown = res.get("score_breakdown", {})
        score_md = (
            f"## 🎯 ATS Puanı: **{ats}/100** | Final Puanı: **{final}/100**\n\n"
            f"| Kriter | Puan |\n|--------|------|\n"
            f"| 🧠 Teknik Yetkinlik | **{breakdown.get('skill_score', 0)}/40** |\n"
            f"| 🔑 Anahtar Kelimeler | **{breakdown.get('keyword_score', 0)}/30** |\n"
            f"| 📐 Biçimlendirme | **{breakdown.get('formatting_score', 0)}/30** |"
        )

        # Beceriler
        skills = res.get("parsed_skills", [])
        skills_md = "### 🛠️ Tespit Edilen Beceriler\n" + " • ".join(skills) if skills else ""

        # Öneriler
        improvements = res.get("suggested_improvements", [])
        improvements_md = "### 💡 İyileştirme Önerileri\n" + "\n".join(
            [f"- {imp}" for imp in improvements]
        )

        # Çıkarılan metin
        extracted = res.get("extracted_text", "")

        return score_md, skills_md, improvements_md, extracted, ats

    except requests.exceptions.ConnectionError:
        return "❌ Backend'e bağlanılamadı. Sunucunun çalıştığından emin olun.", "", "", "", None
    except Exception as e:
        return f"❌ Beklenmeyen hata: {str(e)}", "", "", "", None


# ---------------------------------------------------------------------------
# Mülakat Fonksiyonları
# ---------------------------------------------------------------------------
def mulakat_baslat(role, experience_level, focus_areas_str):
    """Yeni bir mülakat oturumu başlatır, ilk soruyu alır."""
    if not role:
        return "", "⚠️ Lütfen bir rol girin.", ""

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
            return (
                data["session_id"],
                f"### ❓ Soru:\n{data['first_question']}",
                "",
            )
        error_detail = res.json().get("detail", res.text)
        return "", f"❌ Hata: {error_detail}", ""
    except requests.exceptions.ConnectionError:
        return "", "❌ Backend'e bağlanılamadı.", ""
    except Exception as e:
        return "", f"❌ Hata: {str(e)}", ""


def yanit_gonder(session_id, current_question, user_answer):
    """Kullanıcının cevabını gönderir, geri bildirim ve sonraki soruyu alır."""
    if not session_id:
        return "⚠️ Lütfen önce mülakatı başlatın.", current_question, user_answer
    if not user_answer or not user_answer.strip():
        return "⚠️ Lütfen cevabınızı yazın.", current_question, user_answer

    # Soru metninden Markdown başlığını temizle
    clean_question = current_question.replace("### ❓ Soru:\n", "").strip()

    payload = {
        "session_id": session_id,
        "question": clean_question,
        "answer": user_answer,
    }

    try:
        res = requests.post(f"{API_BASE_URL}/interview/respond", json=payload, timeout=90)
        if res.status_code == 200:
            data = res.json()
            score = data.get("score", 0)
            feedback = data.get("feedback", "")
            feedback_md = f"## 📊 Puan: {score}/10\n\n{feedback}"

            next_q = data.get("next_question")
            next_q_md = f"### ❓ Soru:\n{next_q}" if next_q else "✅ Mülakat tamamlandı!"

            return feedback_md, next_q_md, ""  # Cevap kutusunu temizle

        error_detail = res.json().get("detail", res.text)
        return f"❌ Hata: {error_detail}", current_question, user_answer
    except requests.exceptions.ConnectionError:
        return "❌ Backend'e bağlanılamadı.", current_question, user_answer
    except Exception as e:
        return f"❌ Hata: {str(e)}", current_question, user_answer


# ---------------------------------------------------------------------------
# Gradio Arayüz Tasarımı
# ---------------------------------------------------------------------------
with gr.Blocks(theme=gr.themes.Soft(), title="AI Kariyer Koçu") as demo:
    gr.Markdown("# 🚀 AI Kariyer Koçu & Mülakat Simülatörü")

    with gr.Tabs():
        # ── Sekme 1: CV Analizi ──────────────────────────────────────────
        with gr.Tab("📄 CV Analizör"):
            with gr.Row():
                with gr.Column(scale=1):
                    file_input = gr.File(label="CV Yükle (PDF)", file_types=[".pdf"])
                    pos_input = gr.Textbox(
                        label="Hedef Pozisyon (Opsiyonel)",
                        placeholder="Örn: Backend Developer",
                    )
                    desc_input = gr.Textbox(
                        label="İş İlanı Metni (Opsiyonel)",
                        lines=4,
                        placeholder="İş ilanının metnini buraya yapıştırın...",
                    )
                    analyze_btn = gr.Button("🔍 CV'yi Analiz Et", variant="primary")

                with gr.Column(scale=1):
                    score_output = gr.Markdown()
                    skills_output = gr.Markdown()
                    improvements_output = gr.Markdown()
                    with gr.Accordion("📝 Çıkarılan CV Metni", open=False):
                        text_output = gr.TextArea(lines=10, interactive=False)

            analyze_btn.click(
                fn=cv_analiz_et,
                inputs=[file_input, pos_input, desc_input],
                outputs=[score_output, skills_output, improvements_output, text_output],
            )

        # ── Sekme 2: Mülakat Simülatörü ─────────────────────────────────
        with gr.Tab("🎙️ AI Mülakat Simülatörü"):
            session_state = gr.State("")

            with gr.Row():
                role_in = gr.Textbox(label="Hedef Rol", value="Python Developer")
                level_in = gr.Dropdown(
                    label="Deneyim Seviyesi",
                    choices=["Junior", "Mid", "Senior"],
                    value="Mid",
                )
                focus_in = gr.Textbox(
                    label="İlgi Alanları (virgülle ayırın)",
                    value="FastAPI, SQL",
                    placeholder="Örn: FastAPI, Docker, Veritabanı",
                )
            start_btn = gr.Button("🚀 Mülakatı Başlat", variant="primary")

            question_box = gr.Markdown()
            answer_in = gr.Textbox(
                label="Cevabınız",
                lines=4,
                placeholder="Cevabınızı detaylıca yazın...",
            )
            submit_btn = gr.Button("📤 Cevabı Gönder", variant="secondary")
            feedback_box = gr.Markdown()

            start_btn.click(
                fn=mulakat_baslat,
                inputs=[role_in, level_in, focus_in],
                outputs=[session_state, question_box, feedback_box],
            )

            submit_btn.click(
                fn=yanit_gonder,
                inputs=[session_state, question_box, answer_in],
                outputs=[feedback_box, question_box, answer_in],
            )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

---

## 🚀 7. Kurulum ve Çalıştırma

### Ön Koşullar
1. **Ollama** kurulu ve `llama3` modeli çekilmiş olmalı:
   ```bash
   ollama pull llama3
   ```
2. Backend bağımlılıkları yüklü olmalı:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Bağımlılıkları
```bash
pip install gradio requests
```

### Uygulamayı Çalıştırma
```bash
# 1. Ollama sunucusunu başlat (ayrı terminalde)
ollama serve

# 2. Backend'i başlat (proje kök dizininde)
uvicorn app.main:app --reload --port 8000

# 3. Gradio Frontend'i başlat (proje kök dizininde)
python frontend/app.py
```

Tarayıcınızda `http://localhost:7860` adresine giderek arayüzü kullanabilirsiniz.

### Docker ile Çalıştırma (Sadece Backend)
```bash
docker-compose up --build
```
> Not: Docker Compose şu an yalnızca backend'i (`uvicorn`) ayağa kaldırır. Gradio frontend'ini ayrıca çalıştırmanız gerekir.

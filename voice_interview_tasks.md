# 🎙️ Sesli Mülakat Simülatörü Görev Dağılımı (Süreç/Aşama Bazlı Full-Stack Ayrım)

Bu doküman, gerçeğe yakın bir mülakat stresi simüle etmek (süreli, metin düzeltmesi olmayan ve davranışsal analiz içeren) amacıyla **2 kişilik** bir ekibin çalışabilmesi için optimize edilmiştir.

Bu modelde "Frontend vs Backend" ayrımı yoktur. Her iki geliştirici de kendi sorumluluk alanındaki özelliğin (feature) hem arayüzünü (Gradio) hem de arka planını (FastAPI) baştan sona (uçtan uca) geliştirir.

---

## 🔁 1. Kişi: Mülakat Soru-Cevap Döngüsü (Core Interview Loop)
**Odak Noktası:** Uygulamanın en temel işlevi olan "Soru Sor -> Sesi Kaydet -> Yazıya Çevir -> Yeni Soru Üret" akışının kesintisiz ve hatasız çalışmasını sağlamaktır.

### Görevler (Full-Stack):
- [ ] **Mikrofon & Chat Arayüzü (Frontend):** Gradio üzerinde mülakat chat ekranını (`gr.Chatbot`) kurmak. Sistemin mikrofonu açıp kullanıcının sesini (`gr.Audio`) kaydetmesini ve "Sonraki Soruya Geç" butonuna basıldığında kaydın Backend'e gitmesini sağlamak.
- [ ] **STT (Sesten Metne) Entegrasyonu (Backend):** Backend tarafında `/stt/transcribe` endpoint'ini hazırlayıp Whisper modelini entegre etmek.
- [ ] **Doldurucu Sesleri Korumak (Kritik):** Whisper'ı "eee", "ııı" gibi sesleri ve kekelemeleri *silmeyecek* şekilde ayarlamak (böylece 2. kişinin yapacağı final analizi başarılı olabilir).
- [ ] **Döngü Mantığı:** Sesi metne çevirdikten sonra, bu kusurlu metni hemen Ollama'ya (`llama3`) gönderip sıradaki mülakat sorusunu almak ve bu soruyu Frontend'de chat balonuna yazdırmak.

---

## ⏱️ 2. Kişi: Zaman Yönetimi ve Davranışsal Final Raporu
**Odak Noktası:** Mülakatın kurallarını (90 saniye sınırı, soru limiti) belirlemek ve mülakat bittiğinde adayın psikolojik/teknik durumunu analiz eden devasa bir karne üretmek.

### Görevler (Full-Stack):
- [ ] **Zaman Yönetimi (Frontend):** Arayüze 90 saniyeden geriye sayan dinamik bir sayaç eklemek. Süre dolduğunda (kullanıcı butona basmasa bile) mikrofonu *otomatik olarak* durdurup sesi 1. kişinin yazdığı sisteme zorla (force submit) göndermek.
- [ ] **Bitiş Kriteri (Backend):** Mülakat soru sayısını (örn: 5 soru) saymak ve limit dolduğunda mülakatı "Bitti" durumuna geçirmek.
- [ ] **Davranışsal LLM Değerlendirmesi (Backend):** Mülakat bitince, kaydedilen tüm kusurlu metinleri (doldurucu kelimelerle birlikte) Ollama'ya göndermek. Özel bir prompt ile;
    - Heyecan Seviyesi (kekeleme ve "ııı" sayısına göre)
    - Diksiyon / Telaffuz
    - Teknik Doğruluk
    analizlerini içeren kapsamlı bir JSON raporu çıkartmak.
- [ ] **Final Karnesi (Frontend) & Veritabanı (Backend):** Hazırlanan raporu Gradio arayüzünde şık bir karne olarak kullanıcıya sunmak. Ayrıca `app/database/models.py` içindeki `CVAnalizRecord` tablosuna gerekli kolonları ekleyerek bu muazzam analizi veritabanına kaydetmek.

---

## 🚀 Uçtan Uca Ortak İş Akışı (Senaryo)
1. **[1. Kişi]** LLM'den ilk soruyu çeker, ekranda gösterir ve mikrofonu açar.
2. **[2. Kişi]** Soru ekrana geldiği an 90 saniyelik geriye sayımı başlatır.
3. **[Kullanıcı]** Cevap verir. Süre işler.
4. **[Tetikleyici]** Kullanıcı manuel olarak geçer (1. Kişi) veya 90 sn dolar (2. Kişi). Mikrofon kapanır.
5. **[1. Kişi]** Ses dosyasını Whisper ile metne çevirir (ııı, eee dahil) ve LLM'den yeni soruyu getirir.
6. **[Sistem]** Bu döngü 5 kez tekrar eder.
7. **[2. Kişi]** 5. soru bittiğinde döngüyü keser. Tüm konuşmaları toplayıp davranışsal analiz yapar, veritabanına kaydeder ve ekrana Rapor Karnesi çıkarır.

# 🎙️ Sesli Mülakat Simülatörü Görev Dağılımı (2 Kişilik Ekip)

Bu doküman, gerçeğe yakın bir mülakat stresi simüle etmek (süreli, metin düzeltmesi olmayan ve davranışsal analiz içeren) amacıyla **2 kişilik** bir ekibin çalışabilmesi için optimize edilmiştir.

Görevleri temel olarak **İstemci (Frontend/UX)** ve **Yapay Zeka (Backend/LLM)** olmak üzere iki net role böldüm:

---

## 👨‍💻 1. Kişi: Frontend & Kullanıcı Deneyimi (UX) Geliştiricisi
**Odak Noktası:** Mülakat arayüzü, zamanlayıcı (Timer) mantığı, ses kaydının otomatik yönetilmesi ve arka plan servisleriyle iletişim.

### Görevler:
- [ ] **Zamanlayıcı (Timer) UI:** Ekrana kullanıcının süresini (örn: 90 saniye) gösteren ve geriye sayan dinamik bir sayaç (timer) eklemek.
- [ ] **Otomatik Kayıt (Auto-Record):** Ekrana LLM'den yeni bir soru geldiği anda mikrofon kaydını *otomatik olarak* başlatmak ve sayacı tetiklemek.
- [ ] **Sürenin Dolması (Auto-Stop):** Süre dolduğunda mikrofon kaydını otomatik durdurup arka plana (Backend) göndermek.
- [ ] **"Sonraki Soruya Geç" Butonu:** Kullanıcı süreyi sonuna kadar kullanmak istemezse, kaydı manuel olarak durdurup hemen backend'e göndermesini sağlayacak bir buton eklemek.
- [ ] **Salt Okunur (Read-only) UI:** Kullanıcının metni *düzenleyememesi* için, STT'den dönen metni doğrudan Chatbot balonunda veya sadece okunabilir bir alanda göstermek.

---

## ⚙️ 2. Kişi: Backend Yapay Zeka (STT & LLM) Mühendisi
**Odak Noktası:** Sesi metne çevirirken kusurları korumak, mülakat döngüsünü yönetmek ve finalde devasa bir davranışsal rapor sunmak.

### Görevler (STT / Sesten Metne):
- [ ] **Doldurucu Sesleri (Filler Words) Koruma:** Sesi metne çevirecek `/stt/transcribe` endpoint'ini yazmak. Whisper'ın prompt veya parametre ayarlarını değiştirerek "eee", "ııı" gibi seslerin ve tekrarların (kekeleme) metne *olduğu gibi* yansımasını sağlamak.
- [ ] **Telaffuz/Hız Verisi Çıkarmak:** Mümkünse konuşma hızı veya duraksama süresi gibi ek metrikleri Whisper'ın word-level timestamp özelliklerinden çıkarmak.

### Görevler (LLM / Mülakat Akışı):
- [ ] **Durum (State) Yönetimi:** Mülakatın soru sayısını (örn: 5 soru) Backend'de takip etmek ve 5. sorunun cevabı geldiğinde mülakatı bitirme moduna sokmak.
- [ ] **Davranışsal ve Teknik Prompt Mühendisliği (Final Rapor):** Mülakat bittiğinde LLM'e (Ollama) gidecek çok kapsamlı bir değerlendirme promptu hazırlamak. Bu prompt:
    - *Teknik Değerlendirme:* Adayın verdiği cevapların doğruluğunu ve teknik eksiklerini bulmalı.
    - *Davranışsal Analiz:* Adayın cümlelerindeki "eee, ııı" kullanımına, tekrarlanan kelimelere (kekeleme) bakarak heyecan seviyesini analiz etmeli.
- [ ] **Rapor Endpoint'i:** Tüm bu analizi JSON olarak Frontend'e dönen `/api/v1/interview/finish` adında bir uç hazırlamak. 

> [!IMPORTANT]
> **Kritik İpucu:** Backend Geliştiricisi, STT kısmını tasarlarken sesi kusursuzlaştırmaktan **kaçınmalıdır**. Eğer STT "Ben ııı şey yaptım" cümlesini "Ben onu yaptım" diye temizlerse, LLM (davranışsal analiz) kullanıcının heyecanlandığını veya takıldığını asla bilemez.

---

## 🚀 Yeni İş Akışı (Gerçek Zamanlı Süreli Mülakat)
1. **[Backend]** İlk soruyu üretir ve Frontend'e yollar.
2. **[Frontend]** Soruyu ekranda gösterir, sayacı (Örn: 90sn) başlatır ve **mikrofonu anında otomatik açar.**
3. **[Kullanıcı]** Soruya cevap verir. Süre işler.
4. **[Tetikleyici]** Kullanıcı "Sonraki Soruya Geç" butonuna basar YADA 90 saniye dolar. Mikrofon kapanır.
5. **[Frontend -> Backend]** Kaydedilen ses Backend'e gider.
6. **[Backend]** Sesi Whisper ile (ııı, eee dahil) metne döker. Bu kusurlu metni LLM'e yollar.
7. **[Backend -> Frontend]** LLM sıradaki soruyu üretir ve süreç (2. adımdan itibaren) tekrar eder.
8. **[Backend]** Tüm sorular bitince, sistem tüm konuşma kayıtlarını analiz eder ve Teknik Doğruluk, Heyecan Seviyesi, Diksiyon ve Telaffuz içeren bir final karnesi sunar.

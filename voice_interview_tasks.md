# 🎙️ Sesli Mülakat Simülatörü Görev Dağılımı (Güncellenmiş)

Belirttiğin UX (Kullanıcı Deneyimi) senaryosu çok mantıklı! Sesi doğrudan arkaya yollamak yerine **kullanıcıya metni düzenleme imkanı (edit before send)** sunmak hem LLM'in daha iyi anlamasını sağlar hem de STT (Sesten Metne) hatalarının önüne geçer.

Bu senaryoda soruların "seslendirilmesine" (TTS) şu an acil bir ihtiyaç yok gibi görünüyor. Bunun yerine 3. kişinin görevini mülakatın **"Bitiş ve Final Değerlendirmesi"** kısmına kaydırdım.

---

## 👨‍💻 1. Kişi: Frontend & UI (Gradio) Geliştiricisi
**Odak Noktası:** Mikrofon arayüzü, sesten metne dönüşüm sırasında arayüzün güncellenmesi ve Chat (Mesaj Balonları) görünümü.

### Görevler:
- [ ] **Mikrofon Bileşeni:** Mevcut `gr.Textbox`'ın yanına veya üstüne `gr.Audio(sources=["microphone"], type="filepath")` bileşenini eklemek.
- [ ] **Ses Bittiğinde (Stop Recording) Tetikleme:** Kullanıcı kaydı bitirdiğinde (`audio.stop_recording` eventi ile), ses dosyasını Backend'deki STT (Whisper) endpoint'ine göndermek.
- [ ] **Metin Kutusunu Doldurma:** Backend'den dönen "metin" (transcription) yanıtını alıp, kullanıcının düzenleyebilmesi için direkt olarak mevcut `gr.Textbox` (answer_in) içine yazdırmak.
- [ ] **Sohbet Balonları (Chatbot UI):** Şu anki soru-cevap akışını daha şık bir `gr.Chatbot` bileşenine çevirerek "Gönder" butonuna basıldığında mesajların balon şeklinde alt alta eklenmesini sağlamak.

---

## ⚙️ 2. Kişi: Backend STT (Speech-to-Text) Mühendisi
**Odak Noktası:** Sesi alıp en hızlı ve doğru şekilde metne çeviren API ucunu yazmak.

### Görevler:
- [ ] **Yeni Bir Endpoint Oluşturmak:** Backend'de sadece STT işini yapacak bağımsız bir endpoint (`/api/v1/stt/transcribe`) yazmak. Bu uç sadece bir ses dosyası alıp geriye `{"text": "kullanıcının söylediği cümle"}` dönecek.
- [ ] **Whisper Entegrasyonu:** Projeye `faster-whisper` (önerilen) veya OpenAI'nin temel `whisper` modelini kurmak.
- [ ] **Dosya Formatı Yönetimi:** Gradio'dan gelen ses dosyasını (`.wav` vb.) geçici olarak kaydedip Whisper modeline beslemek ve ardından geçici dosyayı silmek.

> [!TIP]
> Frontend geliştiricisi mikrofonu kapattığı an bu API'ye istek atacak. Bu sayede LLM ile hiç uğraşılmadan sadece "Sesi Metne Çevirme" işi yapılmış olacak.

---

## 🤖 3. Kişi: Backend Mülakat Akışı & Değerlendirme Mühendisi
**Odak Noktası:** Mülakatın ilerleyişini, ne zaman biteceğini ve en son sunulacak final değerlendirme raporunu hazırlamak.

### Görevler:
- [ ] **Soru Sayısı / Bitiş Kriteri:** Mülakatın sonsuza kadar sürmemesi için bir limit (örn: 5 soru) belirlemek. `interview.py` içindeki mantığı güncelleyerek 5. sorudan sonra "Mülakat Bitti" durumuna (state) geçmesini sağlamak.
- [ ] **Final Değerlendirmesi Promptu:** Mülakat bittiğinde, o ana kadar sorulan tüm soruları ve kullanıcının verdiği cevapları toplayarak LLM'e (Ollama) özel bir "Final Değerlendirme" promptu göndermek (Örn: *Bu adayın genel performansı nasıldı? Hangi konularda eksikti? İşe alınır mı?*).
- [ ] **Değerlendirme Endpoint'i:** Bitiş durumunda çalışacak `/api/v1/interview/finish` adında bir uç yazıp, bu detaylı raporu JSON olarak Frontend'e dönmek.

> [!NOTE]
> Bu kişi mevcut `interview.py` üzerinde çalışacak. Sistemin soru-cevap döngüsünü yönetecek ve mülakatı başarılı bir raporla sonlandırmaktan sorumlu olacak.

---

## 🚀 Beklenen İş Akışı (Senin Senaryona Göre)
1. **[Backend]** LLM pozisyona göre ilk soruyu üretir ve Frontend'e yollar.
2. **[Frontend]** İlk soru chat balonunda belirir.
3. **[Kullanıcı]** Mikrofona basıp konuşur, kaydı durdurur.
4. **[Frontend -> STT Backend]** Ses dosyası `/stt/transcribe` API'sine gider, metin (text) olarak geri döner.
5. **[Frontend]** Dönen metin doğrudan `gr.Textbox` içine yazılır. Kullanıcı hataları düzeltir.
6. **[Frontend -> LLM Backend]** Kullanıcı "Gönder" dediğinde bu metin sohbet balonuna eklenir ve mevcut LLM API'sine gider.
7. **[Sistem]** Bu döngü 5 kez tekrarlanır.
8. **[Backend]** 5 soru bitince, 3. Kişinin yazdığı sistem devreye girer ve tüm sürecin analizini yapıp rapor çıkarır.

# FastAPI Projesi Kurulum ve Geliştirme Kılavuzu

Bu kılavuz, **AI-CareerCoach** backend servisi için oluşturduğumuz FastAPI şablonunu nasıl ayağa kaldıracağınızı, yapısını ve nasıl yeni özellikler ekleyeceğinizi adım adım açıklamaktadır.

---

## 📂 Proje Yapısı

Oluşturduğumuz modüler yapı, büyük projelerde temiz kod yazımını ve kolay yönetilebilirliği destekler:

*   📂 **`app/`**: Tüm uygulama kodlarının bulunduğu ana klasör.
    *   📄 **`app/main.py`**: Uygulamanın giriş noktası (Entrypoint). FastAPI nesnesini oluşturur, CORS ayarlarını yapar ve yönlendiricileri (routers) bağlar.
    *   📂 **`app/core/`**: Ayarlar ve veritabanı bağlantısı gibi çekirdek yapılandırmalar.
        *   📄 **`app/core/config.py`**: `pydantic-settings` kullanarak çevre değişkenlerini (.env) ve genel ayarları yönetir.
    *   📂 **`app/api/`**: API endpoint'lerinin ve yönlendirmelerin yönetildiği yer.
        *   📄 **`app/api/router.py`**: Tüm alt modüllerin rotalarını birleştirip `main.py`'a sunar.
        *   📂 **`app/api/endpoints/`**: İş mantığının (business logic) ve API adreslerinin bulunduğu yer.
            *   📄 **`app/api/endpoints/cv.py`**: CV yükleme, ATS puanlaması ve analiz rotaları.
            *   📄 **`app/api/endpoints/interview.py`**: Mülakat simülasyonunu başlatma ve cevap değerlendirme rotaları.
*   📄 **`requirements.txt`**: Projenin çalışması için gerekli kütüphanelerin listesi.
*   📄 **`FASTAPI_TUTORIAL.md`**: Bu kılavuz dosyası.

---

## 🚀 Adım Adım Çalıştırma Kılavuzu

FastAPI projesini bilgisayarınızda çalıştırmak için aşağıdaki adımları sırasıyla uygulayın.

### Adım 1: Terminalinizi Açın
VS Code veya kullandığınız editörün terminalinde projenizin ana dizininde (`/Users/elifsenasoysal/Documents/GitHub/AI-CareerCoach`) olduğunuzdan emin olun.

### Adım 2: Sanal Ortam (Virtual Environment) Oluşturun
Python paketlerinizin diğer projelerle karışmaması için bir sanal ortam oluşturmak en iyi pratiktir:

```bash
# MacOS/Linux için:
python3 -m venv venv
```

### Adım 3: Sanal Ortamı Aktif Hale Getirin
Sanal ortamı aktifleştirdiğinizde terminal satırınızın başında `(venv)` ifadesini göreceksiniz:

```bash
# MacOS/Linux için:
source venv/bin/activate
```

### Adım 4: Gerekli Kütüphaneleri Yükleyin
`requirements.txt` dosyasındaki kütüphaneleri sanal ortamınıza yükleyin:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Adım 5: FastAPI Uygulamasını Başlatın
Uygulamayı geliştirme modunda (canlı yenileme ile) çalıştırmak için **Uvicorn** sunucusunu başlatın:

```bash
uvicorn app.main:app --reload
```

> 💡 **Açıklama:** 
> *   `app.main`: `app` klasörünün içindeki `main.py` dosyasını işaret eder.
> *   `:app`: `main.py` dosyasının içindeki `app = FastAPI(...)` değişkenini işaret eder.
> *   `--reload`: Kodda bir değişiklik yaptığınızda sunucunun otomatik olarak yeniden başlamasını sağlar.

Sunucu başarıyla başladığında terminalde şöyle bir çıktı göreceksiniz:
`INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`

---

## 🔌 API'yi Test Etme ve Dokümantasyon

FastAPI'nin en güçlü özelliklerinden biri, yazdığınız kodlardan otomatik olarak interaktif API dokümantasyonu üretmesidir.

1.  Tarayıcınızı açın ve [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) adresine gidin.
2.  Karşınıza **Swagger UI** çıkacaktır. Burada oluşturduğumuz tüm API endpoint'lerini görebilirsiniz:
    *   `GET /`: Sağlık kontrolü (Health Check).
    *   `POST /api/v1/cv/analyze`: CV Dosyası yükleme testi.
    *   `POST /api/v1/interview/start`: Mülakat simülasyonu başlatma.
    *   `POST /api/v1/interview/respond`: Sorulara cevap verme ve puanlama.

### 🧪 Swagger Üzerinde Test Etme
*   Bir endpoint'e tıklayın (örn: `/api/v1/interview/start`).
*   Sağ üstteki **"Try it out"** butonuna tıklayın.
*   Açılan JSON şablonunu dilediğiniz gibi düzenleyin (örn: `role: "Python Developer", experience_level: "Mid"`).
*   **"Execute"** butonuna basarak API'den dönen gerçek cevabı (Response) görüntüleyin.

---

## 🛠️ Yeni Bir Endpoint Nasıl Eklenir?

Projenize yeni bir rota eklemek istediğinizde şu adımları izleyin:

1.  **Girdi/Çıktı Şeması Oluşturun (Pydantic Models):**
    İlgili endpoint dosyasının en üstünde request ve response yapılarını doğrulamak için `BaseModel` sınıfları oluşturun.
    ```python
    from pydantic import BaseModel

    class MyRequest(BaseModel):
        username: str
        age: int
    ```

2.  **Rota Fonksiyonunu Tanımlayın:**
    `APIRouter` nesnesini kullanarak HTTP metodunu (GET, POST, PUT, DELETE vb.) belirtip fonksiyonunuzu yazın.
    ```python
    @router.post("/my-endpoint")
    async def my_function(data: MyRequest):
        return {"message": f"Merhaba {data.username}"}
    ```

3.  **Yeni Rota Modülünü Bağlayın (Eğer yeni bir dosya açtıysanız):**
    [app/api/router.py](file:///Users/elifsenasoysal/Documents/GitHub/AI-CareerCoach/app/api/router.py) dosyasına gidip import edin ve `api_router.include_router` ile dahil edin.

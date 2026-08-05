# Python tabanlı resmi ve hafif bir imaj kullanıyoruz
FROM python:3.11-slim

# Çalışma dizinini belirliyoruz
WORKDIR /app

# Gerekli sistem paketlerini kuruyoruz (gcc vb. derleme araçları)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Bağımlılık listesini kopyalayıp yüklüyoruz
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodlarını kopyalıyoruz
COPY . .

# FastAPI'nin çalışacağı portu dışarıya açıyoruz
EXPOSE 8000

# Uygulamayı başlatıyoruz
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

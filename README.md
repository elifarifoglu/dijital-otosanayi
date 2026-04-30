# Dijitalleştirilmiş Otosanayi

## 1. Proje özeti
Bu proje, otosanayi işletmeleri ve müşterileri için temel bir web uygulaması iskeletidir. Backend FastAPI ile çalışıyor, frontend React ve Vite ile oluşturuluyor. Şu anda backend’de sağlık kontrolleri ve temel CORS yapılandırması var; frontend ise basit bir React uygulaması.

## 2. Teknolojiler
- Python, FastAPI
- PostgreSQL
- React, Vite
- JavaScript

## 3. Klasör yapısı
- `backend/` — FastAPI sunucusu
- `frontend/` — React uygulaması
- `docs/` — proje belgeleri

## 4. Gereksinimler
1. Python 3.11 veya 3.12
2. PostgreSQL
3. Node.js ve npm
4. `pip` ve `npm` komut satırı araçları

## 5. Backend kurulumu
1. `cd backend`
2. `python -m venv .venv`
3. PowerShell için: `.\.venv\Scripts\Activate.ps1`
4. `pip install -r requirements.txt`
5. `.env.example` dosyasını kopyala:
   - `copy .env.example .env`
6. `.env` içindeki `DATABASE_URL` değerini PostgreSQL bağlantına göre ayarla
7. PostgreSQL sunucusunun çalışıyor olduğundan emin ol
8. Gerekirse `CORS_ORIGINS` değerini güncelle

## 6. Frontend kurulumu
1. `cd frontend`
2. `npm install`
3. `.env.example` dosyasını kopyala:
   - `copy .env.example .env`
4. Gerekirse `VITE_API_BASE_URL` değerini `http://127.0.0.1:8000` olarak bırak

## 7. Environment değişkenleri
- Backend:
  - `DATABASE_URL`
  - `CORS_ORIGINS`
- Frontend:
  - `VITE_API_BASE_URL`
  - `VITE_APP_NAME`

Her iki klasörde de `.env.example` dosyası mevcut. Bunlardan `.env` dosyası oluşturup kendi ortamına göre düzenle.

## 8. Uygulamayı çalıştırma
### Backend
- `cd backend`
- `.\.venv\Scripts\Activate.ps1`
- `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`

### Frontend
- `cd frontend`
- `npm run dev`

Frontend `http://localhost:5173` adresinde açılır.

## 9. Doğrulama adımları
1. Backend çalıştıktan sonra:
   - `http://127.0.0.1:8000/`
   - `http://127.0.0.1:8000/health`
2. Frontend çalıştıktan sonra:
   - `http://localhost:5173`
3. Backend ve frontend ayrı terminalde çalıştırılmalı

## 10. Mevcut durum ve notlar
- Proje şu anda başlangıç aşamasında: backend temel sağlık kontrollerini sunuyor, frontend temel React iskeletine sahip.
- Tam kullanıcı, iş emri veya auth özellikleri henüz eklenmedi.
- README sadece mevcut çalışan kurulum adımlarını içerir.

# Dijital Otosanayi

Otosanayi işletmeleri ve müşterileri için geliştirilmiş web tabanlı bir bitirme projesidir.

Müşteriler; kayıtlı işletmeleri listeleyebilir, işletme detaylarını ve yorumlarını görüntüleyebilir, kendi iş emirlerinin süreç durumunu takip edebilir. İşletme sahipleri ise müşteri için iş emri oluşturabilir, durum güncelleyebilir ve işletmelerine ait hizmet ile minimum fiyatları yönetebilir.

---

## Kullanılan Teknolojiler

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic
- **Veritabanı:** PostgreSQL
- **Frontend:** React, Vite
- **Kimlik Doğrulama:** JWT

---

## Proje Yapısı

```
backend/                   FastAPI uygulaması
frontend/                  React arayüzü
backend/migrations/        Alembic migration dosyaları
backend/seed_demo_data.py  Demo verisi oluşturma scripti
```

---

## Temel Özellikler

- Kullanıcı kayıt ve giriş işlemleri
- Rol tabanlı yetkilendirme (müşteri / işletme sahibi)
- İşletme listeleme ve detay görüntüleme
- Yorum ve puan sistemi ile ortalama puan gösterimi
- İş emri oluşturma ve durum güncelleme
- Müşterinin kendi iş emirlerini takip etmesi
- İşletme hizmet kataloğu ve minimum fiyat yönetimi

---

## Kurulum

### Gereksinimler

- Python 3.11 veya 3.12
- PostgreSQL
- Node.js ve npm

### Backend

```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

---

## Environment Değişkenleri

`backend/.env` dosyası oluşturup aşağıdaki değerleri kendi ortamına göre ayarla:

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/dijital_otosanayi
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

`frontend/.env` dosyası (gerekirse):

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## Veritabanı Migration

```bash
cd backend
alembic upgrade head
```

---

## Demo Verisi Oluşturma

```bash
cd backend
python seed_demo_data.py
```

---

## Uygulamayı Çalıştırma

### Backend

```bash
cd backend
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm run dev
```

Frontend `http://localhost:5173` adresinde açılır.

---

## Demo Hesapları

Aşağıdaki hesaplar `seed_demo_data.py` scripti çalıştırıldığında oluşturulan örnek hesaplardır:

| Rol | E-posta | Şifre |
|---|---|---|
| Müşteri | demo.customer@example.com | Demo12345 |
| İşletme Sahibi | demo.owner@example.com | Demo12345 |
| Yönetici | demo.admin@example.com | Demo12345 |

---

## Temel API Endpointleri

| Yöntem | Endpoint | Açıklama |
|---|---|---|
| POST | /auth/register | Kullanıcı kaydı |
| POST | /auth/login | Giriş ve token alma |
| GET | /businesses | İşletme listesi |
| GET | /businesses/{id} | İşletme detayı |
| POST | /businesses/{id}/reviews | Yorum ekleme |
| GET | /my/work-orders | Müşterinin iş emirleri |
| POST | /work-orders | İş emri oluşturma |
| PATCH | /work-orders/{id}/status | İş emri durumu güncelleme |

---

## Demo Akışı

**Müşteri olarak:**
1. Müşteri hesabıyla giriş yap.
2. İşletmeler ekranından işletmeleri listele.
3. İşletme detayı ve mevcut yorumları görüntüle.
4. İş Emirlerim ekranından kendi iş emirlerinin durumunu takip et.

**İşletme sahibi olarak:**
1. İşletme sahibi hesabıyla giriş yap.
2. Müşteri ve araç seçerek yeni iş emri oluştur.
3. Mevcut iş emirlerinin durumunu güncelle.
4. İşletmeye ait hizmetleri ve minimum fiyatları yönet.

---

## Notlar

Proje yerel geliştirme ortamında çalıştırılacak şekilde hazırlanmıştır. Deployment yapılandırması, gelişmiş arama ve filtreleme, bildirim sistemi gibi özellikler ilerleyen aşamalarda geliştirilebilir.

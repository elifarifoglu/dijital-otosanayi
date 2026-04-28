import os
from dotenv import load_dotenv

load_dotenv()

# Uygulama ayarları
APP_NAME = os.getenv("APP_NAME", "Dijital Oto Sanayi API")

# Veritabanı
DATABASE_URL = os.getenv("DATABASE_URL")

# CORS Origins - .env'den virgülüyle ayrılmış string olarak gelir, listeye çevir
CORS_ORIGINS_STR = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",") if origin.strip()]

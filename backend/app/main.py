from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.db import engine
from app.config import CORS_ORIGINS
from app.routers import auth
from app.routers import business
from app.routers import workorder
from app.routers import customer
from app.routers import service

app = FastAPI()

# Routers
app.include_router(auth.router)
app.include_router(business.router)
app.include_router(workorder.router)
app.include_router(customer.router)
app.include_router(service.router)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "API çalışıyor"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/health/db")
def health_db():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()
        return {"database": "connected", "result": value}
    except Exception as e:
        return {"database": "error", "detail": str(e)}
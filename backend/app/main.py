from fastapi import FastAPI
from sqlalchemy import text
from app.db import engine

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API çalışıyor"}

@app.get("/health/db")
def health_db():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.scalar()
        return {"database": "connected", "result": value}
    except Exception as e:
        return {"database": "error", "detail": str(e)}
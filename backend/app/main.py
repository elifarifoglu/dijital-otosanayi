from fastapi import FastAPI

app = FastAPI(title="Dijital Otosanayi API")

@app.get("/")
def read_root():
    return {"message": "Dijital Otosanayi API calisiyor"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
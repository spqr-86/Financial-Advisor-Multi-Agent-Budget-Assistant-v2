"""FastAPI Gateway for Budget Assistant."""
from fastapi import FastAPI
from src.api.routes import router

app = FastAPI(title="Budget Assistant API Gateway", version="2.0.0")
app.include_router(router)

@app.get("/")
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "api-gateway"}

"""FastAPI MCP Service for Budget Assistant."""
from fastapi import FastAPI
from src.mcp.routes import router

app = FastAPI(title="Budget Assistant MCP", version="2.0.0")
app.include_router(router)


@app.get("/")
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mcp"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)

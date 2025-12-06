"""FastAPI Gateway for Budget Assistant."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import settings
from src.api.routes import router
from src.core.exceptions import BudgetException, budget_exception_handler
from src.core.http_client import ServiceClient
from src.core.schemas import HealthResponse

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# MCP client singleton
mcp_client: ServiceClient | None = None


def get_mcp_client() -> ServiceClient:
    """Get MCP service client."""
    global mcp_client
    if mcp_client is None:
        mcp_client = ServiceClient(
            base_url=settings.mcp_api_url,
            timeout=settings.request_timeout,
            max_retries=3,
        )
    return mcp_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting API Gateway...")
    yield
    # Cleanup
    if mcp_client:
        await mcp_client.close()
    logger.info("API Gateway stopped")


app = FastAPI(
    title="Budget Assistant API Gateway",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Exception handlers
app.add_exception_handler(BudgetException, budget_exception_handler)

# Include routes
app.include_router(router)


@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    mcp_ok = await get_mcp_client().health_check()
    return HealthResponse(
        status="healthy" if mcp_ok else "degraded",
        service="api-gateway",
        dependencies={"mcp": mcp_ok},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8081)

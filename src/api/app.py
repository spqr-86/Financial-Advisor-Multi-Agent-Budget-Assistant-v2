"""FastAPI Gateway for Budget Assistant."""

import logging
import signal
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

# Shutdown flag for graceful shutdown
_shutdown_event = False

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


async def graceful_shutdown() -> None:
    """Handle graceful shutdown."""
    global _shutdown_event
    _shutdown_event = True
    logger.info("Shutting down API Gateway gracefully...")

    # Close HTTP client
    if mcp_client:
        logger.info("Closing MCP client connection...")
        await mcp_client.close()

    logger.info("API Gateway shutdown complete")


def signal_handler(sig: int, frame: any) -> None:
    """Handle shutdown signals."""
    sig_name = signal.Signals(sig).name
    logger.info(f"Received {sig_name}, initiating graceful shutdown...")
    # Note: FastAPI/uvicorn handles the actual shutdown
    # This is just for logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting API Gateway...")

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    logger.info("Shutdown handlers registered (SIGTERM, SIGINT)")

    yield

    # Cleanup
    await graceful_shutdown()


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

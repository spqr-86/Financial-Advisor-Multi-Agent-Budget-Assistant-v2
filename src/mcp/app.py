"""FastAPI MCP Service for Budget Assistant."""

import logging
import signal
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.core.exceptions import BudgetException, budget_exception_handler
from src.core.schemas import HealthResponse
from src.mcp.config import settings
from src.mcp.routes import router

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Shutdown flag for graceful shutdown
_shutdown_event = False


async def graceful_shutdown() -> None:
    """Handle graceful shutdown."""
    global _shutdown_event
    _shutdown_event = True
    logger.info("Shutting down MCP Service gracefully...")

    # Close any open resources (storage connections, etc.)
    from src.mcp.routes import _storage, _agent

    if _storage:
        logger.info("Closing storage connections...")
        # GoogleSheetsStorage doesn't need explicit close, but we log it

    if _agent:
        logger.info("Shutting down AI agent...")
        # ADKBudgetAgent cleanup if needed

    logger.info("MCP Service shutdown complete")


def signal_handler(sig: int, frame: any) -> None:
    """Handle shutdown signals."""
    sig_name = signal.Signals(sig).name
    logger.info(f"Received {sig_name}, initiating graceful shutdown...")
    # Note: FastAPI/uvicorn handles the actual shutdown
    # This is just for logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting MCP Service...")

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    logger.info("Shutdown handlers registered (SIGTERM, SIGINT)")

    # Initialize agent system on startup
    logger.info("AI agent system ready (lazy initialization)")

    yield

    # Cleanup
    await graceful_shutdown()


app = FastAPI(
    title="Budget Assistant MCP",
    version="2.0.0",
    lifespan=lifespan,
)

# Exception handlers
app.add_exception_handler(BudgetException, budget_exception_handler)

# Include routes
app.include_router(router)


@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    # TODO: Check agent system health in Iteration 6
    return HealthResponse(
        status="healthy",
        service="mcp",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8082)

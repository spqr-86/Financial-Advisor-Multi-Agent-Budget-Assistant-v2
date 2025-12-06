"""FastAPI MCP Service for Budget Assistant."""

import logging
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting MCP Service...")
    # TODO: Initialize agent system here in Iteration 6
    yield
    # Cleanup
    logger.info("MCP Service stopped")


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

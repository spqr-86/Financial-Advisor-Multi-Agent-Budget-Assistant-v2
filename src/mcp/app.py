"""FastAPI MCP Service for Budget Assistant."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.core.exceptions import BudgetException, budget_exception_handler
from src.core.schemas import HealthResponse
from src.mcp.config import settings
from src.mcp.routes import router
from src.mcp.server.app import mcp

# MCP Server imports
from src.mcp.server.config import MCPServerSettings

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# MCP Server settings
mcp_settings = MCPServerSettings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Starting MCP Service...")
    logger.info("AI agent system ready (lazy initialization)")

    yield

    # Cleanup on shutdown (uvicorn handles SIGTERM/SIGINT automatically)
    logger.info("Shutting down MCP Service gracefully...")

    # Close any open resources
    from src.mcp.routes import _agent, _storage

    if _storage:
        logger.info("Closing storage connections...")

    if _agent:
        logger.info("Shutting down AI agent...")

    logger.info("MCP Service shutdown complete")


app = FastAPI(
    title="Budget Assistant MCP",
    version="2.0.0",
    lifespan=lifespan,
)

# Exception handlers
app.add_exception_handler(BudgetException, budget_exception_handler)

# Include routes
app.include_router(router)


# MCP SSE endpoint (if transport is sse or both)
# FastMCP 2.x: use http_app() with transport="sse" and mount as ASGI app
if mcp_settings.mcp_transport in ("sse", "both"):
    logger.info(
        f"MCP SSE transport enabled, mounting at /mcp"
    )
    # Create MCP ASGI app with SSE transport
    mcp_asgi_app = mcp.http_app(path="/", transport="sse")
    # Mount MCP app under /mcp path
    app.mount("/mcp", mcp_asgi_app)


@app.get("/", response_model=HealthResponse)
@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service="mcp",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8082)

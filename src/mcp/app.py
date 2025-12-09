"""FastAPI MCP Service for Budget Assistant."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from src.core.exceptions import BudgetException, budget_exception_handler
from src.core.schemas import HealthResponse
from src.mcp.config import settings
from src.mcp.routes import router

# MCP Server imports
from src.mcp.server.config import MCPServerSettings
from src.mcp.server.app import mcp

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
    from src.mcp.routes import _storage, _agent

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
if mcp_settings.mcp_transport in ("sse", "both"):
    logger.info(
        f"MCP SSE transport enabled on "
        f"{mcp_settings.mcp_sse_host}:{mcp_settings.mcp_sse_port}"
    )

    @app.get("/mcp/sse")
    async def mcp_sse_endpoint():
        """MCP Server-Sent Events endpoint for web clients."""
        return StreamingResponse(
            mcp.sse_handler(),
            media_type="text/event-stream"
        )


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

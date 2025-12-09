"""Run MCP server in stdio mode for Claude Desktop."""

import asyncio
import logging

from src.mcp.server.app import mcp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info("Starting Budget Assistant MCP server in stdio mode...")
    logger.info("Ready to accept connections from Claude Desktop")

    # FastMCP автоматически определяет stdio transport
    asyncio.run(mcp.run())

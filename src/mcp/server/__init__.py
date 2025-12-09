"""MCP Server для Budget Assistant v2.0."""

from src.mcp.server.app import mcp
from src.mcp.server.config import MCPServerSettings

__all__ = ["mcp", "MCPServerSettings"]

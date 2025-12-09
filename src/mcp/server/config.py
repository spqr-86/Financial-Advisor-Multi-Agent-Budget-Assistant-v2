"""MCP Server configuration."""

from src.core.config import BaseAppSettings


class MCPServerSettings(BaseAppSettings):
    """MCP Server specific settings."""

    # MCP transport settings
    mcp_transport: str = "stdio"  # stdio, sse, both
    mcp_sse_host: str = "0.0.0.0"
    mcp_sse_port: int = 8083

    # MCP server metadata
    mcp_server_name: str = "budget-assistant"
    mcp_server_version: str = "2.0.0"


settings = MCPServerSettings()

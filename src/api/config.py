"""API Gateway service configuration."""

from src.core.config import BaseAppSettings


class APISettings(BaseAppSettings):
    """API Gateway specific settings."""

    # MCP Service URL
    mcp_api_url: str = "http://localhost:8082"

    # Request timeouts
    request_timeout: int = 30


settings = APISettings()

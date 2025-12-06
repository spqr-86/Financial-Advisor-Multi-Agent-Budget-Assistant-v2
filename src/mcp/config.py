"""MCP service configuration."""

from src.core.config import BaseAppSettings


class MCPSettings(BaseAppSettings):
    """MCP (AI agents) specific settings."""

    # Google AI
    google_api_key: str = ""

    # Google Sheets
    spreadsheet_name: str = "Бюджет"
    google_sheets_credentials: str = "credentials.json"

    # Agent settings
    agent_timeout: int = 60
    max_retries: int = 3


settings = MCPSettings()

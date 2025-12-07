"""MCP service configuration."""

from src.core.config import BaseAppSettings


class MCPSettings(BaseAppSettings):
    """MCP (AI agents) specific settings."""

    # Google AI
    google_api_key: str = ""

    # Google Sheets
    google_application_credentials: str = "./service-account.json"
    google_sheets_spreadsheet_name: str = "Budget Assistant Data"
    google_sheets_spreadsheet_id: str | None = None

    # Agent settings
    agent_timeout: int = 60
    max_retries: int = 3


settings = MCPSettings()

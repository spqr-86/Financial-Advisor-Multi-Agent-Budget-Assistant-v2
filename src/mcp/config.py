"""MCP service configuration."""

from src.core.config import BaseAppSettings


class MCPSettings(BaseAppSettings):
    """MCP (AI agents) specific settings."""

    # Google AI
    google_api_key: str = ""

    # Google Sheets
    # Supports both GOOGLE_APPLICATION_CREDENTIALS (file path) and
    # GOOGLE_APPLICATION_CREDENTIALS_JSON (JSON string from Secret Manager)
    google_application_credentials: str = "./service-account.json"
    google_application_credentials_json: str = ""  # Cloud Run secret
    google_sheets_spreadsheet_name: str = "Budget Assistant Data"
    google_sheets_spreadsheet_id: str | None = None

    # Agent settings
    agent_timeout: int = 60
    max_retries: int = 3
    gemini_model: str = "gemini-flash-latest"  # Can be overridden via GEMINI_MODEL env var

    @property
    def credentials_source(self) -> str:
        """Get credentials from JSON or file path."""
        return self.google_application_credentials_json or self.google_application_credentials


settings = MCPSettings()

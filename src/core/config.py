"""Centralized configuration with Pydantic validation."""

from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings with validation."""

    # Telegram
    telegram_bot_token: str
    telegram_admin_ids: List[int] = []
    webhook_secret: Optional[str] = None

    # API
    budget_api_url: Optional[str] = None

    # Gemini
    google_api_key: str = ""

    # Google Sheets
    spreadsheet_name: str = "Бюджет"
    google_sheets_credentials: str = "credentials.json"

    # Runtime
    log_level: str = "INFO"
    environment: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()

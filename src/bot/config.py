"""Bot service configuration."""

from src.core.config import BaseAppSettings


class BotSettings(BaseAppSettings):
    """Telegram bot specific settings."""

    # Telegram
    telegram_bot_token: str
    telegram_admin_ids: list[int] = []
    webhook_secret: str | None = None

    # API Gateway URL
    budget_api_url: str = "http://localhost:8081"


settings = BotSettings()

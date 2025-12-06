"""Telegram Bot - Webhook mode for Cloud Run."""

import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from src.core.config import settings
from src.bot.handlers import router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

def create_app() -> web.Application:
    """Create aiohttp application with bot webhook."""

    # Initialize bot
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Initialize dispatcher
    dp = Dispatcher()
    dp.include_router(router)

    # Create web app
    app = web.Application()

    # Health check
    async def health(request):
        return web.json_response({"status": "healthy"})

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    # Setup webhook
    webhook_path = "/webhook"
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret
    ).register(app, path=webhook_path)

    setup_application(app, dp, bot=bot)

    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=8080)

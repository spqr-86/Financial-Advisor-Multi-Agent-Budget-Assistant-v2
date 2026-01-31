"""Telegram Bot - Webhook mode for Cloud Run."""

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from src.bot.config import settings
from src.bot.handlers import callbacks, commands, structured
from src.bot.handlers import router as main_router
from src.bot.middlewares import APIClientMiddleware, RequestIdMiddleware
from src.core.constants import MAX_RETRIES, REQUEST_TIMEOUT
from src.core.http_client import ServiceClient

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> web.Application:
    """Create aiohttp application with bot webhook."""

    # Initialize bot
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Initialize dispatcher
    dp = Dispatcher()

    # Register routers (order matters: structured, commands, callbacks, main)
    # structured router must be first to handle /add command and FSM states
    dp.include_router(structured.router)
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(main_router)

    # Setup middlewares (order matters: RequestId first for tracing)
    dp.message.middleware(RequestIdMiddleware())
    dp.callback_query.middleware(RequestIdMiddleware())

    # Setup API client middleware
    api_client = ServiceClient(
        base_url=settings.budget_api_url,
        timeout=REQUEST_TIMEOUT,
        max_retries=MAX_RETRIES,
    )
    dp.message.middleware(APIClientMiddleware(api_client))
    dp.callback_query.middleware(APIClientMiddleware(api_client))

    # Create web app
    app = web.Application()

    # Store references for cleanup
    app["bot"] = bot
    app["api_client"] = api_client

    # Health check
    async def health(request: web.Request) -> web.Response:
        return web.json_response({
            "status": "healthy",
            "service": "bot",
            "version": "2.0.0",
        })

    app.router.add_get("/", health)
    app.router.add_get("/health", health)

    # Setup webhook
    webhook_path = "/webhook"
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret,
    ).register(app, path=webhook_path)

    setup_application(app, dp, bot=bot)

    # Cleanup on shutdown
    async def on_shutdown(app: web.Application) -> None:
        await app["api_client"].close()
        await app["bot"].session.close()

    app.on_shutdown.append(on_shutdown)

    return app


if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=8080)

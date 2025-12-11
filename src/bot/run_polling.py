"""Telegram Bot - Polling mode for local development."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.bot.config import settings
from src.bot.handlers import callbacks, commands
from src.bot.handlers import router as main_router
from src.bot.middlewares import APIClientMiddleware
from src.core.http_client import ServiceClient

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Run bot in polling mode (for local development)."""

    # Initialize bot
    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Initialize dispatcher
    dp = Dispatcher()

    # Register routers (order matters: commands, callbacks, main)
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(main_router)

    # Setup API client middleware
    api_client = ServiceClient(
        base_url=settings.budget_api_url,
        timeout=30,
        max_retries=3,
    )
    dp.message.middleware(APIClientMiddleware(api_client))
    dp.callback_query.middleware(APIClientMiddleware(api_client))

    try:
        logger.info("Starting bot in polling mode...")
        logger.info(f"Budget API URL: {settings.budget_api_url}")

        # Delete webhook (if set) and start polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook deleted, starting polling...")

        await dp.start_polling(bot)
    finally:
        await api_client.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

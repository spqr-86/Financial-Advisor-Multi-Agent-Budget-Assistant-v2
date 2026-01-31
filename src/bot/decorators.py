"""Decorators for bot handlers to reduce code duplication."""

import logging
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)


def require_api_client(func: Callable) -> Callable:
    """Decorator to check that api_client is available.

    Usage:
        @router.message(Command("stats"))
        @require_api_client
        async def cmd_stats(message: Message, api_client: ServiceClient) -> None:
            # api_client is guaranteed to be non-None here
            ...

    Removes the need for repeated boilerplate:
        if not api_client:
            logger.error(...)
            await message.answer("API не настроен...")
            return
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Get api_client from kwargs
        api_client = kwargs.get("api_client")

        # Get message/callback from args or kwargs
        event = args[0] if args else kwargs.get("message") or kwargs.get("callback")

        if not api_client:
            user_id = getattr(event.from_user, "id", "unknown") if event else "unknown"
            logger.error(f"API client not configured for user {user_id}")

            # Handle both Message and CallbackQuery
            if hasattr(event, "answer"):
                await event.answer("Сервис временно недоступен. Попробуйте позже.")
            elif hasattr(event, "message"):
                await event.message.edit_text(
                    "Сервис временно недоступен. Попробуйте позже."
                )
            return

        return await func(*args, **kwargs)

    return wrapper

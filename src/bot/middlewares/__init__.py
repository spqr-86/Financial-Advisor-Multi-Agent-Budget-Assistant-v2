"""Bot middlewares."""

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message

from src.core.http_client import ServiceClient


class APIClientMiddleware(BaseMiddleware):
    """Inject API client into handlers."""

    def __init__(self, api_client: ServiceClient):
        self.api_client = api_client

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        data["api_client"] = self.api_client
        return await handler(event, data)


class RateLimitMiddleware(BaseMiddleware):
    """Rate limiting middleware."""

    def __init__(self, limit: int = 10, window: int = 60):
        from collections import defaultdict
        from datetime import datetime, timedelta

        self.limit = limit
        self.window = timedelta(seconds=window)
        self.requests: dict[int, list[datetime]] = defaultdict(list)

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        from datetime import datetime

        if not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id
        now = datetime.now()

        # Clean old requests
        self.requests[user_id] = [
            t for t in self.requests[user_id]
            if now - t < self.window
        ]

        # Check limit
        if len(self.requests[user_id]) >= self.limit:
            await event.answer("Подождите минуту...")
            return None

        self.requests[user_id].append(now)
        return await handler(event, data)


class AccessControlMiddleware(BaseMiddleware):
    """Access control middleware."""

    def __init__(self, admin_ids: list[int]):
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: dict[str, Any],
    ) -> Any:
        if not event.from_user:
            return None

        # If admin_ids is empty, allow everyone
        if self.admin_ids and event.from_user.id not in self.admin_ids:
            await event.answer("Доступ ограничен")
            return None

        return await handler(event, data)

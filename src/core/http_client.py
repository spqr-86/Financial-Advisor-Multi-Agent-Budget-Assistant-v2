"""Reusable async HTTP client with retry logic."""

import logging
from typing import Any

import aiohttp
from aiohttp import ClientTimeout

from src.core.exceptions import ServiceUnavailableError

logger = logging.getLogger(__name__)


class ServiceClient:
    """Async HTTP client for inter-service communication."""

    def __init__(
        self,
        base_url: str,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self._session

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Make HTTP request with retry logic."""
        session = await self._get_session()
        url = f"{self.base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                async with session.request(method, url, **kwargs) as response:
                    if response.status >= 500:
                        raise ServiceUnavailableError(
                            f"Service returned {response.status}"
                        )
                    response.raise_for_status()
                    return await response.json()

            except aiohttp.ClientError as e:
                last_error = e
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                if attempt == self.max_retries - 1:
                    raise ServiceUnavailableError(
                        f"Service unavailable after {self.max_retries} attempts"
                    ) from e

        raise ServiceUnavailableError("Request failed") from last_error

    async def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Make GET request."""
        return await self._request("GET", path, **kwargs)

    async def post(
        self, path: str, json: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Make POST request."""
        return await self._request("POST", path, json=json, **kwargs)

    async def health_check(self) -> bool:
        """Check if service is healthy."""
        try:
            result = await self.get("/health")
            return result.get("status") == "healthy"
        except Exception:
            return False

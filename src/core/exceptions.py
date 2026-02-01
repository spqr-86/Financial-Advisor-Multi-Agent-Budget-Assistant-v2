"""Custom exceptions for Budget Assistant."""

from fastapi import Request
from fastapi.responses import JSONResponse


class BudgetException(Exception):
    """Base exception for Budget Assistant."""

    status_code: int = 500
    detail: str = "Internal server error"
    code: str = "INTERNAL_ERROR"

    def __init__(self, detail: str | None = None, code: str | None = None):
        self.detail = detail or self.__class__.detail
        self.code = code or self.__class__.code
        super().__init__(self.detail)


class ServiceUnavailableError(BudgetException):
    """Raised when a downstream service is unavailable."""

    status_code = 503
    detail = "Service temporarily unavailable"
    code = "SERVICE_UNAVAILABLE"


class RateLimitError(BudgetException):
    """Raised when rate limit is exceeded."""

    status_code = 429
    detail = "Too many requests"
    code = "RATE_LIMIT_EXCEEDED"


class QuotaExceededError(BudgetException):
    """Raised when API quota is exceeded."""

    status_code = 429
    detail = "API quota exceeded"
    code = "QUOTA_EXCEEDED"


async def budget_exception_handler(
    request: Request, exc: BudgetException
) -> JSONResponse:
    """Handle BudgetException and return JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": exc.code,
        },
    )

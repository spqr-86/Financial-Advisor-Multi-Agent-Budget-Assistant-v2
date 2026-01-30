"""Shared Pydantic schemas for all services."""

from datetime import datetime

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for query processing."""

    query: str = Field(..., min_length=1, max_length=4000)
    user_id: str = Field(..., min_length=1)
    session_id: str | None = None


class QueryResponse(BaseModel):
    """Response model for query processing."""

    response: str
    user_id: str
    session_id: str


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = "healthy"
    service: str
    version: str = "2.0.0"
    dependencies: dict[str, bool] | None = None


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: str | None = None
    code: str | None = None


# Storage schemas


class AddExpenseRequest(BaseModel):
    """Request to add an expense."""

    user_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=500)
    date: datetime | None = None


class GetExpensesRequest(BaseModel):
    """Request to get expenses."""

    user_id: str = Field(..., min_length=1)
    start_date: datetime | None = None
    end_date: datetime | None = None
    category: str | None = None
    limit: int = Field(default=100, ge=1, le=1000)


class GetStatisticsRequest(BaseModel):
    """Request to get statistics."""

    user_id: str = Field(..., min_length=1)
    period: str = Field(default="month", pattern="^(day|week|month|year)$")


class DeleteLastExpenseRequest(BaseModel):
    """Request to delete last expense."""

    user_id: str = Field(..., min_length=1)


# Limit schemas


class GetLimitsRequest(BaseModel):
    """Request to get budget limits."""

    user_id: str = Field(..., min_length=1)


class SetLimitRequest(BaseModel):
    """Request to set a budget limit."""

    user_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., ge=0)


class DeleteLimitRequest(BaseModel):
    """Request to delete a budget limit."""

    user_id: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)


class LimitsResponse(BaseModel):
    """Response with budget limits."""

    status: str
    user_id: str
    limits: dict[str, float] = Field(default_factory=dict)


class LimitResponse(BaseModel):
    """Response for single limit operation."""

    status: str
    user_id: str
    category: str
    limit: float | None = None
    deleted: bool = False
    message: str | None = None

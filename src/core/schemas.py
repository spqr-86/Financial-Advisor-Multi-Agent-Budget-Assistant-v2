"""Shared Pydantic schemas for all services."""

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

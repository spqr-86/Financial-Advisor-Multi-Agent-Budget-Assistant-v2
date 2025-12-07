"""MCP service routes."""

import logging

from fastapi import APIRouter, Depends

from src.core.schemas import (
    AddExpenseRequest,
    GetExpensesRequest,
    GetStatisticsRequest,
    QueryRequest,
    QueryResponse,
)
from src.mcp.storage import GoogleSheetsStorage, StorageInterface

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])

# Storage instance (will be initialized on first use)
_storage: StorageInterface | None = None


def get_storage() -> StorageInterface:
    """Get storage instance (dependency injection)."""
    global _storage
    if _storage is None:
        _storage = GoogleSheetsStorage()
    return _storage


@router.post("/query", response_model=QueryResponse)
async def process_mcp_query(request: QueryRequest) -> QueryResponse:
    """Process user query through AI agent system."""
    # TODO: Replace with agent processing in Iteration 6
    logger.info(f"Processing query from user {request.user_id}: {request.query[:50]}")

    response = f"MCP Echo: {request.query}"

    return QueryResponse(
        response=response,
        user_id=request.user_id,
        session_id=request.session_id or request.user_id,
    )


# Storage endpoints for testing


@router.post("/storage/expenses")
async def add_expense(
    request: AddExpenseRequest,
    storage: StorageInterface = Depends(get_storage),
) -> dict:
    """Add a new expense."""
    logger.info(f"Adding expense for user {request.user_id}: {request.category} - {request.amount}")

    result = await storage.add_expense(
        user_id=request.user_id,
        category=request.category,
        amount=request.amount,
        description=request.description,
        date=request.date,
    )

    return result


@router.post("/storage/expenses/list")
async def get_expenses(
    request: GetExpensesRequest,
    storage: StorageInterface = Depends(get_storage),
) -> dict:
    """Get expenses with filters."""
    logger.info(f"Getting expenses for user {request.user_id}")

    result = await storage.get_expenses(
        user_id=request.user_id,
        start_date=request.start_date,
        end_date=request.end_date,
        category=request.category,
        limit=request.limit,
    )

    return result


@router.post("/storage/statistics")
async def get_statistics(
    request: GetStatisticsRequest,
    storage: StorageInterface = Depends(get_storage),
) -> dict:
    """Get expense statistics."""
    logger.info(f"Getting statistics for user {request.user_id}, period: {request.period}")

    result = await storage.get_statistics(
        user_id=request.user_id,
        period=request.period,
    )

    return result


@router.get("/storage/health")
async def storage_health(
    storage: StorageInterface = Depends(get_storage),
) -> dict:
    """Check storage health."""
    result = await storage.health_check()
    return result

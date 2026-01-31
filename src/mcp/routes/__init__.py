"""MCP service routes."""

import logging
import time

from fastapi import APIRouter, Depends

from src.core.schemas import (
    AddExpenseRequest,
    DeleteLastExpenseRequest,
    DeleteLimitRequest,
    GetExpensesRequest,
    GetLimitsRequest,
    GetStatisticsRequest,
    LimitResponse,
    LimitsResponse,
    QueryRequest,
    QueryResponse,
    SetLimitRequest,
)
from src.mcp.agents import ADKBudgetAgent
from src.mcp.storage import GoogleSheetsStorage, StorageInterface

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])

# Storage instance (will be initialized on first use)
_storage: StorageInterface | None = None

# AI Agent instance (using ADK patterns)
_agent: ADKBudgetAgent | None = None


def get_storage() -> StorageInterface:
    """Get storage instance (dependency injection)."""
    global _storage
    if _storage is None:
        _storage = GoogleSheetsStorage()
    return _storage


def get_agent() -> ADKBudgetAgent:
    """Get AI agent instance (dependency injection)."""
    global _agent
    if _agent is None:
        _agent = ADKBudgetAgent()
    return _agent


@router.post("/query", response_model=QueryResponse)
async def process_mcp_query(
    request: QueryRequest,
    agent: ADKBudgetAgent = Depends(get_agent),
) -> QueryResponse:
    """Process user query through AI agent system."""
    start_time = time.time()
    query_preview = request.query[:50] + "..." if len(request.query) > 50 else request.query

    logger.info(f"MCP processing query from user {request.user_id}: {query_preview}")

    try:
        # Process through AI agent
        response = await agent.process(
            query=request.query,
            user_id=request.user_id,
        )

        elapsed = time.time() - start_time
        logger.info(
            f"MCP query processed for user {request.user_id} in {elapsed:.2f}s "
            f"(response: {len(response)} chars)"
        )

        # Check if response indicates quota issue (agent handled the error gracefully)
        if "превышен лимит" in response.lower() or "quota" in response.lower():
            logger.warning(
                f"🚨 QUOTA WARNING: Response indicates quota exhausted for user {request.user_id}. "
                f"Check Gemini API quota at: https://ai.google.dev/gemini-api/docs/rate-limits"
            )

        return QueryResponse(
            response=response,
            user_id=request.user_id,
            session_id=request.session_id or request.user_id,
        )

    except Exception as e:
        elapsed = time.time() - start_time

        # Special handling for quota errors
        error_str = str(e).lower()
        if "429" in error_str or "quota" in error_str or "resource_exhausted" in error_str:
            logger.error(
                f"🚨 GEMINI API QUOTA EXCEEDED for user {request.user_id} after {elapsed:.2f}s! "
                f"Check quota at: https://ai.google.dev/gemini-api/docs/rate-limits",
                exc_info=True,
            )
        else:
            logger.error(
                f"MCP query failed for user {request.user_id} after {elapsed:.2f}s: "
                f"{type(e).__name__}: {e}",
                exc_info=True,
            )
        raise


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


@router.post("/storage/expenses/delete-last")
async def delete_last_expense(
    request: DeleteLastExpenseRequest,
    storage: StorageInterface = Depends(get_storage),
) -> dict:
    """Delete the last expense."""
    logger.info(f"Deleting last expense for user {request.user_id}")

    result = await storage.delete_last_expense(
        user_id=request.user_id,
    )

    return result


@router.get("/storage/health")
async def storage_health(
    storage: StorageInterface = Depends(get_storage),
) -> dict:
    """Check storage health."""
    result = await storage.health_check()
    return result


@router.post("/limits", response_model=LimitsResponse)
async def get_limits(
    request: GetLimitsRequest,
    storage: StorageInterface = Depends(get_storage),
) -> LimitsResponse:
    """Get all budget limits."""
    result = await storage.get_limits(request.user_id)
    return LimitsResponse(**result)


@router.post("/limits/set", response_model=LimitResponse)
async def set_limit(
    request: SetLimitRequest,
    storage: StorageInterface = Depends(get_storage),
) -> LimitResponse:
    """Set a budget limit."""
    result = await storage.set_limit(
        request.user_id,
        request.category,
        request.amount,
    )
    return LimitResponse(**result)


@router.post("/limits/delete", response_model=LimitResponse)
async def delete_limit(
    request: DeleteLimitRequest,
    storage: StorageInterface = Depends(get_storage),
) -> LimitResponse:
    """Delete a budget limit."""
    result = await storage.delete_limit(request.user_id, request.category)
    return LimitResponse(**result)

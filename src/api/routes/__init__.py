"""API Gateway routes."""

import logging
import time

from fastapi import APIRouter

from src.core.schemas import (
    LimitResponse,
    LimitsResponse,
    QueryRequest,
    QueryResponse,
    SetLimitRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    """Proxy query to MCP service."""
    from src.api.app import get_mcp_client

    start_time = time.time()
    query_preview = request.query[:50] + "..." if len(request.query) > 50 else request.query

    logger.info(f"Received query from user {request.user_id}: {query_preview}")

    mcp_client = get_mcp_client()

    try:
        result = await mcp_client.post(
            "/mcp/query",
            json={
                "query": request.query,
                "user_id": request.user_id,
            },
        )

        elapsed = time.time() - start_time
        response_length = len(result.get("response", ""))

        logger.info(
            f"Query processed for user {request.user_id} in {elapsed:.2f}s "
            f"(response: {response_length} chars)"
        )

        return QueryResponse(
            response=result.get("response", ""),
            user_id=request.user_id,
            session_id=request.session_id or request.user_id,
        )

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(
            f"Query failed for user {request.user_id} after {elapsed:.2f}s: "
            f"{type(e).__name__}: {e}",
            exc_info=True,
        )
        raise


@router.get("/limits/{user_id}", response_model=LimitsResponse)
async def get_limits(user_id: str) -> LimitsResponse:
    """Get all budget limits for a user."""
    from src.api.app import get_mcp_client

    logger.info(f"Getting limits for user {user_id}")

    mcp_client = get_mcp_client()
    result = await mcp_client.post(
        "/mcp/limits",
        json={"user_id": user_id},
    )

    return LimitsResponse(
        status=result.get("status", "success"),
        user_id=user_id,
        limits=result.get("limits", {}),
    )


@router.post("/limits", response_model=LimitResponse)
async def set_limit(request: SetLimitRequest) -> LimitResponse:
    """Set a budget limit for a category."""
    from src.api.app import get_mcp_client

    logger.info(
        f"Setting limit for user {request.user_id}: "
        f"{request.category} = {request.amount}"
    )

    mcp_client = get_mcp_client()
    result = await mcp_client.post(
        "/mcp/limits/set",
        json={
            "user_id": request.user_id,
            "category": request.category,
            "amount": request.amount,
        },
    )

    return LimitResponse(
        status=result.get("status", "success"),
        user_id=request.user_id,
        category=request.category,
        limit=result.get("limit"),
        deleted=result.get("deleted", False),
        message=result.get("message"),
    )


@router.delete("/limits/{user_id}/{category}", response_model=LimitResponse)
async def delete_limit(user_id: str, category: str) -> LimitResponse:
    """Delete a budget limit for a category."""
    from src.api.app import get_mcp_client

    logger.info(f"Deleting limit for user {user_id}: {category}")

    mcp_client = get_mcp_client()
    result = await mcp_client.post(
        "/mcp/limits/delete",
        json={
            "user_id": user_id,
            "category": category,
        },
    )

    return LimitResponse(
        status=result.get("status", "success"),
        user_id=user_id,
        category=category,
        deleted=True,
    )


@router.get("/statistics/{user_id}/{period}")
async def get_statistics(user_id: str, period: str = "month") -> dict:
    """Get expense statistics directly from storage.

    Returns structured data for formatting with limits.
    """
    from src.api.app import get_mcp_client

    logger.info(f"Getting statistics for user {user_id}, period: {period}")

    mcp_client = get_mcp_client()
    result = await mcp_client.post(
        "/mcp/storage/statistics",
        json={"user_id": user_id, "period": period},
    )

    # Convert to format expected by format_statistics
    return {
        "statistics": {
            "categories": result.get("by_category", {}),
            "total": result.get("total", 0),
        },
        "user_id": user_id,
        "period": period,
    }

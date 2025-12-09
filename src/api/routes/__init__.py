"""API Gateway routes."""

import logging
import time

from fastapi import APIRouter

from src.core.schemas import QueryRequest, QueryResponse

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

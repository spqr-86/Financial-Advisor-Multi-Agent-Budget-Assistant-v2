"""API Gateway routes."""

import logging

from fastapi import APIRouter

from src.core.schemas import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    """Proxy query to MCP service."""
    from src.api.app import get_mcp_client

    mcp_client = get_mcp_client()

    result = await mcp_client.post(
        "/mcp/query",
        json={
            "query": request.query,
            "user_id": request.user_id,
        },
    )

    return QueryResponse(
        response=result.get("response", ""),
        user_id=request.user_id,
        session_id=request.session_id or request.user_id,
    )

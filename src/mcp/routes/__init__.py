"""MCP service routes."""

import logging

from fastapi import APIRouter

from src.core.schemas import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


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

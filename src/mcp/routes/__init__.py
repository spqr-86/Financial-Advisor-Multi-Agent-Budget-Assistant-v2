"""MCP routes."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/mcp")


class MCPQueryRequest(BaseModel):
    query: str
    user_id: str


class MCPQueryResponse(BaseModel):
    response: str


@router.post("/query", response_model=MCPQueryResponse)
async def process_mcp_query(request: MCPQueryRequest):
    """Process user query (placeholder for agent)."""
    # TODO: Add agent processing in Iteration 6
    return MCPQueryResponse(response=f"MCP Echo: {request.query}")

"""API routes."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api")

class QueryRequest(BaseModel):
    query: str
    user_id: str

class QueryResponse(BaseModel):
    response: str

@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process user query (placeholder, will proxy to MCP)."""
    # TODO: Proxy to MCP in Iteration 4
    return QueryResponse(response=f"API Echo: {request.query}")

#!/bin/bash
# Test MCP server with MCP Inspector

set -e

echo "Starting MCP server for testing with MCP Inspector..."
echo ""
echo "1. Install MCP Inspector (if not installed):"
echo "   npx @modelcontextprotocol/inspector"
echo ""
echo "2. Connect to: http://localhost:8083/mcp/sse"
echo ""
echo "3. Test tools:"
echo "   - process_query"
echo "   - add_expense"
echo "   - get_expenses"
echo "   - get_statistics"
echo ""
echo "Press Ctrl+C to stop server"
echo ""

# Set SSE mode
export MCP_TRANSPORT=sse
export MCP_SSE_PORT=8083

# Start server
poetry run python -m src.mcp.app

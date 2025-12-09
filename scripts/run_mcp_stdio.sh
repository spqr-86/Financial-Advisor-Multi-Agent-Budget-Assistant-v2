#!/bin/bash
# Run MCP server in stdio mode for Claude Desktop

set -e

echo "Starting MCP Server (stdio mode)..."

# Activate poetry environment and run
poetry run python -m src.mcp.server.run_stdio

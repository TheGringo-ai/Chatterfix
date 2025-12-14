#!/bin/bash

# ChatterFix MCP Server Startup Script
echo "🚀 Starting ChatterFix CMMS MCP Server..."

# Check if virtual environment exists
if [ ! -d "venv_debug" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv_debug
fi

# Activate virtual environment
source venv_debug/bin/activate

# Install dependencies if needed
echo "📦 Installing MCP dependencies..."
pip install mcp --quiet
echo "📦 Installing project dependencies..."
pip install -r requirements.txt --quiet

# Set environment
export PYTHONPATH="."
export CHATTERFIX_ENV="mcp_validation"

# Start MCP server
echo "✅ ChatterFix MCP Server ready!"
echo "📊 Server provides demo/production consistency validation"
echo "🔍 Use tools: validate_demo_consistency, check_live_data_consistency"
echo ""
echo "Starting server..."
python mcp_server.py
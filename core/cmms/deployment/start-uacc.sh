#!/bin/bash

# Quick Start Script for Universal AI Command Center
# Run this for immediate testing without installation

echo "🚀 Starting Universal AI Command Center..."

# Check if already running
if lsof -Pi :8888 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  UACC is already running on port 8888"
    echo "🌐 Access it at: http://localhost:8888"
    exit 0
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama detected and running"
else
    echo "⚠️  Ollama not running - starting it..."
    ollama serve &
    sleep 3
fi

# Create logs directory
mkdir -p logs

echo "🎯 Starting Universal AI Command Center on http://localhost:8888"
echo "📊 ChatterFix CMMS will be available on http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start the UACC
python3 universal_ai_command_center.py
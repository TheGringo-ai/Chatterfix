#!/bin/bash
echo "🚀 Starting ChatterFix CMMS Enterprise..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start the production server
echo "🌟 ChatterFix CMMS Enterprise starting on http://localhost:8000"
echo "📊 Demo Login: admin / admin123"
echo "🤖 AI Provider: ${AI_PROVIDER:-grok}"
echo "📱 PWA enabled with offline support"
echo ""
echo "Press Ctrl+C to stop the server"

uvicorn app:app --host 0.0.0.0 --port ${CMMS_PORT:-8000} --reload

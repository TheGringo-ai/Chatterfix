#!/bin/bash
echo "🔧 Starting ChatterFix CMMS in Development Mode..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start with hot reload and debug logging
uvicorn app:app --host 127.0.0.1 --port ${CMMS_PORT:-8000} --reload --log-level debug

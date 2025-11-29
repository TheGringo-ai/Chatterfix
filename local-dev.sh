#!/bin/bash

# ChatterFix Local Development Server
# Run your app locally with hot reload for instant edits

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 ChatterFix Local Development${NC}"
echo "==============================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔌 Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.installed" ] || [ "requirements.txt" -nt "venv/.installed" ]; then
    echo -e "${YELLOW}📥 Installing dependencies...${NC}"
    pip install -r requirements.txt
    touch venv/.installed
fi

# Set development environment variables
export USE_FIRESTORE=false  # Use local SQLite for development
export GOOGLE_CLOUD_PROJECT=""
export LOG_LEVEL=debug
export PORT=8000

echo -e "${GREEN}🎯 Development Configuration:${NC}"
echo "• Database: Local SQLite (fast development)"
echo "• Port: 8000" 
echo "• Hot reload: Enabled"
echo "• Debug mode: On"
echo

echo -e "${YELLOW}🔥 Starting development server with hot reload...${NC}"
echo "📝 Edit any file and see changes instantly!"
echo "🌐 Open: http://localhost:8000"
echo "🛑 Stop with: Ctrl+C"
echo

# Start with hot reload
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level debug \
    --reload-dir app \
    --reload-dir . \
    --access-log
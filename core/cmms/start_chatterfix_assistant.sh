#!/bin/bash
# ChatterFix Local Assistant Launcher
# Safely starts the ChatterFix AI Assistant with local-only controls

echo "🚀 Starting ChatterFix Local AI Assistant..."
echo "🔐 Security: Local-only mode enabled"
echo "📁 Working directory: $(pwd)"
echo "=" * 60

# Navigate to the correct directory
cd "$(dirname "$0")"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not found."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Check if the assistant script exists
if [ ! -f "chatterfix_local_assistant.py" ]; then
    echo "❌ ChatterFix Assistant script not found."
    echo "Expected: chatterfix_local_assistant.py"
    exit 1
fi

# Run the assistant
echo "🤖 Launching ChatterFix AI Assistant..."
python3 chatterfix_local_assistant.py

echo "👋 ChatterFix Assistant session ended."
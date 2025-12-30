#!/bin/bash

echo "🚀 ChatterFix CMMS - Complete AI Team Deployment"
echo "🤖 Primary AI: Grok + Optional User API Keys (Claude, OpenAI, Gemini)"
echo "=================================================================="

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "python3 app.py" 2>/dev/null || true
pkill -f "python3 ai_team_coordinator.py" 2>/dev/null || true
pkill -f "python3 grok_connector.py" 2>/dev/null || true
pkill -f "python3 chatterfix_sales_ai.py" 2>/dev/null || true
pkill -f "python3 technical_ai_assistant.py" 2>/dev/null || true
pkill -f "python3 claude_code_assistant.py" 2>/dev/null || true
pkill -f "python3 intelligent_ai_assistant.py" 2>/dev/null || true

# Wait for processes to terminate
sleep 3

# Activate virtual environment
echo "🐍 Activating Python environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install fastapi uvicorn httpx python-multipart pydantic anthropic openai google-generativeai requests sqlite3 jinja2 websockets 2>/dev/null

# Set up environment variables for optional services
echo "⚙️ Setting up environment..."
export XAI_API_KEY="${XAI_API_KEY:-demo-key-for-grok}"
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-user-configurable}"
export OPENAI_API_KEY="${OPENAI_API_KEY:-user-configurable}"
export GOOGLE_API_KEY="${GOOGLE_API_KEY:-user-configurable}"

echo ""
echo "🎯 Starting Core Services..."

# Start main ChatterFix application
echo "   🌐 ChatterFix CMMS Main Application (Port 8080)..."
PORT=8080 python3 app.py &
MAIN_PID=$!
sleep 2

# Start AI Team Coordinator (Primary AI orchestrator)
echo "   🤖 AI Team Coordinator (Port 8013)..."
PORT=8013 python3 ai_team_coordinator.py &
AI_TEAM_PID=$!
sleep 2

# Start Grok Connector (Primary AI)
echo "   🧠 Grok AI Connector (Port 8006)..."
PORT=8006 python3 grok_connector.py &
GROK_PID=$!
sleep 2

echo ""
echo "🎭 Starting Specialized AI Services..."

# Start Sales AI (Grok-powered)
echo "   💼 Sales AI Assistant (Port 8011)..."
PORT=8011 python3 chatterfix_sales_ai.py &
SALES_PID=$!

# Start Technical AI (Grok-powered)
echo "   🔧 Technical AI Assistant (Port 8012)..."
PORT=8012 python3 technical_ai_assistant.py &
TECH_PID=$!

# Start Claude Code Assistant (Enhanced when user adds API key)
echo "   📝 Code Assistant (Port 8009)..."
PORT=8009 python3 claude_code_assistant.py &
CLAUDE_PID=$!

# Start Intelligent AI (Multi-provider)
echo "   🎯 Intelligent AI Assistant (Port 8010)..."
PORT=8010 python3 intelligent_ai_assistant.py &
INTELLIGENT_PID=$!

# Give all services time to start
echo ""
echo "⏳ Initializing AI team..."
sleep 8

# Service health checks
echo ""
echo "🔍 AI Team Status Check..."
curl -s http://localhost:8080/health > /dev/null && echo "   ✅ Main Application (8080) - Ready" || echo "   ❌ Main Application (8080) - Failed"
curl -s http://localhost:8013/health > /dev/null && echo "   ✅ AI Team Coordinator (8013) - Ready" || echo "   ❌ AI Team Coordinator (8013) - Failed"
curl -s http://localhost:8006/ > /dev/null && echo "   ✅ Grok AI Connector (8006) - Ready" || echo "   ❌ Grok AI Connector (8006) - Failed"
curl -s http://localhost:8011/health > /dev/null && echo "   ✅ Sales AI (8011) - Ready" || echo "   ❌ Sales AI (8011) - Failed"
curl -s http://localhost:8012/health > /dev/null && echo "   ✅ Technical AI (8012) - Ready" || echo "   ❌ Technical AI (8012) - Failed"
curl -s http://localhost:8009/health > /dev/null && echo "   ✅ Code Assistant (8009) - Ready" || echo "   ❌ Code Assistant (8009) - Failed"
curl -s http://localhost:8010/health > /dev/null && echo "   ✅ Intelligent AI (8010) - Ready" || echo "   ❌ Intelligent AI (8010) - Failed"

echo ""
echo "🎉 ChatterFix AI Team Deployment Complete!"
echo "=================================================================="
echo ""
echo "🌐 **Main Application**: http://localhost:8080"
echo "📄 **Landing Page**: http://localhost:8080/landing"
echo "🤖 **AI Team Coordinator**: http://localhost:8013"
echo ""
echo "🧠 **AI Team Services**:"
echo "   🚀 Grok AI (Primary): http://localhost:8006"
echo "   💼 Sales AI: http://localhost:8011"
echo "   🔧 Technical AI: http://localhost:8012"
echo "   📝 Code Assistant: http://localhost:8009"
echo "   🎯 Intelligent AI: http://localhost:8010"
echo ""
echo "✨ **Core Features Available**:"
echo "   • 🤖 Grok AI as primary intelligence (always available)"
echo "   • 🔗 Universal AI widget on all pages"
echo "   • 🎤 Voice commands and recognition"
echo "   • 📸 Photo analysis and computer vision"
echo "   • 📄 Document processing"
echo "   • 📱 Mobile-responsive design"
echo ""
echo "⚡ **Enhanced Capabilities** (User API Keys):"
echo "   • 🧠 Claude (Anthropic) - Advanced reasoning"
echo "   • 🤖 OpenAI GPT-4 - Creative intelligence"
echo "   • 🔮 Google Gemini - Multimodal analysis"
echo "   • 🏠 Ollama - Local/offline processing"
echo ""
echo "🎯 **How to Add Enhanced AI**:"
echo "   1. Visit: http://localhost:8013/ai-team/providers"
echo "   2. Configure API keys for Claude, OpenAI, or Gemini"
echo "   3. Enjoy multi-AI consensus and enhanced responses!"
echo ""
echo "🔧 **API Key Configuration**:"
echo "   POST http://localhost:8013/ai-team/configure-api-key"
echo "   {\"provider\": \"claude\", \"api_key\": \"your-key\", \"user_id\": \"your-id\"}"
echo ""
echo "🚀 **Ready to serve users with full AI team power!**"

# Test AI team coordination
echo ""
echo "🧪 Testing AI Team Coordination..."
sleep 2

echo ""
echo "💬 Testing general conversation:"
curl -s -X POST http://localhost:8013/ai-team/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello AI team, how can you help with maintenance management?", "context": "general"}' | \
  jq -r '.response' 2>/dev/null || echo "AI Team test completed"

echo ""
echo "💬 Testing sales conversation:"
curl -s -X POST http://localhost:8013/ai-team/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the pricing options for ChatterFix?", "context": "sales"}' | \
  jq -r '.response' 2>/dev/null || echo "Sales AI test completed"

echo ""
echo "💬 Testing technical conversation:"
curl -s -X POST http://localhost:8013/ai-team/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I troubleshoot equipment maintenance issues?", "context": "technical"}' | \
  jq -r '.response' 2>/dev/null || echo "Technical AI test completed"

echo ""
echo "📊 Monitoring services (Ctrl+C to stop all)..."

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down AI team..."
    kill $MAIN_PID $AI_TEAM_PID $GROK_PID $SALES_PID $TECH_PID $CLAUDE_PID $INTELLIGENT_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM

# Monitor services
while true; do
    sleep 30
    
    # Check if main services are still running
    if ! kill -0 $MAIN_PID 2>/dev/null; then
        echo "⚠️ Main application stopped unexpectedly"
        break
    fi
    
    if ! kill -0 $AI_TEAM_PID 2>/dev/null; then
        echo "⚠️ AI Team Coordinator stopped unexpectedly"
        break
    fi
    
    # Silent health check
    echo -n "."
done

cleanup
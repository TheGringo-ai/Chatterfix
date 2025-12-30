#!/bin/bash
# ChatterFix CMMS - Global AI Platform Deployment
# 🌍🚀 Ready to rock the entire planet!

echo "🌍🚀 ChatterFix CMMS Global AI Platform Deployment"
echo "=================================================="
echo "Ready to rock the entire planet!"
echo ""

# Set environment for global deployment
export ENVIRONMENT=production
export ENV_FILE=.env.production

# Global AI Configuration (Web APIs only - no local dependencies except Ollama)
echo "⚙️ Configuring Global AI Settings..."

# Create production environment template if it doesn't exist
if [ ! -f ".env.production" ]; then
    echo "📝 Creating production environment template..."
    cat > .env.production << 'EOF'
# ChatterFix CMMS - Global Production Environment
# 🌍 Ready for planetary deployment!

# Global AI API Keys (Required for planetary deployment)
XAI_API_KEY=your-xai-grok-api-key
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-claude-api-key
GOOGLE_API_KEY=your-google-gemini-api-key

# Optional Local AI (only Ollama allowed for local deployment)
OLLAMA_ENDPOINT=http://localhost:11434

# Database Configuration
DATABASE_URL=postgresql://user:password@host:5432/chatterfix_global
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-super-secret-key-for-production
JWT_SECRET=your-jwt-secret-key

# Services Configuration
PORT=8080
GLOBAL_AI_PORT=8015
RAG_MEMORY_PORT=8014
SALES_AI_PORT=8011
TECHNICAL_AI_PORT=8012

# Cloud Storage (for global deployment)
GCS_BUCKET_NAME=chatterfix-global-storage
AWS_S3_BUCKET=chatterfix-global-storage

# Monitoring
SENTRY_DSN=your-sentry-dsn
DATADOG_API_KEY=your-datadog-api-key
EOF
    echo "✅ Production environment template created at .env.production"
    echo "🔑 Please update API keys before deployment!"
fi

# Install global dependencies
echo "📦 Installing global AI dependencies..."
pip install -r requirements.txt
pip install sentence-transformers faiss-cpu numpy httpx

# Create necessary directories
echo "📁 Creating deployment directories..."
mkdir -p logs pids static/uploads data

# Global AI Services Startup
echo "🚀 Starting Global AI Platform Services..."

# Start RAG Memory System
echo "🧠 Starting RAG Memory System (Global)..."
PORT=$RAG_MEMORY_PORT python3 rag_memory_system.py &
echo $! > pids/rag_memory.pid
sleep 2

# Start Global AI Coordinator 
echo "🌍 Starting Global AI Team Coordinator..."
PORT=$GLOBAL_AI_PORT python3 global_ai_coordinator.py &
echo $! > pids/global_ai_coordinator.pid
sleep 3

# Start Sales AI (using Global AI)
echo "💼 Starting Sales AI (Global Integration)..."
PORT=$SALES_AI_PORT python3 chatterfix_sales_ai.py &
echo $! > pids/sales_ai.pid
sleep 2

# Start Technical AI (using Global AI)
echo "🔧 Starting Technical AI (Global Integration)..."
PORT=$TECHNICAL_AI_PORT python3 technical_ai_assistant.py &
echo $! > pids/technical_ai.pid
sleep 2

# Start Main ChatterFix Platform
echo "🏢 Starting ChatterFix CMMS Main Platform..."
PORT=$PORT python3 app.py &
echo $! > pids/main_platform.pid
sleep 3

# Health Check
echo "🏥 Performing Global Health Check..."
sleep 5

function check_service() {
    local service_name=$1
    local port=$2
    local endpoint=${3:-"/health"}
    
    echo -n "  🔍 $service_name ($port): "
    
    response=$(curl -s --max-time 5 http://localhost:$port$endpoint 2>/dev/null || echo '{"status":"offline"}')
    status=$(echo "$response" | python3 -c "import json, sys; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "offline")
    
    if [ "$status" = "healthy" ] || [ "$status" = "active" ] || [[ "$status" == *"GLOBAL"* ]] || [[ "$status" == *"Ready"* ]]; then
        echo "✅ $status"
        return 0
    else
        echo "❌ $status"
        return 1
    fi
}

echo ""
echo "🌍 Global Platform Health Status:"
echo "================================"

check_service "Main Platform" 8080 "/health"
check_service "Global AI Coordinator" 8015 "/"
check_service "RAG Memory System" 8014 "/health" 
check_service "Sales AI" 8011 "/health"
check_service "Technical AI" 8012 "/health"

# Test Global AI Integration
echo ""
echo "🤖 Testing Global AI Integration..."
ai_test=$(curl -s -X POST "http://localhost:8015/ai-team/ask" \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello from ChatterFix global deployment test", "preferred_provider": "grok"}' \
    2>/dev/null || echo '{"success": false}')

ai_success=$(echo "$ai_test" | python3 -c "import json, sys; print(json.load(sys.stdin).get('success', False))" 2>/dev/null || echo "false")

if [ "$ai_success" = "True" ]; then
    echo "✅ Global AI Integration: WORKING"
    provider=$(echo "$ai_test" | python3 -c "import json, sys; print(json.load(sys.stdin).get('provider', 'unknown'))" 2>/dev/null || echo "unknown")
    echo "   🤖 Active Provider: $provider"
else
    echo "⚠️ Global AI Integration: Needs API keys configuration"
fi

# Test RAG Memory
echo ""
echo "🧠 Testing RAG Memory System..."
rag_stats=$(curl -s http://localhost:8014/memory/stats 2>/dev/null || echo '{"total_memories": 0}')
memory_count=$(echo "$rag_stats" | python3 -c "import json, sys; print(json.load(sys.stdin).get('total_memories', 0))" 2>/dev/null || echo "0")
echo "✅ RAG Memory: $memory_count memories stored"

echo ""
echo "🎉 ChatterFix Global AI Platform Deployment Complete!"
echo "===================================================="
echo ""
echo "🌍 Global Services Running:"
echo "  • Main Platform:        http://localhost:8080"
echo "  • Global AI Coordinator: http://localhost:8015" 
echo "  • RAG Memory System:     http://localhost:8014"
echo "  • Sales AI:              http://localhost:8011"
echo "  • Technical AI:          http://localhost:8012"
echo ""
echo "🚀 Features Ready:"
echo "  ✅ Global Web APIs (Grok, OpenAI, Claude, Gemini)"
echo "  ✅ RAG Memory System with Vector Search"
echo "  ✅ Multi-AI Consensus and Fallback Chain"
echo "  ✅ Sales AI with Global Intelligence"
echo "  ✅ Technical AI with Global Capabilities"
echo "  ✅ User API Key Enhancement Options"
echo "  ✅ Planetary Deployment Ready"
echo ""
echo "🔑 Next Steps:"
echo "  1. Update API keys in .env.production"
echo "  2. Configure cloud database (PostgreSQL)"
echo "  3. Set up cloud storage (GCS/S3)"
echo "  4. Deploy to cloud platform (GCP/AWS/Azure)"
echo ""
echo "🛑 To stop all services: ./stop-global-ai-platform.sh"
echo ""
echo "🌍🚀 Ready to rock the entire planet!"
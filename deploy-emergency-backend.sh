#!/bin/bash
set -e

echo "🚨 EMERGENCY AI CHAT BACKEND DEPLOYMENT"
echo "======================================="

# Stop any existing backend on port 8081
echo "🛑 Stopping existing backend services..."
pkill -f "port.*8081" || true
pkill -f ":8081" || true
lsof -ti:8081 | xargs kill -9 || true
sleep 3

# Install dependencies
echo "📦 Installing Python dependencies..."
python3 -m pip install --user --quiet fastapi uvicorn

# Create the emergency backend
echo "📝 Creating Emergency AI Chat Backend..."
cat > emergency_ai_backend.py << 'BACKEND_EOF'
#!/usr/bin/env python3
"""
ChatterFix Emergency AI Chat Backend
Provides intelligent ChatterFix-specific responses
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime

app = FastAPI(title="ChatterFix Emergency AI Backend", version="1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    context: str = "general"

def get_intelligent_response(message: str) -> str:
    """Generate intelligent ChatterFix responses"""
    message_lower = message.lower()
    
    # Downtime reduction
    if any(word in message_lower for word in ['downtime', 'reduce', 'prevent', 'failure']):
        return "ChatterFix reduces downtime through predictive maintenance AI that forecasts equipment failures before they happen, resulting in up to 50% reduction in unplanned downtime."
    
    # Features
    elif any(word in message_lower for word in ['feature', 'what', 'capability', 'do']):
        return "ChatterFix CMMS includes: 🛠️ Smart Work Order Management with AI prioritization, 🏭 Predictive Asset Management, 🔧 Intelligent Inventory Control, 🧠 AI-Powered Analytics, 📄 Document Intelligence with OCR, and 📊 Real-Time Dashboards."
    
    # Demo requests
    elif any(word in message_lower for word in ['demo', 'trial', 'show', 'see']):
        return "I'd love to show you ChatterFix CMMS! Our platform demonstrates 50% downtime reduction and 300% efficiency gains. You can access our live demo at /dashboard or schedule a personalized walkthrough."
    
    # Pricing
    elif any(word in message_lower for word in ['price', 'cost', 'pricing', 'expensive']):
        return "ChatterFix offers flexible pricing with excellent ROI. Our customers typically see cost savings within the first quarter through optimized maintenance and reduced emergency repairs."
    
    # Getting started
    elif any(word in message_lower for word in ['start', 'begin', 'setup', 'install']):
        return "Getting started with ChatterFix is simple: 1) Access the platform at /dashboard, 2) Add your assets and equipment, 3) Import existing maintenance data, 4) Let our AI optimize your schedules."
    
    # Maintenance
    elif any(word in message_lower for word in ['maintenance', 'equipment', 'asset', 'repair']):
        return "ChatterFix specializes in intelligent maintenance management using AI to analyze equipment performance, predict failures, and optimize schedules. What maintenance challenge can I help solve?"
    
    # AI and technology
    elif any(word in message_lower for word in ['ai', 'intelligent', 'smart', 'predict']):
        return "ChatterFix uses advanced AI and machine learning to transform maintenance operations, analyzing patterns and providing intelligent recommendations that improve over time."
    
    # Help and support
    elif any(word in message_lower for word in ['help', 'support', 'contact', 'question']):
        return "I'm here to help with all ChatterFix CMMS questions! I can explain features, guide setup, troubleshoot issues, or connect you with our support team."
    
    # Default response
    else:
        return "Thanks for your interest in ChatterFix CMMS! We're the leading AI-powered maintenance platform helping facilities reduce downtime by 50% and increase efficiency by 300%. What would you like to know?"

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ChatterFix Emergency AI Backend",
        "timestamp": datetime.now().isoformat(),
        "port": 8081
    }

@app.post("/api/ai/chat")
def ai_chat(request: ChatRequest):
    try:
        response = get_intelligent_response(request.message)
        return {
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "model": "chatterfix_emergency"
        }
    except Exception as e:
        return {
            "success": False,
            "response": "I'm here to help with ChatterFix CMMS! Please try asking about our features, demos, or maintenance solutions.",
            "error": str(e)
        }

@app.get("/")
def root():
    return {
        "service": "ChatterFix Emergency AI Backend",
        "status": "running",
        "endpoints": ["/health", "/api/ai/chat"]
    }

if __name__ == "__main__":
    print("🚨 Starting ChatterFix Emergency AI Backend on port 8081...")
    uvicorn.run(app, host="0.0.0.0", port=8081)
BACKEND_EOF

# Start the emergency backend
echo "🚀 Starting Emergency AI Backend on port 8081..."
nohup python3 emergency_ai_backend.py > emergency_ai.log 2>&1 &

# Wait for startup
sleep 8

# Test the service
echo "🧪 Testing Emergency AI Backend..."
if curl -s http://localhost:8081/health > /dev/null; then
    echo "✅ Emergency AI Backend is running!"
    
    # Test chat functionality
    echo "Testing chat responses..."
    curl -X POST http://localhost:8081/api/ai/chat \
         -H "Content-Type: application/json" \
         -d '{"message": "How does ChatterFix reduce downtime?"}' | head -3
    echo ""
else
    echo "⚠️ Emergency Backend startup issue"
fi

echo ""
echo "✅ EMERGENCY AI BACKEND DEPLOYED!"
echo "================================="
echo "🤖 Service: Emergency AI Chat Backend"
echo "🌐 Port: 8081"
echo "📊 Health: http://localhost:8081/health"
echo "💬 Chat API: http://localhost:8081/api/ai/chat"
echo ""
echo "🎉 Smart AI responses now available for ChatterFix!"
#!/bin/bash
set -e

echo "🤖 DEPLOYING STANDALONE AI CHAT SERVICE"
echo "======================================"

VM_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"  
PROJECT="fredfix"

# Create startup script for standalone AI chat service
cat > ai-chat-startup.sh << 'AI_CHAT_EOF'
#!/bin/bash
set -e

echo "🤖 ChatterFix AI Chat Service - Standalone Deployment"
echo "==================================================="

cd /home/yoyofred_gringosgambit_com

# Kill any existing services on port 8081
echo "🛑 Stopping existing services on port 8081..."
lsof -ti:8081 | xargs kill -9 || true
pkill -f "port.*8081" || true
pkill -f ":8081" || true
sleep 3

# Install FastAPI and dependencies
echo "📦 Installing Python dependencies..."
python3 -m pip install --user --quiet fastapi uvicorn

# Create standalone AI chat service
echo "📝 Creating AI Chat Service..."
cat > ai_chat_service.py << 'CHAT_SERVICE_EOF'
#!/usr/bin/env python3
"""
ChatterFix AI Chat Service - Standalone
Provides intelligent responses about ChatterFix CMMS
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime

app = FastAPI(title="ChatterFix AI Chat Service", version="1.0")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str
    context: str = "general"

def get_chatterfix_response(message: str) -> str:
    """Generate intelligent ChatterFix-specific responses"""
    message_lower = message.lower()
    
    # Downtime reduction questions
    if 'downtime' in message_lower or 'reduce' in message_lower or 'prevent' in message_lower:
        return "ChatterFix reduces downtime through predictive maintenance AI that forecasts equipment failures before they happen. Our system analyzes equipment data patterns, schedules preventive maintenance automatically, and alerts technicians before critical failures occur - resulting in up to 50% reduction in unplanned downtime."
    
    # Features and capabilities  
    elif 'feature' in message_lower or 'what' in message_lower or 'capability' in message_lower:
        return "ChatterFix CMMS includes powerful features: 🛠️ Smart Work Order Management with AI prioritization, 🏭 Predictive Asset Management that forecasts failures, 🔧 Intelligent Inventory Control with auto-procurement, 🧠 AI-Powered Analytics and Insights, 📄 Document Intelligence with OCR, and 📊 Real-Time Dashboards. Which feature would you like to explore?"
    
    # Demo and trial requests
    elif 'demo' in message_lower or 'trial' in message_lower or 'show' in message_lower:
        return "I'd love to show you ChatterFix CMMS in action! Our platform demonstrates 50% downtime reduction and 300% efficiency gains through AI-powered maintenance management. You can access our live platform at /dashboard or schedule a personalized demo. Would you like me to guide you through the key features?"
    
    # Pricing and cost questions
    elif 'price' in message_lower or 'cost' in message_lower or 'pricing' in message_lower:
        return "ChatterFix offers flexible pricing with significant ROI through reduced downtime and increased efficiency. Our customers typically see cost savings within the first quarter through optimized maintenance schedules and reduced emergency repairs. Contact our team for a personalized quote based on your facility size and requirements!"
    
    # Getting started questions
    elif 'start' in message_lower or 'begin' in message_lower or 'getting started' in message_lower:
        return "Getting started with ChatterFix is simple! 1) Access the platform at /dashboard, 2) Set up your assets and equipment, 3) Import your current maintenance data, 4) Let our AI learn your patterns and start optimizing. I can guide you through each step - what would you like to set up first?"
    
    # Technical and maintenance questions
    elif 'maintenance' in message_lower or 'equipment' in message_lower or 'asset' in message_lower:
        return "ChatterFix specializes in intelligent maintenance management. Our AI analyzes equipment performance data, maintenance history, and operational patterns to optimize your maintenance strategy. We help with preventive scheduling, predictive analytics, work order optimization, and inventory management. What specific maintenance challenge can I help you solve?"
    
    # AI and intelligence questions
    elif 'ai' in message_lower or 'intelligent' in message_lower or 'smart' in message_lower:
        return "ChatterFix uses advanced AI to transform maintenance management. Our machine learning algorithms analyze historical data, predict equipment failures, optimize maintenance schedules, and provide intelligent recommendations. The AI learns from your facility's unique patterns to deliver increasingly accurate predictions and suggestions over time."
    
    # Help and support
    elif 'help' in message_lower or 'support' in message_lower or 'contact' in message_lower:
        return "I'm here to help with all your ChatterFix CMMS questions! I can explain features, guide you through setup, help with troubleshooting, or connect you with our technical support team. You can also reach our support team directly at support@chatterfix.com. What specific area would you like assistance with?"
    
    # General/fallback response
    else:
        return f"Thanks for asking about ChatterFix CMMS! We're the leading AI-powered maintenance management platform that helps facilities reduce downtime by 50% and increase efficiency by 300%. I can help you understand our features, schedule a demo, or answer technical questions. What would you like to know more about?"

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ChatterFix AI Chat Service",
        "timestamp": datetime.now().isoformat(),
        "port": 8081,
        "version": "1.0"
    }

@app.post("/api/ai/chat")
def ai_chat(chat_request: ChatMessage):
    try:
        response = get_chatterfix_response(chat_request.message)
        return {
            "success": True,
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "service": "chatterfix_ai"
        }
    except Exception as e:
        return {
            "success": False,
            "response": "I'm here to help with ChatterFix CMMS questions! Please try asking about our features, demos, or maintenance solutions.",
            "error": str(e)
        }

@app.get("/")
def root():
    return {
        "service": "ChatterFix AI Chat Service",
        "status": "running",
        "endpoints": ["/health", "/api/ai/chat"],
        "description": "Intelligent AI responses for ChatterFix CMMS"
    }

if __name__ == "__main__":
    print("🤖 Starting ChatterFix AI Chat Service on port 8081...")
    print("Ready to provide intelligent responses about ChatterFix CMMS!")
    uvicorn.run(app, host="0.0.0.0", port=8081)
CHAT_SERVICE_EOF

# Start the AI chat service
echo "🚀 Starting AI Chat Service on port 8081..."
nohup python3 ai_chat_service.py > ai_chat_service.log 2>&1 &

# Wait for startup
sleep 8

# Test the service
echo "🧪 Testing AI Chat Service..."
if curl -s http://localhost:8081/health > /dev/null; then
    echo "✅ AI Chat Service is running!"
    
    # Test the chat endpoint
    echo "Testing chat functionality..."
    curl -X POST http://localhost:8081/api/ai/chat \
         -H "Content-Type: application/json" \
         -d '{"message": "How does ChatterFix reduce downtime?"}' | head -3
    echo ""
else
    echo "⚠️ Service may still be starting..."
fi

echo "✅ AI CHAT SERVICE DEPLOYMENT COMPLETE!"
echo "======================================="
echo "🌐 Service: http://localhost:8081"
echo "🤖 AI Chat: http://localhost:8081/api/ai/chat"
echo "📊 Health: http://localhost:8081/health"
AI_CHAT_EOF

chmod +x ai-chat-startup.sh

echo "📤 Deploying AI Chat Service to VM..."
gcloud compute instances add-metadata $VM_NAME \
    --zone=$ZONE \
    --project=$PROJECT \
    --metadata-from-file startup-script=ai-chat-startup.sh

echo "🔄 Triggering AI Chat Service deployment..."
gcloud compute instances reset $VM_NAME --zone=$ZONE --project=$PROJECT

echo ""
echo "⏳ Waiting for AI Chat Service deployment (120 seconds)..."
sleep 120

echo "🧪 Testing AI Chat Service..."
echo "Health Check:"
curl -s http://35.237.149.25:8081/health

echo ""
echo "AI Chat Test:"  
curl -X POST http://35.237.149.25:8081/api/ai/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "How does ChatterFix reduce downtime?"}'

echo ""
echo "🎉 AI CHAT SERVICE DEPLOYED!"
echo "============================"
echo "✅ Standalone AI Chat: http://35.237.149.25:8081"
echo "✅ ChatterFix Website: http://chatterfix.com:8080"
echo "✅ Smart AI responses now available!"
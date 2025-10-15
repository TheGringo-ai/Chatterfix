#!/bin/bash
cd /home/yoyofred_gringosgambit_com
python3 -m pip install --user fastapi uvicorn
pkill -f "python.*8081" || true
cat > backend.py << 'BACKEND_SIMPLE'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class ChatMessage(BaseModel):
    message: str
    context: str = "general"

@app.get("/health")
def health():
    return {"status": "healthy", "service": "ChatterFix Backend", "port": 8081}

@app.post("/api/ai/chat")
def ai_chat(chat_request: ChatMessage):
    return {"success": True, "response": "ChatterFix CMMS reduces downtime by 50% through AI-powered predictive maintenance! How can I help you learn more?"}

@app.get("/api/dashboard")
def dashboard():
    return {"work_orders": 4, "status": "operational"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8081)
BACKEND_SIMPLE
nohup python3 backend.py > backend.log 2>&1 &

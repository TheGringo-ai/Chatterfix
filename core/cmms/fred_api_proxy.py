#!/usr/bin/env python3
"""
Fix It Fred API Proxy - Enables ChatGPT to connect to Fix It Fred
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Fix It Fred AI Service URL (internal)
FRED_AI_URL = "http://localhost:9000"

@app.route('/api/ai/health', methods=['GET'])
def ai_health():
    """Health check endpoint that ChatGPT can use"""
    try:
        response = requests.get(f"{FRED_AI_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "service": "Fix It Fred AI",
                "status": "healthy",
                "fred_status": data.get("status"),
                "providers": data.get("providers", {}),
                "public_access": True
            })
        else:
            return jsonify({"service": "Fix It Fred AI", "status": "unhealthy"}), 503
    except Exception as e:
        return jsonify({"service": "Fix It Fred AI", "status": "error", "message": str(e)}), 503

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """Chat endpoint that ChatGPT can use to talk to Fix It Fred"""
    try:
        # Get message from request
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({"error": "No message provided"}), 400
        
        # Forward to Fix It Fred AI Service
        response = requests.post(
            f"{FRED_AI_URL}/api/chat",
            json={"message": message},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            fred_response = response.json()
            return jsonify({
                "success": True,
                "fred_response": fred_response.get("response", ""),
                "provider": fred_response.get("provider", "unknown"),
                "model": fred_response.get("model", "unknown"),
                "timestamp": fred_response.get("timestamp"),
                "chatgpt_access": True
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Fix It Fred returned status {response.status_code}",
                "message": response.text
            }), response.status_code
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Connection to Fix It Fred failed",
            "message": str(e)
        }), 503

@app.route('/api/ai/status', methods=['GET'])
def ai_status():
    """Full status for ChatGPT integration"""
    try:
        # Test Fix It Fred connection
        response = requests.get(f"{FRED_AI_URL}/health", timeout=5)
        fred_healthy = response.status_code == 200
        
        return jsonify({
            "service": "Fix It Fred API Proxy",
            "status": "online",
            "fred_ai_service": "healthy" if fred_healthy else "unreachable",
            "chatgpt_integration": "ready",
            "endpoints": {
                "health": "/api/ai/health",
                "chat": "/api/ai/chat",
                "status": "/api/ai/status"
            },
            "usage": {
                "chat_example": {
                    "url": "https://chatterfix.com/api/ai/chat",
                    "method": "POST",
                    "body": {"message": "Hello Fix It Fred!"}
                }
            }
        })
    except Exception as e:
        return jsonify({
            "service": "Fix It Fred API Proxy",
            "status": "error",
            "message": str(e)
        }), 503

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8090))
    app.run(host='0.0.0.0', port=port, debug=False)
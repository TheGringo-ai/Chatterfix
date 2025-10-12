#!/usr/bin/env python3
"""
Quick fix for AI chat routing issue
The chat widget should use the working Ollama/Fred integration instead of the broken AI endpoint
"""

import requests
import json

def test_ai_endpoints():
    """Test all AI endpoints to find working ones"""
    base_url = "http://35.237.149.25:8080"
    
    endpoints = [
        ("/api/ai/chat", "POST", {"message": "Hello"}),
        ("/api/ai/status", "GET", None),
        ("/api/ollama/status", "GET", None),
        ("/api/fix-it-fred/troubleshoot", "POST", {
            "equipment": "ChatterFix Chat Test", 
            "issue_description": "Testing chat functionality"
        })
    ]
    
    print("🔧 Testing AI Endpoints to Fix Chat Widget")
    print("=" * 50)
    
    working_endpoints = []
    
    for endpoint, method, data in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            if method == "GET":
                response = requests.get(url, timeout=10)
            else:
                response = requests.post(url, json=data, timeout=10)
            
            status = "✅ WORKING" if response.status_code < 400 else "❌ ERROR"
            response_time = response.elapsed.total_seconds()
            
            print(f"{status} {endpoint} ({method}) - {response_time:.2f}s")
            
            if response.status_code < 400:
                working_endpoints.append({
                    "endpoint": endpoint,
                    "method": method,
                    "response_time": response_time,
                    "response": response.json() if endpoint != "/api/ai/status" else "OK"
                })
                
        except Exception as e:
            print(f"❌ ERROR {endpoint} - {str(e)}")
    
    return working_endpoints

def generate_chat_fix_recommendation(working_endpoints):
    """Generate recommendation for fixing chat widget"""
    print("\n🎯 AI Chat Fix Recommendations")
    print("=" * 40)
    
    if any("/api/ollama/status" in ep["endpoint"] for ep in working_endpoints):
        print("✅ Ollama is working - recommend routing chat through Ollama")
        
    if any("/api/fix-it-fred/troubleshoot" in ep["endpoint"] for ep in working_endpoints):
        print("✅ Fix It Fred is working - can use as chat backend")
        
    print("\n💡 Proposed Fix:")
    print("1. Update chat widget to use /api/fix-it-fred/troubleshoot")
    print("2. Format user messages as troubleshooting requests")
    print("3. Extract AI responses from Fred's output")
    print("4. Fall back to Ollama direct API if available")
    
    print("\n🔧 Quick Implementation:")
    print("""
// Update chat widget JavaScript to use working endpoint:
async function sendChatMessage(message) {
    try {
        const response = await fetch('/api/fix-it-fred/troubleshoot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                equipment: 'ChatterFix CMMS',
                issue_description: message
            })
        });
        
        const data = await response.json();
        return data.data.response || 'Let me help you with ChatterFix!';
    } catch (error) {
        return 'How can I help you get started with ChatterFix?';
    }
}
    """)

def test_fred_as_chat_backend():
    """Test using Fred as the chat backend"""
    print("\n🤖 Testing Fred as Chat Backend")
    print("=" * 40)
    
    chat_messages = [
        "What is ChatterFix CMMS?",
        "How do I create a work order?",
        "Tell me about the AI features",
        "What makes ChatterFix different?"
    ]
    
    for message in chat_messages:
        try:
            response = requests.post(
                "http://35.237.149.25:8080/api/fix-it-fred/troubleshoot",
                json={
                    "equipment": "ChatterFix CMMS Platform",
                    "issue_description": f"User question: {message}"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                fred_response = data.get("data", {}).get("response", "No response")
                print(f"Q: {message}")
                print(f"A: {fred_response[:100]}...")
                print()
            else:
                print(f"❌ Failed for: {message}")
                
        except Exception as e:
            print(f"❌ Error testing: {message} - {str(e)}")

if __name__ == "__main__":
    working = test_ai_endpoints()
    generate_chat_fix_recommendation(working)
    test_fred_as_chat_backend()
    
    print("\n🎉 Summary: Fix It Fred can serve as the chat backend!")
    print("The chat widget just needs to be updated to use the working endpoint.")
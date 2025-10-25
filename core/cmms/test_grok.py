#!/usr/bin/env python3
"""
Test script to establish Fix It Fred ↔ Grok communication
"""

import requests
import json

def test_grok_communication():
    """Test Fix It Fred communicating with Grok"""
    
    # Test 1: Check Grok status
    print("🔍 Testing Grok connection status...")
    try:
        response = requests.get("http://localhost:8006/grok/status")
        print(f"✅ Grok Status: {response.json()}")
    except Exception as e:
        print(f"❌ Grok status error: {e}")
    
    # Test 2: Simple Grok chat
    print("\n💬 Testing Grok chat...")
    try:
        payload = {
            "message": "Hello Grok! This is Fix It Fred.",
            "context": "fred_test"
        }
        response = requests.post("http://localhost:8006/grok/chat", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Grok Response: {result['response'][:200]}...")
        else:
            print(f"❌ Grok chat error: {response.text}")
    except Exception as e:
        print(f"❌ Grok chat error: {e}")
    
    # Test 3: Fred asking Grok
    print("\n🤖 Testing Fred asking Grok...")
    try:
        payload = {
            "message": "Grok, help me optimize ChatterFix CMMS performance",
            "context": "performance_optimization"
        }
        response = requests.post("http://localhost:8006/fred/ask-grok", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Fred to Grok successful!")
            print(f"📝 Grok's advice: {result['grok_response'][:300]}...")
        else:
            print(f"❌ Fred to Grok error: {response.text}")
    except Exception as e:
        print(f"❌ Fred to Grok error: {e}")

if __name__ == "__main__":
    print("🚀 Fix It Fred ↔ Grok Communication Test")
    print("=" * 50)
    test_grok_communication()
    print("\n🎉 Communication test complete!")
#!/usr/bin/env python3
import requests
import json

# Test Fix It Fred AI Service
def test_fred():
    url = "http://localhost:8005/api/chat"
    payload = {
        "message": "Hello Fix It Fred! Tell me about ChatterFix CMMS",
        "context": "maintenance", 
        "provider": "ollama"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        if response.status_code == 200:
            data = response.json()
            print(f"AI Response: {data.get('response', 'No response field')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_fred()
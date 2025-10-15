#!/usr/bin/env python3
"""Quick performance test for Ollama and Fix It Fred"""
import requests
import time
import json

def test_ollama():
    print("🧪 Testing Ollama performance...")
    start_time = time.time()
    
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama3.2:1b',
                'prompt': 'Hello, this is a quick test.',
                'stream': False
            },
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            tokens = len(data.get('response', '').split())
            tokens_per_second = tokens / elapsed if elapsed > 0 else 0
            
            print(f"✅ Ollama Response Time: {elapsed:.2f}s")
            print(f"📊 Tokens per Second: {tokens_per_second:.1f}")
            return True
        else:
            print(f"❌ Ollama Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ollama Test Failed: {e}")
        return False

def test_fix_it_fred():
    print("\n🤖 Testing Fix It Fred performance...")
    start_time = time.time()
    
    try:
        response = requests.post(
            'http://localhost:9000/api/chat',
            json={
                'message': 'Quick test - what maintenance should I do?',
                'provider': 'ollama',
                'model': 'llama3.2:1b'
            },
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Fix It Fred Response Time: {elapsed:.2f}s")
            print(f"🎯 Success: {data.get('success', False)}")
            return True
        else:
            print(f"❌ Fix It Fred Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Fix It Fred Test Failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ChatterFix AI Performance Test")
    print("=" * 40)
    
    ollama_ok = test_ollama()
    fred_ok = test_fix_it_fred()
    
    print("\n📊 SUMMARY:")
    print(f"Ollama: {'✅ HEALTHY' if ollama_ok else '❌ NEEDS ATTENTION'}")
    print(f"Fix It Fred: {'✅ HEALTHY' if fred_ok else '❌ NEEDS ATTENTION'}")
    
    if ollama_ok and fred_ok:
        print("\n🎉 All systems optimal!")
    else:
        print("\n⚠️  Some services need attention")

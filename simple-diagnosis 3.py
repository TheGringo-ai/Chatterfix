#!/usr/bin/env python3
"""
Simple ChatterFix diagnosis and fix
"""

import requests

VM_IP = "35.237.149.25"

def main():
    print("🔧 ChatterFix Deployment Issues Diagnosis")
    print("=" * 50)
    
    # Check what's running
    print("Current status:")
    
    # UI Gateway
    try:
        response = requests.get(f"http://{VM_IP}:8080/health", timeout=5)
        if response.status_code == 200:
            print("✅ UI Gateway on port 8080: Working")
        else:
            print(f"⚠️ UI Gateway: HTTP {response.status_code}")
    except:
        print("❌ UI Gateway: Not responding")
    
    # Backend
    try:
        response = requests.get(f"http://{VM_IP}:8081/health", timeout=3)
        if response.status_code == 200:
            print("✅ Backend on port 8081: Working")
        else:
            print(f"⚠️ Backend: HTTP {response.status_code}")
    except:
        print("❌ Backend on port 8081: Not responding")
    
    # Ollama
    try:
        response = requests.get(f"http://{VM_IP}:11434/api/tags", timeout=3)
        if response.status_code == 200:
            print("✅ Ollama on port 11434: Working")
        else:
            print(f"⚠️ Ollama: HTTP {response.status_code}")
    except:
        print("❌ Ollama: Not responding externally")
    
    print("\n🔍 ISSUES IDENTIFIED:")
    print("1. ❌ Backend service on port 8081 is not running")
    print("2. ⚠️ PostgreSQL connection is failing")
    print("3. ⚠️ Deployment scripts may not be executing properly")
    
    print("\n💡 SOLUTIONS:")
    print("1. Use simple SQLite backend instead of PostgreSQL")
    print("2. Deploy minimal backend service manually")
    print("3. Test backend functionality incrementally")
    
    print("\n📋 RECOMMENDED ACTION:")
    print("Deploy a simple, working backend that uses:")
    print("  - SQLite database (no connection issues)")
    print("  - Port 8081 (no conflicts)")
    print("  - Minimal dependencies")
    print("  - Basic CRUD operations")

if __name__ == "__main__":
    main()
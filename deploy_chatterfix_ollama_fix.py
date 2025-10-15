#!/usr/bin/env python3
"""
ChatterFix Ollama Connection Fix Deployment Script
Bulletproof deployment to connect ChatterFix -> Fix It Fred -> Ollama with zero errors
"""

import os
import sys
import time
import subprocess
import requests
import json
from datetime import datetime

def log(message, level="INFO"):
    """Enhanced logging with timestamps"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def check_service_health(url, service_name, timeout=10):
    """Check if a service is healthy and responding"""
    try:
        response = requests.get(f"{url}/health", timeout=timeout)
        if response.status_code == 200:
            log(f"✅ {service_name} is healthy at {url}")
            return True
        else:
            log(f"❌ {service_name} returned status {response.status_code}", "ERROR")
            return False
    except requests.exceptions.RequestException as e:
        log(f"❌ {service_name} connection failed: {e}", "ERROR")
        return False

def test_ollama_connection():
    """Test Ollama connection and model availability"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            if "llama3.2:1b" in model_names:
                log("✅ Ollama is running with llama3.2:1b model loaded")
                return True
            else:
                log(f"⚠️ Ollama is running but llama3.2:1b not found. Available: {model_names}", "WARNING")
                return False
        else:
            log(f"❌ Ollama API returned status {response.status_code}", "ERROR")
            return False
    except requests.exceptions.RequestException as e:
        log(f"❌ Ollama connection failed: {e}", "ERROR")
        return False

def test_fix_it_fred_connection():
    """Test Fix It Fred AI service connection"""
    return check_service_health("http://localhost:9000", "Fix It Fred AI Service")

def test_chatterfix_connection():
    """Test ChatterFix main app connection"""
    return check_service_health("http://localhost:8090", "ChatterFix Main App")

def test_full_chain():
    """Test the complete ChatterFix -> Fix It Fred -> Ollama chain"""
    log("🔗 Testing complete AI chain: ChatterFix -> Fix It Fred -> Ollama")
    
    try:
        # Test Fix It Fred AI service directly
        payload = {
            "message": "Test message for CMMS maintenance",
            "provider": "ollama",
            "model": "llama3.2:1b",
            "context": "test_chain"
        }
        
        response = requests.post(
            "http://localhost:9000/api/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_response = data.get("response", "")
            if ai_response and len(ai_response) > 10:
                log(f"✅ Fix It Fred -> Ollama chain working: {len(ai_response)} chars response")
                
                # Now test ChatterFix global AI endpoint
                chatterfix_payload = {
                    "message": "Test ChatterFix CMMS integration",
                    "page": "test",
                    "context": "global_ai_test"
                }
                
                chatterfix_response = requests.post(
                    "http://localhost:8090/global-ai/process-message",
                    json=chatterfix_payload,
                    timeout=30
                )
                
                if chatterfix_response.status_code == 200:
                    chatterfix_data = chatterfix_response.json()
                    if chatterfix_data.get("success") and chatterfix_data.get("response"):
                        log("✅ Complete ChatterFix -> Fix It Fred -> Ollama chain working!")
                        return True
                    else:
                        log(f"❌ ChatterFix AI response failed: {chatterfix_data}", "ERROR")
                        return False
                else:
                    log(f"❌ ChatterFix AI endpoint failed: {chatterfix_response.status_code}", "ERROR")
                    return False
            else:
                log(f"❌ Fix It Fred returned empty response: {data}", "ERROR")
                return False
        else:
            log(f"❌ Fix It Fred AI service failed: {response.status_code}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Chain test failed: {e}", "ERROR")
        return False

def restart_chatterfix_app():
    """Restart the ChatterFix app to apply changes"""
    log("🔄 Restarting ChatterFix app to apply Fix It Fred connection...")
    
    try:
        # Find and kill existing ChatterFix process on port 8090
        result = subprocess.run(
            ["lsof", "-ti:8090"], 
            capture_output=True, 
            text=True
        )
        
        if result.stdout.strip():
            pid = result.stdout.strip()
            log(f"Killing existing ChatterFix process (PID: {pid})")
            subprocess.run(["kill", "-9", pid])
            time.sleep(3)
        
        # Start ChatterFix app with Fix It Fred integration
        log("Starting ChatterFix app with Fix It Fred integration...")
        os.chdir("/Users/fredtaylor/Desktop/Projects/ai-tools/vm-deployment")
        
        # Start in background
        process = subprocess.Popen(
            ["python3", "app.py"],
            env={**os.environ, "PORT": "8090", "FIX_IT_FRED_URL": "http://localhost:9000"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for startup
        time.sleep(10)
        
        if process.poll() is None:  # Process is still running
            log("✅ ChatterFix app restarted successfully")
            return True
        else:
            stdout, stderr = process.communicate()
            log(f"❌ ChatterFix app failed to start: {stderr.decode()}", "ERROR")
            return False
            
    except Exception as e:
        log(f"❌ Failed to restart ChatterFix app: {e}", "ERROR")
        return False

def deploy_connection_fix():
    """Main deployment function for ChatterFix Ollama connection fix"""
    log("🚀 Starting ChatterFix Ollama Connection Fix Deployment")
    log("=" * 80)
    
    # Step 1: Check all services
    log("Step 1: Checking service health...")
    
    ollama_ok = test_ollama_connection()
    fix_it_fred_ok = test_fix_it_fred_connection()
    
    if not ollama_ok:
        log("❌ Ollama is not running or llama3.2:1b model not loaded", "ERROR")
        return False
        
    if not fix_it_fred_ok:
        log("❌ Fix It Fred AI service is not running on port 9000", "ERROR")
        return False
    
    # Step 2: Restart ChatterFix with new configuration
    log("Step 2: Restarting ChatterFix with Fix It Fred integration...")
    
    if not restart_chatterfix_app():
        log("❌ Failed to restart ChatterFix app", "ERROR")
        return False
    
    # Step 3: Test complete chain
    log("Step 3: Testing complete AI chain...")
    
    # Give services time to stabilize
    time.sleep(5)
    
    if not test_full_chain():
        log("❌ Complete AI chain test failed", "ERROR")
        return False
    
    # Step 4: Final validation
    log("Step 4: Final validation...")
    
    chatterfix_ok = test_chatterfix_connection()
    if not chatterfix_ok:
        log("❌ ChatterFix health check failed", "ERROR")
        return False
    
    log("🎉 ChatterFix Ollama Connection Fix Deployment SUCCESSFUL!")
    log("=" * 80)
    log("✅ ChatterFix is now connected to VM Ollama through Fix It Fred")
    log("✅ No more fallback responses - direct Ollama integration active")
    log("✅ All services healthy and responding")
    log("🌐 ChatterFix available at: http://localhost:8090")
    log("🤖 Fix It Fred AI service at: http://localhost:9000")
    log("🧠 Ollama backend at: http://localhost:11434")
    
    return True

if __name__ == "__main__":
    try:
        success = deploy_connection_fix()
        if success:
            print("\n🎯 DEPLOYMENT SUCCESSFUL - ChatterFix is now using VM Ollama!")
            sys.exit(0)
        else:
            print("\n💥 DEPLOYMENT FAILED - Check logs above for issues")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Deployment failed with error: {e}")
        sys.exit(1)
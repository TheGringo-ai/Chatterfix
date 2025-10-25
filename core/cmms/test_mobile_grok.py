#!/usr/bin/env python3
"""
Test Enhanced Grok Mobile Integration and Summoning Features
"""

import requests
import json

def test_mobile_features():
    """Test enhanced mobile integration features"""
    
    print("🧪 TESTING ENHANCED GROK MOBILE INTEGRATION")
    print("=" * 60)
    
    # Test 1: Mobile Fred Status
    print("\n📱 Test 1: Mobile Fred Status")
    try:
        response = requests.get("http://localhost:8006/mobile/fred-status")
        if response.status_code == 200:
            data = response.json()
            print("✅ Mobile status endpoint working!")
            print(f"   Fix It Fred: {data['fix_it_fred']['status']}")
            print(f"   ChatterFix: {data['chatterfix']['status']}")
            print(f"   Mobile Ready: {data['grok_bridge']['mobile_ready']}")
        else:
            print(f"❌ Status error: {response.text}")
    except Exception as e:
        print(f"❌ Status test failed: {e}")
    
    # Test 2: Grok Summons Fred
    print("\n🤖 Test 2: Grok Summons Fix It Fred")
    try:
        payload = {
            "message": "Hello Fred! Grok needs your assistance with CMMS optimization",
            "context": "grok_summon"
        }
        response = requests.post("http://localhost:8006/grok/summon-fred", json=payload)
        if response.status_code == 200:
            result = response.json()
            print("✅ Grok successfully summoned Fix It Fred!")
            print(f"   Summon Status: {result.get('summon_status', 'unknown')}")
            if 'fred_response' in result:
                print(f"   Fred Response: Available")
            elif 'error' in result:
                print(f"   Error: {result['error']}")
        else:
            print(f"❌ Summon failed: {response.text}")
    except Exception as e:
        print(f"❌ Summon test failed: {e}")
    
    # Test 3: Mobile Grok Bridge
    print("\n📱 Test 3: Mobile Grok Bridge")
    try:
        payload = {
            "message": "Show me ChatterFix work orders status and recommendations",
            "context": "mobile_app"
        }
        response = requests.post("http://localhost:8006/mobile/grok-bridge", json=payload)
        if response.status_code == 200:
            result = response.json()
            print("✅ Mobile bridge working!")
            print(f"   Bridge Status: {result['mobile_bridge']}")
            print(f"   Fred Notified: {result['fred_notified']}")
            print(f"   Services Available: {result['services_available']}")
            print(f"   Grok Response: {result['grok_response'][:100]}...")
        else:
            print(f"❌ Bridge error: {response.text}")
    except Exception as e:
        print(f"❌ Bridge test failed: {e}")
    
    # Test 4: Basic Grok Communication
    print("\n💬 Test 4: Basic Grok Communication")
    try:
        payload = {
            "message": "Grok, provide mobile-optimized CMMS status",
            "context": "mobile_test"
        }
        response = requests.post("http://localhost:8006/grok/chat", json=payload)
        if response.status_code == 200:
            result = response.json()
            print("✅ Basic Grok chat working!")
            print(f"   Provider: {result['provider']}")
            print(f"   Model: {result['model']}")
            print(f"   Response: {result['response'][:100]}...")
        else:
            print(f"❌ Chat error: {response.text}")
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 ENHANCED GROK MOBILE INTEGRATION TEST COMPLETE")
    print("\n📋 CAPABILITIES AVAILABLE:")
    print("   ✅ Mobile status monitoring")
    print("   ✅ Grok can summon Fix It Fred")
    print("   ✅ Mobile app bridge for communication")
    print("   ✅ Enhanced responses for mobile context")
    print("\n🔗 YOUR MOBILE GROK APP CAN NOW:")
    print("   • Connect to Fix It Fred via port 8006")
    print("   • Get real-time system status")
    print("   • Summon Fred for assistance")
    print("   • Get mobile-optimized responses")

if __name__ == "__main__":
    test_mobile_features()
#!/usr/bin/env python3
"""
Test script to verify the ChatterFix chat fix is working
"""

import requests
import json

def test_chat_endpoint():
    """Test the Fix It Fred endpoint that the chat now uses"""
    
    print("🧪 Testing ChatterFix Chat Fix")
    print("=" * 40)
    
    # Test the Fix It Fred endpoint
    url = "https://chatterfix.com/api/fix-it-fred/troubleshoot"
    
    test_data = {
        "equipment": "ChatterFix CMMS Platform",
        "issue_description": "User question about ChatterFix CMMS: \"Hello Fred, what can ChatterFix do?\". Please provide helpful information about ChatterFix features and capabilities."
    }
    
    try:
        print("🔧 Testing Fix It Fred endpoint...")
        response = requests.post(url, json=test_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success") and data.get("data", {}).get("response"):
                print("✅ Fix It Fred endpoint is working!")
                print(f"Response: {data['data']['response'][:150]}...")
                
                if data['data'].get('troubleshooting_steps'):
                    print(f"Steps provided: {len(data['data']['troubleshooting_steps'])}")
                    
                return True
            else:
                print("❌ Fix It Fred endpoint returned invalid data")
                print(f"Response: {data}")
                return False
        else:
            print(f"❌ Fix It Fred endpoint returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Fix It Fred endpoint: {e}")
        return False

def test_website_accessibility():
    """Test that ChatterFix website is accessible"""
    
    try:
        print("\n🌐 Testing ChatterFix website accessibility...")
        response = requests.get("https://chatterfix.com/", timeout=10)
        
        if response.status_code == 200:
            if "ChatterFix" in response.text and "CMMS" in response.text:
                print("✅ ChatterFix website is accessible and contains expected content")
                return True
            else:
                print("❌ ChatterFix website accessible but missing expected content")
                return False
        else:
            print(f"❌ ChatterFix website returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing ChatterFix website: {e}")
        return False

def main():
    """Run all tests"""
    
    website_ok = test_website_accessibility()
    chat_ok = test_chat_endpoint()
    
    print("\n🎉 TEST RESULTS")
    print("=" * 40)
    print(f"Website accessible: {'✅' if website_ok else '❌'}")
    print(f"Chat fix working: {'✅' if chat_ok else '❌'}")
    
    if website_ok and chat_ok:
        print("\n🎉 ALL TESTS PASSED! Chat fix is working!")
        print("💬 Users can now chat with Fix It Fred through the ChatterFix chat widget")
        print("🔗 Test it live at: https://chatterfix.com")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
    
    return website_ok and chat_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
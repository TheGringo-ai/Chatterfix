#!/usr/bin/env python3
"""
Fix It Fred AI Integration Injector for ChatterFix
Automatically injects the powerful Fix It Fred AI into ChatterFix CMMS
"""

import requests
import time
import json
from pathlib import Path

def inject_fred_ai():
    """Inject Fix It Fred AI into ChatterFix"""
    print("🚀 Starting Fix It Fred AI injection into ChatterFix...")
    
    # Read the integration script
    integration_file = Path(__file__).parent / "fix_it_fred_chatterfix_integration.js"
    
    if not integration_file.exists():
        print("❌ Integration script not found!")
        return False
    
    with open(integration_file, 'r') as f:
        integration_script = f.read()
    
    # Test ChatterFix connectivity
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ ChatterFix is running and healthy")
        else:
            print(f"⚠️ ChatterFix responded with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to ChatterFix: {e}")
        return False
    
    # Create injection payload for ChatterFix
    injection_payload = {
        "script": integration_script,
        "name": "Fix It Fred AI Integration",
        "version": "3.0",
        "description": "Advanced AI assistant for maintenance management",
        "features": [
            "Intelligent equipment troubleshooting",
            "Predictive maintenance planning", 
            "Safety protocol guidance",
            "Parts identification and management",
            "Real-time technical support",
            "ChatterFix CMMS optimization"
        ]
    }
    
    print("🔧 Fix It Fred AI Features:")
    for feature in injection_payload["features"]:
        print(f"  • {feature}")
    
    # Create a simple HTML file to manually inject
    html_injection = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Fix It Fred AI - ChatterFix Integration</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; color: #006fee; margin-bottom: 30px; }}
        .code-block {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 6px; padding: 20px; margin: 20px 0; overflow-x: auto; }}
        .btn {{ background: linear-gradient(135deg, #006fee, #4285f4); color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; }}
        .btn:hover {{ transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0, 111, 238, 0.3); }}
        .feature-list {{ background: rgba(0, 111, 238, 0.05); padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .feature-list li {{ margin: 8px 0; }}
        .instructions {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Fix It Fred AI Integration</h1>
            <h2>Advanced AI Assistant for ChatterFix CMMS</h2>
        </div>
        
        <div class="feature-list">
            <h3>🔧 AI Capabilities:</h3>
            <ul>
                {"".join(f"<li>{feature}</li>" for feature in injection_payload["features"])}
            </ul>
        </div>
        
        <div class="instructions">
            <h3>📋 Integration Instructions:</h3>
            <ol>
                <li>Open ChatterFix in your browser: <a href="http://localhost:8000" target="_blank">http://localhost:8000</a></li>
                <li>Open browser developer tools (F12)</li>
                <li>Go to the Console tab</li>
                <li>Copy and paste the script below</li>
                <li>Press Enter to activate Fix It Fred AI</li>
            </ol>
        </div>
        
        <h3>🚀 Integration Script:</h3>
        <div class="code-block">
            <button class="btn" onclick="copyToClipboard()">📋 Copy Script</button>
            <pre id="integration-script">{integration_script.replace('<', '&lt;').replace('>', '&gt;')}</pre>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <button class="btn" onclick="window.open('http://localhost:8000', '_blank')">🚀 Open ChatterFix</button>
            <button class="btn" onclick="testAI()" style="margin-left: 10px;">🧪 Test AI Connection</button>
        </div>
        
        <div id="test-results" style="margin-top: 20px;"></div>
    </div>
    
    <script>
        function copyToClipboard() {{
            const script = document.getElementById('integration-script').textContent;
            navigator.clipboard.writeText(script).then(function() {{
                alert('✅ Fix It Fred AI script copied to clipboard!\\n\\nNow:\\n1. Open ChatterFix\\n2. Open developer tools (F12)\\n3. Paste in console\\n4. Press Enter');
            }});
        }}
        
        async function testAI() {{
            const resultDiv = document.getElementById('test-results');
            resultDiv.innerHTML = '<p>🧪 Testing AI connections...</p>';
            
            try {{
                // Test Fix It Fred AI
                const fredResponse = await fetch('http://localhost:8001/health');
                const fredData = await fredResponse.json();
                
                // Test ChatterFix
                const chatterResponse = await fetch('http://localhost:8000/health');
                const chatterData = await chatterResponse.json();
                
                resultDiv.innerHTML = `
                    <div style="background: #d4edda; border: 1px solid #c3e6cb; padding: 15px; border-radius: 8px;">
                        <h4>✅ Connection Test Results:</h4>
                        <p><strong>Fix It Fred AI:</strong> ${{fredData.status}} - ${{fredData.service || 'Ready'}}</p>
                        <p><strong>ChatterFix CMMS:</strong> ${{chatterData.status}} - ${{chatterData.gateway || 'Platform Gateway'}}</p>
                        <p><strong>Status:</strong> Ready for integration! 🚀</p>
                    </div>
                `;
            }} catch (error) {{
                resultDiv.innerHTML = `
                    <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 8px;">
                        <h4>⚠️ Connection Issue:</h4>
                        <p>Error: ${{error.message}}</p>
                        <p>Please ensure both ChatterFix and Fix It Fred AI services are running.</p>
                    </div>
                `;
            }}
        }}
        
        // Auto-test on page load
        window.onload = function() {{
            setTimeout(testAI, 1000);
        }};
    </script>
</body>
</html>
"""
    
    # Write HTML injection file
    html_file = Path(__file__).parent / "fix_it_fred_integration.html"
    with open(html_file, 'w') as f:
        f.write(html_injection)
    
    print("✅ Integration files created successfully!")
    print(f"🌐 Open this file in your browser: {html_file}")
    print("📋 Or run the integration script directly in ChatterFix console")
    
    # Test AI services
    print("\n🧪 Testing AI service connections...")
    
    try:
        # Test Fix It Fred AI
        fred_response = requests.get('http://localhost:8005/health', timeout=3)
        if fred_response.status_code == 200:
            fred_data = fred_response.json()
            print(f"✅ Fix It Fred AI: {fred_data.get('status', 'unknown')} - {fred_data.get('service', 'AI Service')}")
        else:
            print(f"⚠️ Fix It Fred AI: HTTP {fred_response.status_code}")
    except Exception as e:
        print(f"❌ Fix It Fred AI: {e}")
    
    try:
        # Test AI Team
        team_response = requests.get('http://localhost:8008/health', timeout=3)
        if team_response.status_code == 200:
            team_data = team_response.json()
            print(f"✅ AI Development Team: {team_data.get('status', 'unknown')} - {team_data.get('service', 'AI Team')}")
        else:
            print(f"⚠️ AI Development Team: HTTP {team_response.status_code}")
    except Exception as e:
        print(f"❌ AI Development Team: {e}")
    
    print("\n🎯 Fix It Fred AI Integration Ready!")
    print("💡 This AI assistant provides:")
    print("   • Real-time equipment troubleshooting")
    print("   • Predictive maintenance recommendations") 
    print("   • Safety protocol guidance")
    print("   • Parts identification and sourcing")
    print("   • Integration with ChatterFix CMMS features")
    print("   • Multi-provider AI backend (OpenAI, Claude, Gemini, Local)")
    
    return True

if __name__ == "__main__":
    inject_fred_ai()
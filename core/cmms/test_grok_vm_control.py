#!/usr/bin/env python3
"""
Test Grok VM Control and File Management Capabilities
"""

import requests
import json

def test_grok_vm_control():
    """Test Grok's VM control and file management with approval system"""
    
    print("🏗️ TESTING GROK VM CONTROL & FILE MANAGEMENT")
    print("=" * 60)
    
    # Test 1: VM Restart Suggestion
    print("\n🔄 Test 1: VM Restart Suggestion")
    try:
        payload = {
            "message": "VM seems slow, restart it to improve performance",
            "context": "performance_optimization"
        }
        response = requests.post("http://localhost:8007/grok/vm/suggest-restart", json=payload)
        if response.status_code == 200:
            data = response.json()
            print("✅ VM restart suggestion created!")
            print(f"   Change ID: {data['change_id']}")
            print(f"   Risk Level: {data['risk_level']}")
            print(f"   Warning: {data['warning']}")
            print(f"   Approval Required: {data['approval_required']}")
            vm_restart_id = data['change_id']
        else:
            print(f"❌ VM restart suggestion error: {response.text}")
            vm_restart_id = None
    except Exception as e:
        print(f"❌ VM restart test failed: {e}")
        vm_restart_id = None
    
    # Test 2: File Edit Suggestion
    print("\n📝 Test 2: File Edit Suggestion")
    try:
        payload = {
            "file_path": "/home/yoyofred/test_grok_edit.txt",
            "file_content": "# Grok Test File\\nThis file was suggested by Grok AI for editing\\nTimestamp: $(date)\\n",
            "reason": "Create test file to verify Grok file editing capabilities",
            "risk_level": "Low",
            "backup": True
        }
        response = requests.post("http://localhost:8007/grok/vm/suggest-file-edit", json=payload)
        if response.status_code == 200:
            data = response.json()
            print("✅ File edit suggestion created!")
            print(f"   Change ID: {data['change_id']}")
            print(f"   File Path: {data['file_path']}")
            print(f"   Risk Level: {data['risk_level']}")
            print(f"   Backup Enabled: {data['backup_enabled']}")
            file_edit_id = data['change_id']
        else:
            print(f"❌ File edit suggestion error: {response.text}")
            file_edit_id = None
    except Exception as e:
        print(f"❌ File edit test failed: {e}")
        file_edit_id = None
    
    # Test 3: Safe Command Suggestion
    print("\n💻 Test 3: Safe VM Command Suggestion")
    try:
        payload = {
            "command": "df -h && free -h && uptime",
            "reason": "Check system resources and uptime for monitoring",
        }
        response = requests.post("http://localhost:8007/grok/vm/suggest-command", json=payload)
        if response.status_code == 200:
            data = response.json()
            print("✅ Safe command suggestion created!")
            print(f"   Change ID: {data['change_id']}")
            print(f"   Command: {data['command']}")
            print(f"   Risk Level: {data['risk_level']}")
            if 'risk_assessment' in data:
                assessment = data['risk_assessment']
                print(f"   Risk Assessment: {assessment['level']}")
                if assessment['warnings']:
                    for warning in assessment['warnings']:
                        print(f"   {warning}")
            safe_command_id = data['change_id']
        else:
            print(f"❌ Safe command suggestion error: {response.text}")
            safe_command_id = None
    except Exception as e:
        print(f"❌ Safe command test failed: {e}")
        safe_command_id = None
    
    # Test 4: Risky Command Suggestion (should have high risk)
    print("\n⚠️ Test 4: Risky VM Command Suggestion")
    try:
        payload = {
            "command": "sudo systemctl restart nginx",
            "reason": "Restart nginx service to apply configuration changes",
        }
        response = requests.post("http://localhost:8007/grok/vm/suggest-command", json=payload)
        if response.status_code == 200:
            data = response.json()
            print("✅ Risky command suggestion created!")
            print(f"   Change ID: {data['change_id']}")
            print(f"   Command: {data['command']}")
            print(f"   Risk Level: {data['risk_level']}")
            if 'risk_assessment' in data:
                assessment = data['risk_assessment']
                print(f"   Risk Assessment: {assessment['level']}")
                if assessment['warnings']:
                    for warning in assessment['warnings']:
                        print(f"   {warning}")
            risky_command_id = data['change_id']
        else:
            print(f"❌ Risky command suggestion error: {response.text}")
            risky_command_id = None
    except Exception as e:
        print(f"❌ Risky command test failed: {e}")
        risky_command_id = None
    
    # Test 5: Critical Command Detection
    print("\n🚨 Test 5: Critical Command Detection")
    try:
        payload = {
            "command": "sudo rm -rf /tmp/test_files",
            "reason": "Clean up test files (should be flagged as critical)",
        }
        response = requests.post("http://localhost:8007/grok/vm/suggest-command", json=payload)
        if response.status_code == 200:
            data = response.json()
            print("✅ Critical command suggestion created!")
            print(f"   Change ID: {data['change_id']}")
            print(f"   Command: {data['command']}")
            print(f"   Risk Level: {data['risk_level']}")
            if 'risk_assessment' in data:
                assessment = data['risk_assessment']
                print(f"   Risk Assessment: {assessment['level']}")
                if assessment['warnings']:
                    for warning in assessment['warnings']:
                        print(f"   {warning}")
            critical_command_id = data['change_id']
        else:
            print(f"❌ Critical command suggestion error: {response.text}")
            critical_command_id = None
    except Exception as e:
        print(f"❌ Critical command test failed: {e}")
        critical_command_id = None
    
    # Test 6: Check All Pending Changes
    print("\n📋 Test 6: Review All Pending Changes")
    try:
        response = requests.get("http://localhost:8007/grok/infrastructure/pending-changes")
        if response.status_code == 200:
            data = response.json()
            print("✅ Pending changes retrieved!")
            print(f"   Total Pending: {data.get('total_pending', 0)}")
            
            if data.get('pending_changes'):
                print("\\n   📝 Pending Changes Summary:")
                for change_id, change in data['pending_changes'].items():
                    action = change.get('action', 'unknown')
                    risk = change.get('risk_level', 'unknown')
                    print(f"     - {change_id}: {action} (Risk: {risk})")
                    if action == 'edit_file':
                        print(f"       File: {change.get('parameters', {}).get('file_path', 'unknown')}")
                    elif action in ['run_vm_command']:
                        print(f"       Command: {change.get('parameters', {}).get('command', 'unknown')}")
        else:
            print(f"❌ Pending changes error: {response.text}")
    except Exception as e:
        print(f"❌ Pending changes test failed: {e}")
    
    print("\\n" + "=" * 60)
    print("🎯 GROK VM CONTROL & FILE MANAGEMENT TEST COMPLETE")
    
    print("\\n📋 GROK CAN NOW SUGGEST:")
    print("   ✅ VM restart/start/stop operations")
    print("   ✅ File editing with automatic backups")
    print("   ✅ Command execution with risk assessment")
    print("   ✅ Smart risk analysis (Low/Medium/High/Critical)")
    print("   ✅ All changes require your approval")
    
    print("\\n🔐 SECURITY FEATURES:")
    print("   ✅ Automatic file backups before editing")
    print("   ✅ Command risk assessment and warnings")
    print("   ✅ Critical command detection")
    print("   ✅ All VM operations require approval")
    print("   ✅ Audit trail of all suggestions")
    
    print("\\n🤖 WHEN YOUR VM CRASHES, GROK CAN:")
    print("   • Detect the VM is down via monitoring")
    print("   • Suggest restarting the VM")
    print("   • Wait for your approval")
    print("   • Execute the restart remotely")
    print("   • Verify the VM is back online")
    print("   • Edit configuration files if needed")
    print("   • Run diagnostic commands")
    
    print("\\n⚡ EXAMPLE GROK CAPABILITIES:")
    print("   'VM crashed, restart it' → Suggests VM restart")
    print("   'Fix config file' → Suggests file edit with backup")
    print("   'Check disk space' → Suggests df -h command")
    print("   'Restart nginx' → Suggests service restart (flagged risky)")
    
    print("\\n🎊 GROK IS NOW YOUR REMOTE VM ADMIN WITH APPROVAL!")

if __name__ == "__main__":
    test_grok_vm_control()
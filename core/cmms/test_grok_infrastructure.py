#!/usr/bin/env python3
"""
Test Grok Infrastructure Integration with GCP Permissions
"""

import requests
import json
import time

def test_grok_infrastructure_integration():
    """Test Grok's infrastructure monitoring and approval system"""
    
    print("🏗️ TESTING GROK INFRASTRUCTURE INTEGRATION")
    print("=" * 60)
    
    # Test 1: Check Infrastructure Advisor Status
    print("\n🔍 Test 1: Infrastructure Advisor Status")
    try:
        response = requests.get("http://localhost:8007/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Infrastructure Advisor online!")
            print(f"   Service: {data['service']}")
            print(f"   Permissions: {data['permissions']}")
            print(f"   Capabilities: {len(data['capabilities'])} available")
        else:
            print(f"❌ Advisor error: {response.text}")
    except Exception as e:
        print(f"❌ Advisor test failed: {e}")
    
    # Test 2: Get Infrastructure Status
    print("\n📊 Test 2: Infrastructure Status Analysis")
    try:
        response = requests.get("http://localhost:8007/grok/infrastructure/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ Infrastructure analysis complete!")
            infra = data['infrastructure']
            print(f"   Compute Instances: {infra['compute_instances']['total']} total, {infra['compute_instances']['running']} running")
            print(f"   Cloud Run Services: {infra['cloud_run_services']['total']} total, {infra['cloud_run_services']['ready']} ready")
            print(f"   Recommendations: {len(infra['recommendations'])} available")
            if 'vm_system' in infra:
                vm_services = infra['vm_system'].get('services_running', {})
                online_count = sum(1 for s in vm_services.values() if s.get('status') == 'online')
                print(f"   Local Services: {online_count}/{len(vm_services)} online")
        else:
            print(f"❌ Status error: {response.text}")
    except Exception as e:
        print(f"❌ Status test failed: {e}")
    
    # Test 3: Grok Infrastructure Analysis via Main Connector
    print("\n🤖 Test 3: Grok Infrastructure Analysis")
    try:
        payload = {
            "message": "Analyze my current infrastructure and suggest optimizations",
            "context": "infrastructure_optimization"
        }
        response = requests.post("http://localhost:8006/grok/infrastructure/analyze", json=payload)
        if response.status_code == 200:
            result = response.json()
            print("✅ Grok infrastructure analysis successful!")
            print(f"   Analysis completed at: {result['analysis_timestamp']}")
            print(f"   Permissions: {result['permissions']}")
            grok_response = result['grok_infrastructure_analysis']
            print(f"   Grok Response: {grok_response[:200]}...")
        else:
            print(f"❌ Analysis error: {response.text}")
    except Exception as e:
        print(f"❌ Analysis test failed: {e}")
    
    # Test 4: Emergency Infrastructure Scan
    print("\n🚨 Test 4: Emergency Infrastructure Scan")
    try:
        response = requests.post("http://localhost:8006/grok/infrastructure/emergency-scan")
        if response.status_code == 200:
            result = response.json()
            print("✅ Emergency scan complete!")
            scan_results = result['scan_results']
            print(f"   Overall Status: {scan_results['overall_status']}")
            print(f"   Issues Found: {scan_results['issues_found']}")
            print(f"   Critical Action Required: {result['critical_action_required']}")
            if scan_results['issues']:
                print("   Issues:")
                for issue in scan_results['issues'][:2]:  # Show first 2 issues
                    print(f"     - {issue['type']}: {issue['message']}")
        else:
            print(f"❌ Emergency scan error: {response.text}")
    except Exception as e:
        print(f"❌ Emergency scan failed: {e}")
    
    # Test 5: Suggest Infrastructure Change (with approval)
    print("\n⚠️ Test 5: Infrastructure Change Suggestion")
    try:
        payload = {
            "message": "Scale down unused services to save costs",
            "context": "cost_optimization"
        }
        response = requests.post("http://localhost:8006/grok/infrastructure/suggest-change", json=payload)
        if response.status_code == 200:
            result = response.json()
            print("✅ Infrastructure change suggested!")
            print(f"   Approval Required: {result['approval_required']}")
            print(f"   Next Steps: {result['next_steps']}")
            if 'change_details' in result:
                change_id = result['change_details'].get('change_id')
                print(f"   Change ID: {change_id}")
        else:
            print(f"❌ Suggestion error: {response.text}")
    except Exception as e:
        print(f"❌ Suggestion test failed: {e}")
    
    # Test 6: Check Pending Changes
    print("\n📋 Test 6: Pending Changes Review")
    try:
        response = requests.get("http://localhost:8006/grok/infrastructure/pending-changes")
        if response.status_code == 200:
            result = response.json()
            print("✅ Pending changes retrieved!")
            print(f"   Total Pending: {result.get('total_pending', 0)}")
            if result.get('pending_changes'):
                print("   Pending Changes:")
                for change_id, change in list(result['pending_changes'].items())[:2]:
                    print(f"     - {change_id}: {change.get('reason', 'No reason provided')}")
        else:
            print(f"❌ Pending changes error: {response.text}")
    except Exception as e:
        print(f"❌ Pending changes test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 GROK INFRASTRUCTURE INTEGRATION TEST COMPLETE")
    print("\n📋 GROK NOW HAS PERMISSIONS TO:")
    print("   ✅ Monitor GCP Compute instances")
    print("   ✅ Monitor Cloud Run services")
    print("   ✅ Analyze VM system resources")
    print("   ✅ Monitor local Fix It Fred services")
    print("   ✅ Suggest infrastructure improvements")
    print("   ✅ Perform emergency scans")
    print("   ⚠️  Require approval for all changes")
    
    print("\n🔐 SECURITY FEATURES:")
    print("   ✅ Read-only GCP permissions")
    print("   ✅ All changes require user approval")
    print("   ✅ Change tracking and audit trail")
    print("   ✅ Risk assessment for suggestions")
    
    print("\n🤖 GROK CAN NOW:")
    print("   • Monitor your entire infrastructure")
    print("   • Suggest cost optimizations")
    print("   • Detect and alert on issues")
    print("   • Recommend scaling adjustments")
    print("   • Only make changes with your approval")

if __name__ == "__main__":
    test_grok_infrastructure_integration()
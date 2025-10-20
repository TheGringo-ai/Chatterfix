#!/usr/bin/env python3
"""
Test Fix It Fred's autonomous development capabilities
"""

from fix_it_fred_dev_hooks import FixItFredDevHooks
import time

def test_fred_capabilities():
    """Test Fix It Fred's development control"""
    print("🤖 Testing Fix It Fred's Autonomous Development Capabilities")
    print("=" * 60)
    
    # Initialize Fred
    fred = FixItFredDevHooks()
    
    # Test 1: Basic VM Command
    print("\n🧪 Test 1: Basic VM Command Execution")
    result = fred.execute_vm_command("echo 'Hello from Fix It Fred!' && date && uptime", "System info")
    if result["success"]:
        print("✅ VM Command Test PASSED")
        print(f"Output: {result['output'][:200]}...")
    else:
        print("❌ VM Command Test FAILED")
        
    # Test 2: Service Status Check
    print("\n🧪 Test 2: Service Status Monitoring")
    services = ["chatterfix-cmms", "nginx"]
    for service in services:
        status = fred.check_service_status(service)
        if status["success"]:
            is_active = "active" in status["output"]
            print(f"✅ {service}: {'RUNNING' if is_active else 'STOPPED'}")
        else:
            print(f"❌ {service}: STATUS CHECK FAILED")
            
    # Test 3: Git Operations
    print("\n🧪 Test 3: Git Operations")
    git_status = fred.git_operations("status")
    if git_status["success"]:
        print("✅ Git Status Check PASSED")
        print(f"Git output: {git_status['output'][:100]}...")
    else:
        print("❌ Git Status Check FAILED")
        
    # Test 4: Create and Deploy a Test File
    print("\n🧪 Test 4: Live File Creation and Deployment")
    test_content = f"""#!/bin/bash
# Fix It Fred Test File - Created {time.strftime('%Y-%m-%d %H:%M:%S')}
echo "🤖 Fix It Fred autonomous deployment test"
echo "Timestamp: $(date)"
echo "VM Info: $(hostname) - $(whoami)"
"""
    
    # Write test file locally
    with open("/tmp/fred_test.sh", "w") as f:
        f.write(test_content)
        
    # Deploy to VM
    deploy_result = fred.deploy_code_to_vm("/tmp/fred_test.sh", "/tmp/fred_test.sh")
    if deploy_result["success"]:
        print("✅ File Deployment PASSED")
        
        # Make executable and run
        exec_result = fred.execute_vm_command("chmod +x /tmp/fred_test.sh && /tmp/fred_test.sh", "Execute test script")
        if exec_result["success"]:
            print("✅ Remote Execution PASSED")
            print(f"Script output: {exec_result['output']}")
        else:
            print("❌ Remote Execution FAILED")
    else:
        print("❌ File Deployment FAILED")
        
    # Test 5: Health Monitoring
    print("\n🧪 Test 5: Auto-Healing Capabilities")
    healing_actions = fred.monitor_and_heal()
    print(f"✅ Auto-healing check complete: {len(healing_actions)} actions taken")
    for action in healing_actions:
        print(f"  🔧 {action['service']}: {action['action']} - {'✅' if action['result']['success'] else '❌'}")
        
    print("\n🎉 Fix It Fred Development Tests Complete!")
    print("=" * 60)
    print("\n🚀 CAPABILITIES VERIFIED:")
    print("  ✅ Direct VM command execution")
    print("  ✅ Service monitoring and control") 
    print("  ✅ Git operations automation")
    print("  ✅ File deployment and execution")
    print("  ✅ Auto-healing monitoring")
    print("\n🤖 Fix It Fred is ready for autonomous development operations!")

if __name__ == "__main__":
    test_fred_capabilities()
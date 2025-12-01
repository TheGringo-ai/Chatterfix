#!/usr/bin/env python3
"""
Test script to validate the MCP server functionality
"""

import asyncio
import json
from mcp_server import (
    validate_feature_consistency, 
    check_purchasing_data_consistency,
    comprehensive_showcase_validation,
    pre_deployment_validation
)

async def test_validation_tools():
    """Test all validation tools"""
    print("🚀 Testing ChatterFix MCP Validation Tools\n")
    
    # Test 1: Feature consistency validation
    print("1️⃣  Testing feature consistency...")
    try:
        result = await validate_feature_consistency("all")
        print(f"   ✅ Feature validation: {result.get('validation_results', {}).get('purchasing', {}).get('status', 'Unknown')}")
    except Exception as e:
        print(f"   ❌ Feature validation failed: {e}")
    
    # Test 2: Purchasing data consistency
    print("\n2️⃣  Testing purchasing data consistency...")
    try:
        result = await check_purchasing_data_consistency()
        print(f"   ✅ Purchasing consistency: {result.get('status', 'Unknown')}")
        print(f"   📊 Live data access: {result.get('live_data_access', False)}")
    except Exception as e:
        print(f"   ❌ Purchasing validation failed: {e}")
    
    # Test 3: Comprehensive showcase validation
    print("\n3️⃣  Testing comprehensive showcase validation...")
    try:
        result = await comprehensive_showcase_validation(include_performance=True)
        print(f"   ✅ Showcase readiness: {result.get('showcase_readiness', {}).get('overall_status', 'Unknown')}")
        print(f"   📈 Customer confidence: {result.get('customer_impact', {}).get('authentic_experience', False)}")
    except Exception as e:
        print(f"   ❌ Showcase validation failed: {e}")
    
    # Test 4: Pre-deployment validation
    print("\n4️⃣  Testing pre-deployment validation...")
    try:
        result = await pre_deployment_validation()
        print(f"   ✅ Deployment status: {result.get('overall_status', 'Unknown')}")
        blockers = result.get('blockers', [])
        if blockers:
            print(f"   ⚠️  Blockers found: {blockers}")
        else:
            print("   🎉 No blockers - ready to deploy!")
    except Exception as e:
        print(f"   ❌ Deployment validation failed: {e}")
    
    print("\n✅ MCP validation testing complete!")

if __name__ == "__main__":
    asyncio.run(test_validation_tools())
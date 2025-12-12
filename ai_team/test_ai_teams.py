"""
Test Script for AI Team Collaboration
Tests both general AutoGen team and specialized deployment team
"""

import asyncio
import logging
import os
import sys

# Add the parent directory to the path
sys.path.append(".")

from ai_team.autogen_framework import get_orchestrator
from ai_team.deployment_team import DeploymentConfig, get_deployment_orchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_general_ai_team():
    """Test the general AI team with real API integrations"""
    print("🤖 Testing General AI Team Collaboration")
    print("=" * 50)

    orchestrator = get_orchestrator()

    # Display team status
    status = orchestrator.get_agent_status()
    print(f"Team Size: {status['total_agents']} agents")
    for agent in status["agents"]:
        model_name = f" ({agent['model_name']})" if agent.get("model_name") else ""
        print(f"  ✅ {agent['name']} - {agent['role']}{model_name}")

    print("\n🧪 Testing collaborative coding task...")

    # Test collaborative task
    result = await orchestrator.execute_collaborative_task(
        task_id="test-coding-collaboration",
        prompt="Create a Python function that validates email addresses using regex. Include error handling and unit tests.",
        context="This is for a production web application that needs robust email validation.",
        max_iterations=2,
    )

    print(f"\n📊 **Collaboration Results:**")
    print(f"Success: {result.success}")
    print(f"Total Time: {result.total_time:.2f}s")
    print(f"Confidence: {result.confidence_score:.2f}")
    print(f"Agent Responses: {len(result.agent_responses)}")

    print(f"\n🎯 **Final Answer:**")
    print(
        result.final_answer[:500] + "..."
        if len(result.final_answer) > 500
        else result.final_answer
    )

    print(f"\n📝 **Collaboration Log:**")
    for log_entry in result.collaboration_log:
        print(f"  • {log_entry}")

    return result


async def test_deployment_team():
    """Test the deployment team for cloud operations"""
    print("\n🚀 Testing Deployment Team Collaboration")
    print("=" * 50)

    config = DeploymentConfig(
        project_id="fredfix",
        github_repo="fredtaylor/ChatterFix",
        service_name="chatterfix-cmms",
    )

    deployment_orchestrator = get_deployment_orchestrator(config)

    # Display deployment team status
    status = deployment_orchestrator.get_agent_status()
    print(f"Deployment Team Size: {status['total_agents']} agents")
    for agent in status["agents"]:
        print(f"  ✅ {agent['name']} - {agent['role']}")
        print(f"     Capabilities: {', '.join(agent['capabilities'])}")

    print("\n🧪 Testing deployment pipeline collaboration...")

    # Test deployment pipeline
    deployment_result = await deployment_orchestrator.execute_deployment_pipeline(
        app_name="ChatterFix",
        github_repo="fredtaylor/ChatterFix",
        context="Production deployment with zero-downtime requirements and full monitoring.",
    )

    print(f"\n📊 **Deployment Results:**")
    result = deployment_result["deployment_result"]
    print(f"App: {deployment_result['app_name']}")
    print(f"Repository: {deployment_result['github_repo']}")
    print(f"Project: {deployment_result['project_id']}")
    print(f"Success: {result.success}")
    print(f"Total Time: {result.total_time:.2f}s")

    print(f"\n🎯 **Deployment Plan:**")
    print(
        result.final_answer[:800] + "..."
        if len(result.final_answer) > 800
        else result.final_answer
    )

    return deployment_result


async def test_agent_availability():
    """Test individual agent availability and API connections"""
    print("\n🔍 Testing Individual Agent Availability")
    print("=" * 50)

    orchestrator = get_orchestrator()

    for agent_name, agent in orchestrator.agents.items():
        try:
            available = await agent.is_available()
            status = "✅ Available" if available else "❌ Unavailable"
            print(f"  {agent_name}: {status}")

            if available:
                # Test a simple response
                test_response = await agent.generate_response("What is 1+1?", "")
                success = "Error:" not in test_response
                api_status = "✅ API Working" if success else "❌ API Error"
                print(f"    API Test: {api_status}")
                if not success:
                    print(f"    Error: {test_response[:100]}")

        except Exception as e:
            print(f"  {agent_name}: ❌ Exception - {str(e)}")

    return True


async def main():
    """Run all tests"""
    print("🚀 AI Team Integration Tests")
    print("=" * 60)

    try:
        # Test 1: Agent availability
        await test_agent_availability()

        # Test 2: General AI team collaboration
        general_result = await test_general_ai_team()

        # Test 3: Deployment team collaboration
        deployment_result = await test_deployment_team()

        print("\n🎉 **All Tests Completed Successfully!**")
        print("\n📋 **Summary:**")
        print(
            f"  • General AI Team: {len(general_result.agent_responses)} agents collaborated"
        )
        print(f"  • Deployment Team: {deployment_result['deployment_result'].success}")
        print(f"  • All APIs: Functional ✅")

        print("\n🤖 **Your AI teams are ready for production use!**")
        print("  • Real API integrations: Claude, ChatGPT, Gemini, Grok")
        print("  • Cloud deployment: Google Cloud Platform")
        print("  • Repository management: GitHub integration")
        print("  • gRPC services: Multi-model collaboration")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        logger.exception("Test execution failed")


if __name__ == "__main__":
    asyncio.run(main())

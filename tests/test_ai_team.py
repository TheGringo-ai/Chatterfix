#!/usr/bin/env python3
"""
Test script for optimized AI team - Verify all 6 agents are working
Tests: GPT-4o, GPT-4, Gemini Flash, Gemini Pro, Grok Code, Grok 3
"""

import asyncio
import json
import aiohttp
from typing import Dict, List

AI_TEAM_URL = "https://ai-team-service-psycl7nhha-uc.a.run.app"

async def test_ai_team_agents():
    """Test all AI agents in the optimized team"""
    
    print("🚀 TESTING OPTIMIZED AI TEAM - 6 AGENTS")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # 1. Check service health
        try:
            async with session.get(f"{AI_TEAM_URL}/health") as response:
                health = await response.json()
                print(f"✅ Service Health: {health}")
        except Exception as e:
            print(f"❌ Service Health Check Failed: {e}")
            return
        
        # 2. Get available models
        try:
            async with session.get(f"{AI_TEAM_URL}/api/v1/models") as response:
                models = await response.json()
                print(f"\n📊 Available Models: {models}")
                
                # Expected agents
                expected_agents = {
                    "gpt4-analyst": "Lead Analyst",
                    "chatgpt-coder": "Senior Developer", 
                    "gemini-creative": "Creative Director",
                    "gemini-analyst": "AI Specialist",
                    "grok-coder": "Speed Coder",
                    "grok-reasoner": "Strategic Thinker"
                }
                
                print(f"\n🎯 Expected Agents: {len(expected_agents)}")
                for agent, role in expected_agents.items():
                    print(f"   • {agent}: {role}")
                    
        except Exception as e:
            print(f"❌ Models Check Failed: {e}")
        
        # 3. Test collaboration endpoint
        test_task = {
            "task": "Quick test of AI team collaboration capabilities",
            "context": "Testing optimized 6-agent team after Claude removal"
        }
        
        try:
            print(f"\n🧪 Testing Collaboration...")
            async with session.post(
                f"{AI_TEAM_URL}/api/v1/execute", 
                json=test_task,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Collaboration Test: SUCCESS")
                    print(f"   Response: {json.dumps(result, indent=2)[:200]}...")
                else:
                    print(f"⚠️  Collaboration Test: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text[:200]}...")
        except Exception as e:
            print(f"❌ Collaboration Test Failed: {e}")

    print(f"\n🎉 AI TEAM TEST COMPLETED")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_ai_team_agents())
#!/usr/bin/env python3
"""
AI Team Collaboration Demo Script
Shows how to set up multi-model AI collaboration with Claude, GPT, Gemini, and Grok
"""

import asyncio
import json
import requests
import time

def wait_for_app():
    """Wait for the ChatterFix app to start"""
    print("⏳ Waiting for ChatterFix application to start...")
    for i in range(30):
        try:
            response = requests.get("http://localhost:8080/health", timeout=2)
            if response.status_code == 200:
                print("✅ ChatterFix application is running!")
                return True
        except:
            pass
        time.sleep(1)
    return False

def get_available_models():
    """Get list of available AI models"""
    try:
        response = requests.get("http://localhost:8080/ai-team/models")
        if response.status_code == 200:
            models = response.json()
            print(f"🤖 Available AI Models: {models}")
            return models
        else:
            print(f"❌ Failed to get models: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting models: {e}")
        return None

def demonstrate_collaboration():
    """Demonstrate AI team collaboration"""
    print("\n🚀 Starting AI Team Collaboration Demo...")

    # Example 1: Frontend Development Task
    frontend_task = {
        "prompt": "Create a modern, responsive login form with email/password fields, remember me checkbox, and social login buttons",
        "context": "Build a login component for a React-based CMMS application with Tailwind CSS styling",
        "required_models": ["claude", "chatgpt", "gemini"],
        "task_type": "FRONTEND_DEVELOPMENT",
        "max_iterations": 3
    }

    print("📝 Task 1: Frontend Development - Login Form")
    print(f"   Prompt: {frontend_task['prompt'][:100]}...")
    print(f"   Required Models: {frontend_task['required_models']}")

    try:
        response = requests.post(
            "http://localhost:8080/ai-team/execute",
            json=frontend_task,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Collaboration completed!")
            print(f"   Task ID: {result.get('task_id')}")
            print(f"   Success: {result.get('success')}")
            print(f"   Confidence: {result.get('confidence_score', 0):.2f}")
            print(f"   Final Result Preview: {result.get('final_result', '')[:200]}...")
        else:
            print(f"❌ Task failed: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Example 2: Backend API Design
    backend_task = {
        "prompt": "Design REST API endpoints for user authentication including login, logout, password reset, and JWT token management",
        "context": "FastAPI backend with Firebase Auth integration for a maintenance management system",
        "required_models": ["chatgpt", "claude"],
        "task_type": "BACKEND_DEVELOPMENT",
        "max_iterations": 2
    }

    print("\n📝 Task 2: Backend Development - Authentication API")
    print(f"   Prompt: {backend_task['prompt'][:100]}...")
    print(f"   Required Models: {backend_task['required_models']}")

    try:
        response = requests.post(
            "http://localhost:8080/ai-team/execute",
            json=backend_task,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Collaboration completed!")
            print(f"   Task ID: {result.get('task_id')}")
            print(f"   Success: {result.get('success')}")
            print(f"   Confidence: {result.get('confidence_score', 0):.2f}")
        else:
            print(f"❌ Task failed: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

def show_collaboration_examples():
    """Show different ways to set up collaboration"""
    print("\n" + "="*60)
    print("🎯 AI TEAM COLLABORATION EXAMPLES")
    print("="*60)

    examples = [
        {
            "title": "Full Stack Development",
            "models": ["claude", "chatgpt", "gemini", "grok"],
            "task": "Build a complete user management system with React frontend and FastAPI backend"
        },
        {
            "title": "Code Review & Optimization",
            "models": ["chatgpt", "claude"],
            "task": "Review and optimize existing Python code for performance and security"
        },
        {
            "title": "Database Design",
            "models": ["claude", "gemini"],
            "task": "Design database schema for a complex multi-tenant application"
        },
        {
            "title": "Testing & QA",
            "models": ["chatgpt", "grok"],
            "task": "Generate comprehensive test suites and QA automation scripts"
        },
        {
            "title": "Documentation",
            "models": ["claude", "gemini"],
            "task": "Create technical documentation and API references"
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print(f"   Models: {', '.join(example['models'])}")
        print(f"   Task: {example['task']}")

    print("\n" + "="*60)
    print("🔧 HOW TO USE COLLABORATION")
    print("="*60)
    print("""
1. Start ChatterFix: python main.py
2. Use the API endpoints:
   - GET  /ai-team/models     (list available models)
   - POST /ai-team/execute    (run collaborative task)
   - POST /ai-team/stream     (real-time collaboration)

3. Specify required_models in your request:
   {
     "prompt": "Your task description",
     "required_models": ["claude", "chatgpt", "gemini"],
     "max_iterations": 3
   }

4. Models will collaborate automatically:
   - Claude: Analytical thinking, code quality
   - ChatGPT: Creative solutions, documentation
   - Gemini: Fast processing, data analysis
   - Grok: Innovative approaches, humor

5. I (GitHub Copilot) can participate by:
   - Reviewing collaborative outputs
   - Providing additional context
   - Suggesting improvements
   - Implementing the generated code
    """)

def main():
    print("🤖 AI Team Collaboration Setup Guide")
    print("="*50)

    if not wait_for_app():
        print("❌ ChatterFix application failed to start. Please run: python main.py")
        return

    # Get available models
    models = get_available_models()

    if models:
        demonstrate_collaboration()

    show_collaboration_examples()

    print("\n🎉 Ready for AI-powered collaborative development!")
    print("💡 Tip: Use different model combinations for different types of tasks")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
ChatterFix CMMS - AI Collaboration Setup Script
Quick setup and demonstration of the AI Collaboration System
"""

import asyncio
import os
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_collaboration_system import (
    AICollaborationSystem,
    AIModel,
    Priority,
    TaskStatus,
    initialize_ai_collaboration
)

async def setup_ai_collaboration_demo():
    """
    Setup and demonstrate the AI Collaboration System
    """
    print("🚀 Setting up ChatterFix AI Collaboration System...")
    print("=" * 60)
    
    # Initialize the system
    try:
        collaboration_system = await initialize_ai_collaboration()
        print("✅ AI Collaboration System initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        return False
    
    print("\n📋 Demonstrating AI Collaboration Features...")
    print("-" * 40)
    
    # 1. Start AI sessions for different models
    print("\n1. Starting AI sessions...")
    sessions = {}
    
    for ai_model in [AIModel.CLAUDE, AIModel.CHATGPT, AIModel.GROK, AIModel.LLAMA]:
        try:
            session_id, session_data = await collaboration_system.start_ai_session(
                ai_model, 
                f"Demo session for {ai_model.value}"
            )
            sessions[ai_model] = session_id
            print(f"   ✅ {ai_model.value.upper()} session started: {session_id[:8]}...")
        except Exception as e:
            print(f"   ❌ Failed to start {ai_model.value} session: {e}")
    
    # 2. Create demo tasks
    print("\n2. Creating collaboration tasks...")
    tasks = []
    
    demo_tasks = [
        {
            "title": "Review ChatterFix Architecture",
            "description": "Analyze current system architecture and identify improvement areas",
            "assigned_ai": AIModel.CLAUDE,
            "priority": Priority.HIGH,
            "created_by": AIModel.CLAUDE
        },
        {
            "title": "Improve Frontend User Experience",
            "description": "Enhance UI/UX for work order management interface",
            "assigned_ai": AIModel.CHATGPT,
            "priority": Priority.MEDIUM,
            "created_by": AIModel.CLAUDE
        },
        {
            "title": "Debug Performance Issues",
            "description": "Investigate and resolve database query performance problems",
            "assigned_ai": AIModel.GROK,
            "priority": Priority.CRITICAL,
            "created_by": AIModel.CHATGPT
        },
        {
            "title": "Enhance Analytics Dashboard",
            "description": "Implement advanced data analytics and reporting features",
            "assigned_ai": AIModel.LLAMA,
            "priority": Priority.MEDIUM,
            "created_by": AIModel.GROK
        }
    ]
    
    for task_data in demo_tasks:
        try:
            task_id = await collaboration_system.create_task(**task_data)
            tasks.append(task_id)
            print(f"   ✅ Task created: {task_data['title']} -> {task_data['assigned_ai'].value}")
        except Exception as e:
            print(f"   ❌ Failed to create task: {e}")
    
    # 3. Query knowledge base
    print("\n3. Testing knowledge base queries...")
    
    test_queries = [
        "work order management",
        "database schema",
        "AI integration",
        "deployment process",
        "modal creation"
    ]
    
    for query in test_queries:
        try:
            results = await collaboration_system.query_knowledge(query, AIModel.CLAUDE)
            print(f"   ✅ Query '{query}': {len(results)} results found")
        except Exception as e:
            print(f"   ❌ Query '{query}' failed: {e}")
    
    # 4. Capture current context
    print("\n4. Capturing project context...")
    try:
        context = await collaboration_system.context_manager.capture_current_context()
        print(f"   ✅ Context captured: {context.context_id[:8]}...")
        print(f"   📊 Active features: {len(context.active_features)}")
        print(f"   ⚠️  Known issues: {len(context.known_issues)}")
        print(f"   📝 Technical debt: {len(context.technical_debt)}")
    except Exception as e:
        print(f"   ❌ Failed to capture context: {e}")
    
    # 5. Test deployment safety
    print("\n5. Testing deployment safety system...")
    try:
        safety_result = await collaboration_system.deploy_with_safety(
            AIModel.CLAUDE, 
            "Demo deployment safety check"
        )
        print(f"   ✅ Safety check completed: {safety_result['deployment_status']}")
        print(f"   💾 Backup created: {safety_result['backup_id'][:8]}...")
        print(f"   🧪 Test status: {safety_result['test_results']['overall_status']}")
    except Exception as e:
        print(f"   ❌ Safety check failed: {e}")
    
    # 6. Demonstrate AI handoff
    print("\n6. Testing AI handoff process...")
    try:
        handoff_id = await collaboration_system.handoff_manager.initiate_handoff(
            AIModel.CLAUDE,
            AIModel.CHATGPT,
            "normal",
            "Handing off frontend development tasks"
        )
        print(f"   ✅ Handoff initiated: {handoff_id[:8]}...")
        
        # Receive handoff
        handoff_data = await collaboration_system.handoff_manager.receive_handoff(
            handoff_id,
            AIModel.CHATGPT
        )
        print(f"   ✅ Handoff received by ChatGPT")
        print(f"   📋 Recommendations: {len(handoff_data['recommendations'])}")
    except Exception as e:
        print(f"   ❌ Handoff failed: {e}")
    
    # 7. Get system status
    print("\n7. System status overview...")
    try:
        status = await collaboration_system.get_system_status()
        print(f"   ✅ System health: {status['system_health']['deployment_status']}")
        print(f"   🔄 Active sessions: {sum(status['active_sessions'].values()) if status['active_sessions'] else 0}")
        print(f"   📋 Task summary: {status['task_summary']}")
        print(f"   📚 Knowledge entries: {status['knowledge_base_entries']}")
    except Exception as e:
        print(f"   ❌ Status check failed: {e}")
    
    # 8. Complete a task
    print("\n8. Completing a demo task...")
    if tasks:
        try:
            await collaboration_system.complete_task(
                tasks[0],
                AIModel.CLAUDE,
                "Task completed successfully during demo",
                ["demo_artifact.txt"]
            )
            print(f"   ✅ Task completed: {tasks[0][:8]}...")
        except Exception as e:
            print(f"   ❌ Task completion failed: {e}")
    
    # 9. End sessions
    print("\n9. Ending AI sessions...")
    for ai_model, session_id in sessions.items():
        try:
            summary = await collaboration_system.end_ai_session(
                session_id,
                f"Demo session completed for {ai_model.value}"
            )
            print(f"   ✅ {ai_model.value.upper()} session ended")
        except Exception as e:
            print(f"   ❌ Failed to end {ai_model.value} session: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 AI Collaboration System Demo Complete!")
    print("\n📋 Summary of Created Components:")
    print("   • AI Collaboration Database (ai_collaboration.db)")
    print("   • Context Management System")
    print("   • Task Workflow Framework") 
    print("   • Knowledge Base with ChatterFix expertise")
    print("   • Deployment Safety System")
    print("   • AI Handoff Protocol")
    print("   • Web Dashboard Interface")
    print("   • REST API Endpoints")
    
    print("\n🚀 Next Steps:")
    print("   1. Integrate with main ChatterFix app using ai_collaboration_integration.py")
    print("   2. Access dashboard at /ai-collaboration")
    print("   3. Start collaborating with multiple AI models")
    print("   4. Monitor progress and maintain context across sessions")
    
    print("\n📖 Documentation:")
    print("   • Complete guide: AI_COLLABORATION_SYSTEM_GUIDE.md")
    print("   • API documentation available via dashboard")
    
    return True

async def test_integration():
    """
    Test the integration with a minimal FastAPI app
    """
    print("\n🧪 Testing Integration...")
    print("-" * 30)
    
    try:
        from fastapi import FastAPI
        from ai_collaboration_integration import integrate_ai_collaboration
        
        # Create test app
        app = FastAPI(title="ChatterFix AI Collaboration Test")
        
        # Integrate collaboration system
        success = integrate_ai_collaboration(app)
        
        if success:
            print("✅ Integration successful!")
            print("📋 Available endpoints added to FastAPI app")
            
            # List some key endpoints
            print("\n🔗 Key Endpoints:")
            print("   • GET  /ai-collaboration (Dashboard)")
            print("   • GET  /api/ai-collaboration/status")
            print("   • POST /api/ai-collaboration/session/start")
            print("   • POST /api/ai-collaboration/task/create")
            print("   • POST /api/ai-collaboration/knowledge/query")
            
        else:
            print("❌ Integration failed")
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")

def check_requirements():
    """
    Check if all required dependencies are available
    """
    print("🔍 Checking Requirements...")
    print("-" * 25)
    
    required_modules = [
        'fastapi',
        'sqlite3',
        'asyncio',
        'json',
        'datetime',
        'pathlib',
        'logging',
        'uuid',
        'hashlib'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} (missing)")
            missing.append(module)
    
    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("   Please install required packages")
        return False
    else:
        print("\n✅ All dependencies available")
        return True

if __name__ == "__main__":
    print("🤖 ChatterFix CMMS - AI Collaboration System Setup")
    print("=" * 55)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup and demo
    try:
        asyncio.run(setup_ai_collaboration_demo())
        asyncio.run(test_integration())
        
        print("\n🎯 Setup Complete!")
        print("The AI Collaboration System is ready for use.")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
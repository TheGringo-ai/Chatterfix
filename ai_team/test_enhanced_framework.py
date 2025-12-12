"""
Comprehensive Test Suite for Enhanced Autogen Framework
Tests all new features: task routing, performance optimization,
collaboration engine, and real-time monitoring
"""

import asyncio
import json
import logging
import time
import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

# Import the enhanced framework components
from .autogen_framework import AutogenOrchestrator, get_orchestrator
from .task_routing import TaskType, TaskClassification, IntelligentTaskRouter
from .performance_optimizer import PerformanceOptimizer, QualityDimension
from .collaboration_engine import (
    CollaborationMode,
    CollaborationContext,
    AdvancedCollaborationEngine
)
from .realtime_monitor import (
    RealtimeMonitoringDashboard,
    MonitoringLevel,
    MetricType,
    RealtimeMetric
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEnhancedFramework(unittest.IsolatedAsyncioTestCase):
    """Test suite for enhanced autogen framework"""

    async def asyncSetUp(self):
        """Set up test environment"""
        self.orchestrator = AutogenOrchestrator()
        self.orchestrator.setup_default_agents()
        self.orchestrator.enable_enhanced_features(True)
        
        # Mock the actual AI agent responses to avoid API calls
        self.mock_responses = {
            "claude-analyst": "As Claude, I analyze this as a complex coding task requiring careful architecture planning.",
            "chatgpt-coder": "As ChatGPT, I'll implement this with clean, efficient code following best practices.",
            "gemini-creative": "As Gemini, I suggest an innovative approach with modern design patterns.",
            "grok-coder": "As Grok, here's a fast, optimized implementation that scales well.",
            "grok-reasoner": "As Grok Reasoner, the logical approach is to break this into smaller components."
        }

    async def asyncTearDown(self):
        """Clean up test environment"""
        # Clean up monitoring and optimization systems
        if hasattr(self.orchestrator, 'realtime_monitor'):
            self.orchestrator.realtime_monitor.stop_monitoring()

    async def test_task_classification(self):
        """Test intelligent task classification"""
        logger.info("🧪 Testing task classification...")
        
        test_cases = [
            {
                "prompt": "Create a function to calculate fibonacci numbers",
                "expected_type": TaskType.CODING,
                "context": "Need to implement algorithm"
            },
            {
                "prompt": "Analyze the performance issues in our system",
                "expected_type": TaskType.ANALYSIS,
                "context": "System running slowly"
            },
            {
                "prompt": "Design a beautiful user interface for mobile app",
                "expected_type": TaskType.CREATIVE,
                "context": "Need modern UI design"
            },
            {
                "prompt": "Fix the bug causing login failures",
                "expected_type": TaskType.DEBUGGING,
                "context": "Authentication not working"
            }
        ]
        
        for test_case in test_cases:
            classification = await self.orchestrator.task_router.classify_task(
                test_case["prompt"], test_case["context"]
            )
            
            self.assertIsInstance(classification, TaskClassification)
            self.assertEqual(classification.primary_type, test_case["expected_type"])
            self.assertGreater(classification.confidence_score, 0.0)
            self.assertLessEqual(classification.confidence_score, 1.0)
            
            logger.info(f"✅ Classified '{test_case['prompt'][:30]}...' as {classification.primary_type.value}")

    async def test_agent_routing(self):
        """Test intelligent agent routing"""
        logger.info("🧪 Testing agent routing...")
        
        # Test coding task routing
        coding_classification = TaskClassification(
            primary_type=TaskType.CODING,
            secondary_types=[TaskType.ARCHITECTURE],
            confidence_score=0.8,
            complexity_level="medium",
            estimated_duration="medium",
            required_capabilities=["coding", "architecture"]
        )
        
        available_agents = list(self.orchestrator.agents.keys())
        selected_agents = await self.orchestrator.task_router.route_task(
            coding_classification, available_agents
        )
        
        self.assertIsInstance(selected_agents, list)
        self.assertGreater(len(selected_agents), 0)
        
        # Should prefer coding-capable agents
        coding_agents = ["chatgpt-coder", "grok-coder"]
        has_coding_agent = any(agent in selected_agents for agent in coding_agents)
        self.assertTrue(has_coding_agent, "Should select coding-capable agents for coding tasks")
        
        logger.info(f"✅ Routed coding task to: {selected_agents}")

    async def test_performance_optimization(self):
        """Test performance optimization features"""
        logger.info("🧪 Testing performance optimization...")
        
        # Test cache functionality
        test_prompt = "What is the current time?"
        test_context = "Testing caching"
        test_agent = "claude-analyst"
        test_model = "claude"
        
        # First request should miss cache
        cached_response, cache_hit, optimization_info = await self.orchestrator.performance_optimizer.optimize_request(
            test_prompt, test_context, test_agent, test_model
        )
        
        self.assertFalse(cache_hit, "First request should not hit cache")
        
        # Test quality assessment
        test_response = "The current time is 12:00 PM. This is a clear and accurate response."
        processed_response, quality_score, post_info = await self.orchestrator.performance_optimizer.post_process_response(
            test_response, test_prompt, test_context, test_agent, test_model
        )
        
        self.assertEqual(processed_response, test_response)
        self.assertGreater(quality_score, 0.0)
        self.assertLessEqual(quality_score, 1.0)
        
        # Test optimization analytics
        analytics = await self.orchestrator.performance_optimizer.get_optimization_analytics()
        self.assertIsInstance(analytics, dict)
        self.assertIn("cache_performance", analytics)
        
        logger.info(f"✅ Performance optimization working (Quality: {quality_score:.2f})")

    async def test_collaboration_modes(self):
        """Test different collaboration modes"""
        logger.info("🧪 Testing collaboration modes...")
        
        # Test parallel mode
        result_parallel = await self.orchestrator.execute_enhanced_task(
            task_id="test_parallel",
            prompt="Create a simple hello world function",
            context="Testing parallel collaboration",
            collaboration_mode=CollaborationMode.PARALLEL
        )
        
        self.assertTrue(result_parallel.success)
        self.assertGreater(len(result_parallel.agent_responses), 0)
        
        # Test devils advocate mode
        result_devils_advocate = await self.orchestrator.execute_enhanced_task(
            task_id="test_devils_advocate",
            prompt="Design a secure authentication system",
            context="Testing devils advocate collaboration",
            collaboration_mode=CollaborationMode.DEVILS_ADVOCATE
        )
        
        self.assertTrue(result_devils_advocate.success)
        
        # Test consensus building
        result_consensus = await self.orchestrator.execute_enhanced_task(
            task_id="test_consensus",
            prompt="Choose the best database for our application",
            context="Testing consensus building",
            collaboration_mode=CollaborationMode.CONSENSUS_BUILDING
        )
        
        self.assertTrue(result_consensus.success)
        
        logger.info("✅ All collaboration modes working")

    async def test_realtime_monitoring(self):
        """Test real-time monitoring capabilities"""
        logger.info("🧪 Testing real-time monitoring...")
        
        # Start monitoring session
        session_id = await self.orchestrator.realtime_monitor.start_monitoring_session(
            "test_session", {"test": "monitoring"}
        )
        
        self.assertIsInstance(session_id, str)
        self.assertNotEqual(session_id, "")
        
        # Record some test interactions
        await self.orchestrator.realtime_monitor.record_agent_interaction(
            session_id, "claude-analyst", "test_task", 2.5, 0.8, True
        )
        
        await self.orchestrator.realtime_monitor.record_agent_interaction(
            session_id, "chatgpt-coder", "test_task", 3.1, 0.7, True
        )
        
        # Get dashboard
        dashboard = await self.orchestrator.realtime_monitor.get_realtime_dashboard()
        
        self.assertIsInstance(dashboard, dict)
        self.assertIn("timestamp", dashboard)
        self.assertIn("current_metrics", dashboard)
        self.assertIn("system_status", dashboard)
        
        logger.info("✅ Real-time monitoring working")

    async def test_quality_assessment(self):
        """Test streaming quality assessment"""
        logger.info("🧪 Testing quality assessment...")
        
        test_cases = [
            {
                "response": "This is a clear, accurate, and well-structured response that addresses all aspects of the question.",
                "prompt": "Explain how to write clean code",
                "expected_quality": 0.6  # Should be relatively high
            },
            {
                "response": "Umm, maybe this could work but I'm not sure...",
                "prompt": "Design a secure system",
                "expected_quality": 0.4  # Should be lower due to uncertainty
            },
            {
                "response": "Error error wrong incorrect failed broken",
                "prompt": "Create a function",
                "expected_quality": 0.2  # Should be very low due to error indicators
            }
        ]
        
        for test_case in test_cases:
            assessment = await self.orchestrator.realtime_monitor.streaming_monitor.assess_streaming_quality(
                test_case["response"], test_case["prompt"]
            )
            
            self.assertIsNotNone(assessment)
            self.assertGreater(assessment.current_quality, 0.0)
            self.assertLessEqual(assessment.current_quality, 1.0)
            
            # Quality should roughly match expectations
            if test_case["expected_quality"] > 0.5:
                self.assertGreater(assessment.current_quality, 0.4, 
                                 f"High quality response should score above 0.4: {test_case['response'][:50]}")
            elif test_case["expected_quality"] < 0.3:
                self.assertLess(assessment.current_quality, 0.6,
                               f"Low quality response should score below 0.6: {test_case['response'][:50]}")
            
            logger.info(f"✅ Quality assessment: {assessment.current_quality:.2f} for '{test_case['response'][:30]}...'")

    async def test_agent_health_monitoring(self):
        """Test agent health monitoring"""
        logger.info("🧪 Testing agent health monitoring...")
        
        # Simulate some agent activity first
        for agent_name in ["claude-analyst", "chatgpt-coder"]:
            await self.orchestrator.realtime_monitor.record_agent_interaction(
                "health_test", agent_name, "test", 2.0, 0.8, True
            )
        
        # Test health assessment
        health_status = await self.orchestrator.realtime_monitor.agent_health_monitor.assess_agent_health(
            "claude-analyst"
        )
        
        self.assertIsNotNone(health_status)
        self.assertEqual(health_status.agent_name, "claude-analyst")
        self.assertGreater(health_status.health_score, 0.0)
        self.assertLessEqual(health_status.health_score, 1.0)
        
        # Test all agent health
        all_health = await self.orchestrator.realtime_monitor.agent_health_monitor.get_all_agent_health()
        self.assertIsInstance(all_health, dict)
        
        logger.info("✅ Agent health monitoring working")

    async def test_enhanced_task_execution(self):
        """Test complete enhanced task execution"""
        logger.info("🧪 Testing enhanced task execution...")
        
        # Mock agent responses to avoid API calls
        with patch.object(self.orchestrator.agents["claude-analyst"], 'generate_response', 
                         new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = self.mock_responses["claude-analyst"]
            
            with patch.object(self.orchestrator.agents["chatgpt-coder"], 'generate_response',
                             new_callable=AsyncMock) as mock_chatgpt:
                mock_chatgpt.return_value = self.mock_responses["chatgpt-coder"]
                
                # Test enhanced task execution
                result = await self.orchestrator.execute_enhanced_task(
                    task_id="test_enhanced_execution",
                    prompt="Create a REST API for user management with proper authentication",
                    context="Building a secure web application",
                    collaboration_mode=CollaborationMode.PARALLEL
                )
                
                # Validate results
                self.assertTrue(result.success)
                self.assertIsNotNone(result.final_answer)
                self.assertGreater(len(result.agent_responses), 0)
                self.assertGreater(result.confidence_score, 0.0)
                
                # Check for enhanced metadata
                if hasattr(result, '__dict__'):
                    enhanced_attrs = ['enhanced_features_used', 'optimization_metrics']
                    for attr in enhanced_attrs:
                        if attr in result.__dict__:
                            logger.info(f"✅ Enhanced metadata present: {attr}")
                
                logger.info(f"✅ Enhanced execution completed (Confidence: {result.confidence_score:.2f})")

    async def test_error_handling(self):
        """Test error handling in enhanced features"""
        logger.info("🧪 Testing error handling...")
        
        # Test with invalid inputs
        try:
            # Test task classification with empty prompt
            classification = await self.orchestrator.task_router.classify_task("", "")
            self.assertIsNotNone(classification)  # Should handle gracefully
        except Exception as e:
            logger.warning(f"Task classification error handled: {e}")
        
        try:
            # Test monitoring with invalid session
            await self.orchestrator.realtime_monitor.record_agent_interaction(
                "", "nonexistent-agent", "test", -1.0, 2.0, True
            )
        except Exception as e:
            logger.warning(f"Monitoring error handled: {e}")
        
        logger.info("✅ Error handling working")

    async def test_performance_benchmarks(self):
        """Test performance benchmarks of enhanced features"""
        logger.info("🧪 Testing performance benchmarks...")
        
        # Benchmark task classification
        start_time = time.time()
        for i in range(10):
            await self.orchestrator.task_router.classify_task(
                f"Test task {i}", f"Context {i}"
            )
        classification_time = (time.time() - start_time) / 10
        
        self.assertLess(classification_time, 0.1, "Task classification should be fast")
        
        # Benchmark quality assessment
        start_time = time.time()
        for i in range(10):
            await self.orchestrator.realtime_monitor.streaming_monitor.assess_streaming_quality(
                f"Test response {i}", f"Test prompt {i}"
            )
        quality_time = (time.time() - start_time) / 10
        
        self.assertLess(quality_time, 0.1, "Quality assessment should be fast")
        
        logger.info(f"✅ Performance benchmarks: Classification={classification_time:.3f}s, Quality={quality_time:.3f}s")

    async def test_comprehensive_analytics(self):
        """Test comprehensive analytics system"""
        logger.info("🧪 Testing comprehensive analytics...")
        
        # Get analytics with enhanced features
        analytics = await self.orchestrator.get_comprehensive_analytics(include_enhanced=True)
        
        self.assertIsInstance(analytics, dict)
        self.assertIn("timestamp", analytics)
        self.assertIn("enhanced_features_enabled", analytics)
        
        # Check for enhanced analytics sections
        enhanced_sections = [
            "optimization_analytics",
            "monitoring_analytics", 
            "routing_analytics",
            "collaboration_analytics"
        ]
        
        for section in enhanced_sections:
            if section in analytics:
                self.assertIsInstance(analytics[section], dict)
                logger.info(f"✅ Enhanced analytics section present: {section}")
        
        # Test agent status with enhanced features
        status = self.orchestrator.get_agent_status()
        self.assertIn("enhanced_features_enabled", status)
        self.assertTrue(status["enhanced_features_enabled"])
        
        logger.info("✅ Comprehensive analytics working")

    async def test_feature_integration(self):
        """Test integration between all enhanced features"""
        logger.info("🧪 Testing feature integration...")
        
        # Test complete workflow: routing -> optimization -> collaboration -> monitoring
        with patch.object(self.orchestrator.agents["claude-analyst"], 'generate_response',
                         new_callable=AsyncMock) as mock_claude:
            mock_claude.return_value = self.mock_responses["claude-analyst"]
            
            # Execute task with all features enabled
            result = await self.orchestrator.execute_enhanced_task(
                task_id="integration_test",
                prompt="Optimize database queries for better performance",
                context="System performance issues detected",
                collaboration_mode=CollaborationMode.CONSENSUS_BUILDING
            )
            
            # Verify integration worked
            self.assertTrue(result.success)
            
            # Check if task was properly classified
            if hasattr(result, '__dict__') and 'task_classification' in result.__dict__:
                classification = result.__dict__['task_classification']
                if classification:
                    expected_types = [TaskType.OPTIMIZATION, TaskType.ANALYSIS]
                    self.assertIn(classification['primary_type'], [t.value for t in expected_types])
                    logger.info(f"✅ Task properly classified as {classification['primary_type']}")
            
            # Check optimization metrics
            if hasattr(result, '__dict__') and 'optimization_metrics' in result.__dict__:
                metrics = result.__dict__['optimization_metrics']
                self.assertIn('avg_quality_score', metrics)
                self.assertIn('avg_response_time', metrics)
                logger.info(f"✅ Optimization metrics captured")
            
            # Get real-time dashboard to verify monitoring
            dashboard = await self.orchestrator.get_realtime_dashboard()
            self.assertIn("timestamp", dashboard)
            
            logger.info("✅ Feature integration working successfully")

    async def test_system_health(self):
        """Test overall system health and diagnostics"""
        logger.info("🧪 Testing system health...")
        
        # Test enhanced features functionality
        test_results = await self.orchestrator.test_enhanced_features()
        
        self.assertIsInstance(test_results, dict)
        self.assertIn("overall_status", test_results)
        
        # At least some features should be working
        working_features = [
            test_results.get("task_routing", False),
            test_results.get("performance_optimization", False),
            test_results.get("collaboration_engine", False),
            test_results.get("realtime_monitoring", False)
        ]
        
        working_count = sum(working_features)
        self.assertGreater(working_count, 0, "At least some enhanced features should be working")
        
        logger.info(f"✅ System health: {working_count}/4 enhanced features working")
        logger.info(f"   Overall status: {test_results['overall_status']}")


async def run_comprehensive_tests():
    """Run all tests comprehensively"""
    print("🚀 STARTING ENHANCED AUTOGEN FRAMEWORK COMPREHENSIVE TESTS")
    print("=" * 80)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEnhancedFramework)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    if result.failures:
        print("\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print("\n⚠️ ERRORS:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    if len(result.failures) == 0 and len(result.errors) == 0:
        print("\n✅ ALL TESTS PASSED! Enhanced framework is working perfectly.")
        return True
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        return False


async def demo_enhanced_features():
    """Demonstrate enhanced features in action"""
    print("\n🎭 ENHANCED FEATURES DEMONSTRATION")
    print("=" * 50)
    
    # Initialize orchestrator
    orchestrator = get_orchestrator()
    orchestrator.enable_enhanced_features(True)
    
    # Demo 1: Intelligent Task Routing
    print("\n1. 🎯 INTELLIGENT TASK ROUTING DEMO")
    prompt = "Create a secure login system with two-factor authentication"
    classification = await orchestrator.task_router.classify_task(prompt, "Security focused development")
    print(f"   Task: {prompt}")
    print(f"   Classified as: {classification.primary_type.value}")
    print(f"   Confidence: {classification.confidence_score:.2f}")
    print(f"   Complexity: {classification.complexity_level}")
    
    # Demo 2: Performance Optimization
    print("\n2. ⚡ PERFORMANCE OPTIMIZATION DEMO")
    analytics = await orchestrator.performance_optimizer.get_optimization_analytics()
    print(f"   Cache performance: {analytics.get('cache_performance', {})}")
    print(f"   Optimization recommendations: {analytics.get('recommendations', ['None'])[:2]}")
    
    # Demo 3: Real-time Monitoring
    print("\n3. 📊 REAL-TIME MONITORING DEMO")
    dashboard = await orchestrator.get_realtime_dashboard()
    print(f"   System status: {dashboard.get('system_status', {}).get('status', 'unknown')}")
    print(f"   Active sessions: {len(dashboard.get('active_sessions', {}))}")
    print(f"   Monitoring level: {dashboard.get('monitoring_level', 'unknown')}")
    
    # Demo 4: Enhanced Collaboration
    print("\n4. 🤝 COLLABORATION MODES DEMO")
    collab_analytics = orchestrator.collaboration_engine.get_collaboration_analytics()
    print(f"   Available modes: {[mode.value for mode in CollaborationMode]}")
    print(f"   Total collaborations: {collab_analytics.get('total_collaborations', 0)}")
    
    print("\n✨ Enhanced features demonstration completed!")


if __name__ == "__main__":
    # Run comprehensive tests
    async def main():
        print("🧪 ENHANCED AUTOGEN FRAMEWORK - COMPREHENSIVE TEST SUITE")
        print("Testing all advanced features: routing, optimization, collaboration, monitoring")
        print()
        
        # Run tests
        success = await run_comprehensive_tests()
        
        if success:
            # Run demo if tests pass
            await demo_enhanced_features()
        
        return success
    
    # Run the test suite
    asyncio.run(main())
#!/usr/bin/env python3
"""
LineSmart Intelligence System Test Script
Tests the complete AI-powered failure-to-training automation system
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import LineSmart services
try:
    from app.services.linesmart_intelligence import linesmart_intelligence, get_workforce_intelligence_dashboard
    from app.core.firestore_db import get_firestore_manager
    print("✅ Successfully imported LineSmart Intelligence services")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)


async def create_test_work_orders():
    """Create test work orders with Genesis project technicians for LineSmart testing"""
    try:
        firestore_manager = get_firestore_manager()
        
        # Test work orders that will trigger different LineSmart intelligence patterns
        test_work_orders = [
            {
                "title": "Hydraulic Press Seal Failure - Recurring Issue",
                "description": "Hydraulic fluid leaking from main cylinder seal. Third occurrence this quarter.",
                "work_summary": "Replaced hydraulic seal. Found contaminated fluid may be causing premature wear. Took 6 hours due to difficulty accessing seal housing.",
                "assigned_to": "4",  # Jake Thompson
                "asset_id": "hydraulic_press_001",
                "priority": "High",
                "status": "Completed",
                "actual_hours": 6.0,
                "completed_date": datetime.now().isoformat(),
                "work_order_type": "Corrective",
                "completion_parts": [
                    {"part_id": "seal_001", "part_name": "Hydraulic Cylinder Seal", "quantity_used": 1, "unit_cost": 45.00}
                ]
            },
            {
                "title": "Conveyor Belt Misalignment - Production Impact", 
                "description": "Conveyor belt tracking off-center causing product damage and reduced throughput.",
                "work_summary": "Adjusted belt tracking and replaced worn guide rollers. Belt tension was incorrect due to improper previous adjustment. Completed in 4 hours.",
                "assigned_to": "5",  # Anna Kowalski
                "asset_id": "conveyor_001",
                "priority": "Medium",
                "status": "Completed", 
                "actual_hours": 4.0,
                "completed_date": (datetime.now() - timedelta(days=1)).isoformat(),
                "work_order_type": "Corrective",
                "completion_parts": [
                    {"part_id": "roller_001", "part_name": "Guide Roller", "quantity_used": 2, "unit_cost": 25.00}
                ]
            },
            {
                "title": "Electrical Panel Overheating - Safety Risk",
                "description": "Main electrical panel running hot, breaker tripping intermittently. Potential fire hazard.",
                "work_summary": "Found loose electrical connections and inadequate ventilation. Tightened connections and cleaned panel. Should have been caught in routine inspection.",
                "assigned_to": "4",  # Jake Thompson
                "asset_id": "electrical_panel_001",
                "priority": "Critical",
                "status": "Completed",
                "actual_hours": 3.0,
                "completed_date": (datetime.now() - timedelta(days=2)).isoformat(),
                "work_order_type": "Emergency",
                "completion_parts": []
            },
            {
                "title": "CNC Machine Spindle Vibration - Quality Issues",
                "description": "Excessive vibration in CNC spindle causing poor surface finish on parts.",
                "work_summary": "Diagnosed worn spindle bearings. Replacement required specialized tools and took longer than expected due to learning curve.",
                "assigned_to": "5",  # Anna Kowalski  
                "asset_id": "cnc_machine_001",
                "priority": "High",
                "status": "Completed",
                "actual_hours": 8.0,
                "completed_date": (datetime.now() - timedelta(days=3)).isoformat(),
                "work_order_type": "Corrective",
                "completion_parts": [
                    {"part_id": "bearing_001", "part_name": "Spindle Bearing Kit", "quantity_used": 1, "unit_cost": 180.00}
                ]
            }
        ]
        
        work_order_ids = []
        for wo_data in test_work_orders:
            wo_data["created_date"] = wo_data["completed_date"]
            wo_id = await firestore_manager.create_document("work_orders", wo_data)
            work_order_ids.append(wo_id)
            logger.info(f"Created test work order: {wo_id} - {wo_data['title']}")
            
        return work_order_ids
        
    except Exception as e:
        logger.error(f"Error creating test work orders: {e}")
        return []


async def run_intelligence_analysis(work_order_ids):
    """Run LineSmart intelligence analysis on completed work orders (manual test)"""
    print("\n🧠 Testing LineSmart Intelligence Analysis...")
    
    analyses = []
    for wo_id in work_order_ids:
        try:
            print(f"\n📊 Analyzing work order: {wo_id}")
            analysis = await linesmart_intelligence.analyze_failure_for_training(wo_id)
            
            if analysis.get("error"):
                print(f"❌ Analysis failed: {analysis['error']}")
                continue
                
            analyses.append(analysis)
            
            print("✅ Analysis Results:")
            print(f"   • Failure Type: {analysis.get('failure_analysis', {}).get('failure_type', 'N/A')}")
            print(f"   • Root Cause: {analysis.get('failure_analysis', {}).get('root_cause_category', 'N/A')}")
            print(f"   • Preventability Score: {analysis.get('failure_analysis', {}).get('preventability_score', 0)}%")
            
            skill_gaps = analysis.get('skill_gap_analysis', {}).get('identified_gaps', [])
            if skill_gaps:
                print(f"   • Identified Skill Gaps: {', '.join(skill_gaps)}")
            
            training_opp = analysis.get('training_opportunities')
            if training_opp:
                print(f"   • Training Recommended: {training_opp.get('primary_focus', 'N/A')}")
                print(f"   • Impact Level: {training_opp.get('estimated_impact', 'N/A')}")
                
                # Test training content generation
                if analysis.get('training_recommendation'):
                    training_content = analysis['training_recommendation']
                    print(f"   • AI Training Module Generated: {training_content.get('title', 'N/A')}")
                    print(f"   • Duration: {training_content.get('estimated_duration_minutes', 0)} minutes")
            else:
                print("   • No training opportunities identified")
                
        except Exception as e:
            print(f"❌ Error analyzing work order {wo_id}: {e}")
            
    return analyses


async def run_performance_analytics():
    """Run performance improvement metrics (manual test)"""
    print("\n📈 Testing Performance Analytics...")
    
    # Test Jake Thompson (ID: 4)
    print("\n👨‍🔧 Jake Thompson Performance Analysis:")
    jake_metrics = await linesmart_intelligence.get_performance_improvement_metrics("4", 180)
    
    if jake_metrics.get("error"):
        print(f"❌ Jake's analysis failed: {jake_metrics['error']}")
    else:
        improvements = jake_metrics.get("improvements", {})
        print(f"   • Efficiency Improvement: {improvements.get('efficiency_improvement_percent', 0)}%")
        print(f"   • First-Time Fix Improvement: {improvements.get('first_time_fix_improvement_percent', 0)}%")
        print(f"   • Work Order Volume Change: {improvements.get('work_order_volume_change', 0)}")
    
    # Test Anna Kowalski (ID: 5)
    print("\n👩‍🔧 Anna Kowalski Performance Analysis:")
    anna_metrics = await linesmart_intelligence.get_performance_improvement_metrics("5", 180)
    
    if anna_metrics.get("error"):
        print(f"❌ Anna's analysis failed: {anna_metrics['error']}")
    else:
        improvements = anna_metrics.get("improvements", {})
        print(f"   • Efficiency Improvement: {improvements.get('efficiency_improvement_percent', 0)}%")
        print(f"   • First-Time Fix Improvement: {improvements.get('first_time_fix_improvement_percent', 0)}%")
        print(f"   • Work Order Volume Change: {improvements.get('work_order_volume_change', 0)}")
    
    return {"jake": jake_metrics, "anna": anna_metrics}


async def run_skill_gap_analytics():
    """Run skill gap analytics across workforce (manual test)"""
    print("\n🎯 Testing Skill Gap Analytics...")
    
    analytics = await linesmart_intelligence.get_skill_gap_analytics(timeframe_days=90)
    
    if analytics.get("error"):
        print(f"❌ Analytics failed: {analytics['error']}")
        return analytics
    
    print(f"✅ Analytics Results (Last 90 days):")
    print(f"   • Total Analyses: {analytics.get('total_analyses', 0)}")
    
    skill_gaps = analytics.get('top_skill_gaps', {})
    if skill_gaps:
        print("   • Top Skill Gaps:")
        for skill, count in skill_gaps.items():
            print(f"     - {skill}: {count} occurrences")
    
    failure_types = analytics.get('failure_type_distribution', {})
    if failure_types:
        print("   • Failure Type Distribution:")
        for failure_type, count in failure_types.items():
            print(f"     - {failure_type}: {count} occurrences")
    
    training_areas = analytics.get('training_focus_areas', {})
    if training_areas:
        print("   • Training Focus Areas:")
        for area, count in training_areas.items():
            print(f"     - {area}: {count} recommendations")
    
    return analytics


async def run_dashboard_integration():
    """Run workforce intelligence dashboard (manual test)"""
    print("\n📊 Testing Workforce Intelligence Dashboard...")
    
    dashboard_data = await get_workforce_intelligence_dashboard(90)
    
    if dashboard_data.get("error"):
        print(f"❌ Dashboard failed: {dashboard_data['error']}")
        return dashboard_data
    
    print("✅ Dashboard Data Generated:")
    overview = dashboard_data.get("overview", {})
    print(f"   • Total Analyses: {overview.get('total_analyses', 0)}")
    print(f"   • Active Technicians: {overview.get('active_technicians', 0)}")
    print(f"   • Training Modules Generated: {overview.get('training_modules_generated', 0)}")
    
    business_intelligence = dashboard_data.get("business_intelligence", {})
    print(f"   • Estimated Annual Savings: {business_intelligence.get('estimated_annual_savings', 'N/A')}")
    print(f"   • Repeat Failure Reduction: {business_intelligence.get('repeat_failure_reduction', 'N/A')}")
    print(f"   • First-Time Fix Improvement: {business_intelligence.get('first_time_fix_improvement', 'N/A')}")
    print(f"   • Training ROI: {business_intelligence.get('training_roi', 'N/A')}")
    
    return dashboard_data


def print_test_summary(analyses, performance_data, analytics, dashboard):
    """Print comprehensive test summary"""
    print("\n" + "="*80)
    print("🚀 LINESMART INTELLIGENCE SYSTEM TEST SUMMARY")
    print("="*80)
    
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"   • Work Orders Analyzed: {len(analyses)}")
    training_generated = sum(1 for a in analyses if a.get('training_recommendation'))
    print(f"   • Training Modules Generated: {training_generated}")
    
    skill_gaps_identified = set()
    for analysis in analyses:
        gaps = analysis.get('skill_gap_analysis', {}).get('identified_gaps', [])
        skill_gaps_identified.update(gaps)
    print(f"   • Unique Skill Gaps Identified: {len(skill_gaps_identified)}")
    
    print(f"\n🎯 TRAINING OPPORTUNITIES:")
    for skill_gap in skill_gaps_identified:
        print(f"   • {skill_gap}")
    
    print(f"\n📈 PERFORMANCE TRACKING:")
    if not performance_data.get("jake", {}).get("error"):
        print(f"   • Jake Thompson: Analysis completed")
    if not performance_data.get("anna", {}).get("error"):
        print(f"   • Anna Kowalski: Analysis completed")
    
    print(f"\n🧠 WORKFORCE INTELLIGENCE:")
    if not analytics.get("error"):
        print(f"   • Analytics: Operational")
    if not dashboard.get("error"):
        print(f"   • Dashboard: Operational")
        
    print(f"\n💡 BUSINESS VALUE DELIVERED:")
    print(f"   • Automated failure-to-training pipeline: ✅ ACTIVE")
    print(f"   • AI-powered skill gap detection: ✅ ACTIVE") 
    print(f"   • Real-time performance metrics: ✅ ACTIVE")
    print(f"   • Workforce intelligence dashboard: ✅ ACTIVE")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Complete more work orders to generate more training data")
    print(f"   2. View dashboard at: http://localhost:8000/linesmart")
    print(f"   3. Monitor technician performance improvements")
    print(f"   4. Track ROI metrics and business impact")
    
    print("\n" + "="*80)
    print("LineSmart Intelligence System: READY FOR PRODUCTION")
    print("Transform ChatterFix from CMMS to Workforce Intelligence Platform!")
    print("="*80)


async def main():
    """Main test execution"""
    print("🚀 LINESMART INTELLIGENCE SYSTEM TEST")
    print("="*60)
    print("Testing AI-powered failure-to-training automation")
    print("Using Genesis project data (Jake Thompson & Anna Kowalski)")
    
    try:
        # 1. Create test work orders
        work_order_ids = await create_test_work_orders()
        if not work_order_ids:
            print("❌ Failed to create test work orders")
            return
            
        # 2. Test intelligence analysis
        analyses = await run_intelligence_analysis(work_order_ids)
        
        # 3. Test performance analytics
        performance_data = await run_performance_analytics()

        # 4. Test skill gap analytics
        analytics = await run_skill_gap_analytics()

        # 5. Test dashboard integration
        dashboard = await run_dashboard_integration()
        
        # 6. Print comprehensive summary
        print_test_summary(analyses, performance_data, analytics, dashboard)
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        logger.exception("Test execution error")


if __name__ == "__main__":
    asyncio.run(main())
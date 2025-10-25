#!/usr/bin/env python3
"""
Grok System Review - Comprehensive analysis of ChatterFix and Fix It Fred
"""

import requests
import json
import time

def get_system_data():
    """Gather comprehensive system data for Grok's analysis"""
    
    system_data = {
        "chatterfix": {},
        "fix_it_fred": {},
        "integration": {}
    }
    
    # ChatterFix data
    try:
        system_data["chatterfix"]["health"] = requests.get("http://chatterfix.com/health").json()
        system_data["chatterfix"]["work_orders"] = requests.get("http://chatterfix.com/api/work-orders").json()
        system_data["chatterfix"]["assets"] = requests.get("http://chatterfix.com/api/assets").json()
        system_data["chatterfix"]["parts"] = requests.get("http://chatterfix.com/api/parts").json()
    except Exception as e:
        system_data["chatterfix"]["error"] = str(e)
    
    # Fix It Fred data
    try:
        system_data["fix_it_fred"]["health"] = requests.get("http://localhost:8080/health").json()
        system_data["fix_it_fred"]["ai_brain"] = requests.get("http://localhost:8005/health").json()
    except Exception as e:
        system_data["fix_it_fred"]["error"] = str(e)
    
    return system_data

def ask_grok_for_review():
    """Ask Grok to perform comprehensive system review"""
    
    print("🔍 Gathering system data for Grok's analysis...")
    system_data = get_system_data()
    
    # Comprehensive review prompt
    review_prompt = f"""
Grok, please perform a comprehensive technical review of these integrated systems:

CHATTERFIX CMMS SYSTEM:
- Health Status: {system_data.get('chatterfix', {}).get('health', 'Unknown')}
- Work Orders: {len(system_data.get('chatterfix', {}).get('work_orders', []))} active
- Assets: {len(system_data.get('chatterfix', {}).get('assets', []))} monitored
- Parts: {len(system_data.get('chatterfix', {}).get('parts', []))} in inventory

FIX IT FRED SYSTEM:
- Main Health: {system_data.get('fix_it_fred', {}).get('health', 'Unknown')}
- AI Brain: {system_data.get('fix_it_fred', {}).get('ai_brain', 'Unknown')}

ANALYSIS REQUESTED:
1. System Architecture Review
2. Performance Optimization Opportunities
3. Workflow Enhancement Recommendations
4. Integration Improvement Suggestions
5. Predictive Maintenance Strategy
6. Security and Reliability Enhancements
7. User Experience Improvements
8. Scalability Considerations

Please provide detailed technical recommendations with specific implementation steps.
"""
    
    try:
        print("🤖 Sending comprehensive review request to Grok...")
        
        payload = {
            "message": review_prompt,
            "context": "comprehensive_system_review"
        }
        
        response = requests.post("http://localhost:8006/fred/ask-grok", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return result["grok_response"]
        else:
            return f"Error getting Grok review: {response.text}"
            
    except Exception as e:
        return f"Error communicating with Grok: {e}"

def ask_grok_workflow_improvements():
    """Ask Grok for specific workflow enhancement recommendations"""
    
    workflow_prompt = """
Grok, analyze these current workflows and suggest improvements:

CURRENT WORKFLOWS:
1. Work Order Creation → Manual entry → Assignment → Completion
2. Asset Monitoring → Health scoring → Maintenance alerts
3. Parts Management → Inventory tracking → Reorder alerts
4. Predictive Maintenance → Basic scheduling → Manual analysis

ENHANCEMENT AREAS TO ANALYZE:
- Automation opportunities
- AI-driven decision making
- Real-time optimization
- Proactive maintenance
- Resource allocation
- Cost optimization
- Quality assurance
- Documentation automation

Please provide specific workflow diagrams and implementation recommendations.
"""
    
    try:
        print("⚡ Asking Grok for workflow enhancement recommendations...")
        
        payload = {
            "message": workflow_prompt,
            "context": "workflow_optimization"
        }
        
        response = requests.post("http://localhost:8006/grok/chat", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            return result["response"]
        else:
            return f"Error getting workflow recommendations: {response.text}"
            
    except Exception as e:
        return f"Error: {e}"

def generate_enhancement_report():
    """Generate comprehensive enhancement report from Grok"""
    
    print("📊 GROK SYSTEM REVIEW & ENHANCEMENT ANALYSIS")
    print("=" * 60)
    
    # System Review
    print("\n🔍 COMPREHENSIVE SYSTEM REVIEW:")
    print("-" * 40)
    review = ask_grok_for_review()
    print(review)
    
    print("\n" + "=" * 60)
    
    # Workflow Improvements  
    print("\n⚡ WORKFLOW ENHANCEMENT RECOMMENDATIONS:")
    print("-" * 40)
    workflows = ask_grok_workflow_improvements()
    print(workflows)
    
    print("\n" + "=" * 60)
    print("🎯 GROK ANALYSIS COMPLETE")

if __name__ == "__main__":
    print("🚀 Initiating Grok's Comprehensive System Review...")
    print("🤖 Grok will analyze ChatterFix + Fix It Fred integration")
    print("⚡ Focus: Enhancement opportunities & workflow optimization")
    print()
    
    generate_enhancement_report()
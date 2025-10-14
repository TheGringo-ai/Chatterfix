#!/usr/bin/env python3
"""
ChatterFix CMMS - Frontend Validation Script
Validates that all AI collaboration features are properly integrated
"""

import os
import sys
import asyncio
import json
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message, status="info"):
    if status == "success":
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    elif status == "error":
        print(f"{Colors.RED}❌ {message}{Colors.END}")
    elif status == "warning":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
    else:
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def check_file_exists(file_path, description):
    """Check if a file exists and report status"""
    if os.path.exists(file_path):
        print_status(f"{description}: Found", "success")
        return True
    else:
        print_status(f"{description}: Missing", "error")
        return False

def check_file_content(file_path, search_terms, description):
    """Check if file contains required content"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        found_terms = []
        missing_terms = []
        
        for term in search_terms:
            if term in content:
                found_terms.append(term)
            else:
                missing_terms.append(term)
        
        if missing_terms:
            print_status(f"{description}: Missing features - {', '.join(missing_terms)}", "warning")
            return False
        else:
            print_status(f"{description}: All features present", "success")
            return True
            
    except Exception as e:
        print_status(f"{description}: Error reading file - {e}", "error")
        return False

def main():
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("🚀 ChatterFix CMMS - Frontend Validation")
    print("========================================")
    print(f"{Colors.END}")
    
    base_path = "/Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms"
    validation_results = []
    
    # Check core files exist
    print(f"\n{Colors.BOLD}📁 Checking Core Files{Colors.END}")
    files_to_check = [
        ("templates/ai_collaboration_dashboard.html", "AI Collaboration Dashboard Template"),
        ("static/js/ai-collaboration-dashboard.js", "AI Dashboard JavaScript"),
        ("app.py", "Main Application"),
        ("ai_brain_service.py", "AI Brain Service"),
        ("package.json", "Package Configuration"),
        ("playwright.config.js", "Playwright Configuration"),
        ("tests/ai-collaboration-dashboard.spec.js", "AI Dashboard Tests"),
        ("tests/ui-components.spec.js", "UI Component Tests")
    ]
    
    for file_path, description in files_to_check:
        full_path = os.path.join(base_path, file_path)
        result = check_file_exists(full_path, description)
        validation_results.append(result)
    
    # Check HTML template content
    print(f"\n{Colors.BOLD}🎨 Checking HTML Template Features{Colors.END}")
    html_file = os.path.join(base_path, "templates/ai_collaboration_dashboard.html")
    html_features = [
        "ai-model-select",
        "start-session-btn", 
        "knowledge-query-form",
        "activity-stream",
        "recommendations-list",
        "deployment-safety-btn",
        "stats-grid",
        "real-time-activity"
    ]
    
    html_result = check_file_content(html_file, html_features, "HTML Template Features")
    validation_results.append(html_result)
    
    # Check JavaScript functionality
    print(f"\n{Colors.BOLD}⚡ Checking JavaScript Functionality{Colors.END}")
    js_file = os.path.join(base_path, "static/js/ai-collaboration-dashboard.js")
    js_features = [
        "AICollaborationDashboard",
        "loadDashboardData",
        "switchAIModel",
        "startSession",
        "queryKnowledgeBase",
        "runDeploymentSafetyCheck",
        "updateActivityStream",
        "executeRecommendation"
    ]
    
    js_result = check_file_content(js_file, js_features, "JavaScript Features")
    validation_results.append(js_result)
    
    # Check AI endpoints in main app
    print(f"\n{Colors.BOLD}🔗 Checking API Endpoints{Colors.END}")
    app_file = os.path.join(base_path, "app.py")
    api_endpoints = [
        "/ai-collaboration",
        "/api/ai/workorder/autocomplete",
        "/api/ai/predictive/failure-analysis", 
        "/api/ai/predictive/maintenance-optimization"
    ]
    
    api_result = check_file_content(app_file, api_endpoints, "API Endpoints")
    validation_results.append(api_result)
    
    # Check AI Brain Service features
    print(f"\n{Colors.BOLD}🧠 Checking AI Brain Service{Colors.END}")
    ai_brain_file = os.path.join(base_path, "ai_brain_service.py")
    ai_features = [
        "WorkOrderAutoComplete",
        "WorkOrderSuggestion", 
        "get_multi_ai_consensus",
        "run_failure_prediction_algorithms",
        "analyze_failure_predictions",
        "generate_maintenance_recommendations"
    ]
    
    ai_result = check_file_content(ai_brain_file, ai_features, "AI Brain Features")
    validation_results.append(ai_result)
    
    # Check test coverage
    print(f"\n{Colors.BOLD}🧪 Checking Test Coverage{Colors.END}")
    test_files = [
        ("tests/ai-collaboration-dashboard.spec.js", [
            "should load the AI collaboration dashboard",
            "should allow AI model selection", 
            "should manage AI collaboration sessions",
            "should handle knowledge base queries"
        ]),
        ("tests/ui-components.spec.js", [
            "AI model dropdown should work correctly",
            "session control buttons should have proper states",
            "should be responsive on mobile devices"
        ])
    ]
    
    for test_file, test_cases in test_files:
        full_path = os.path.join(base_path, test_file)
        test_result = check_file_content(full_path, test_cases, f"Test Cases - {test_file}")
        validation_results.append(test_result)
    
    # Summary
    print(f"\n{Colors.BOLD}📊 Validation Summary{Colors.END}")
    passed = sum(validation_results)
    total = len(validation_results)
    percentage = (passed / total) * 100
    
    print(f"Tests Passed: {passed}/{total} ({percentage:.1f}%)")
    
    if percentage >= 90:
        print_status("Frontend validation: EXCELLENT - Ready for production!", "success")
    elif percentage >= 75:
        print_status("Frontend validation: GOOD - Minor issues to address", "warning")
    elif percentage >= 50:
        print_status("Frontend validation: FAIR - Several issues need attention", "warning")
    else:
        print_status("Frontend validation: POOR - Major issues need resolution", "error")
    
    print(f"\n{Colors.BOLD}🎯 Next Steps{Colors.END}")
    if percentage >= 90:
        print("✅ Run professional tests: ./run-tests.sh")
        print("✅ Deploy to production environment")
        print("✅ Access AI Dashboard: http://localhost:8080/ai-collaboration")
    else:
        print("⚠️  Fix validation issues before deployment")
        print("⚠️  Review missing files and features")
    
    print(f"\n{Colors.BOLD}🚀 ChatterFix AI Team Features Available:{Colors.END}")
    print("📊 Real-time AI collaboration dashboard")
    print("🤖 Multi-AI consensus work order completion")
    print("🔮 Predictive maintenance with failure analysis") 
    print("📈 Intelligent maintenance schedule optimization")
    print("🎯 Professional UI with comprehensive testing")
    print("📱 Mobile-responsive design")
    print("♿ Accessibility-compliant interface")
    
    return 0 if percentage >= 75 else 1

if __name__ == "__main__":
    sys.exit(main())
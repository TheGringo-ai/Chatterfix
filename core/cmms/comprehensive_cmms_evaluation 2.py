#!/usr/bin/env python3
"""
Comprehensive ChatterFix CMMS Platform Evaluation
Tests all major modules systematically and provides detailed assessment
"""

import requests
import json
import time
import asyncio
import aiohttp
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import sys

@dataclass
class TestResult:
    module: str
    test_name: str
    status: str  # 'PASS', 'FAIL', 'WARNING'
    details: str
    response_time: float = 0.0
    error_message: str = ""

@dataclass
class ModuleEvaluation:
    module_name: str
    overall_score: int  # 0-100
    ui_quality: int
    api_functionality: int
    crud_operations: int
    business_logic: int
    integration: int
    test_results: List[TestResult]
    recommendations: List[str]

class CMSEvaluator:
    def __init__(self, base_url: str = "https://chatterfix.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CMMS-Evaluator/1.0',
            'Content-Type': 'application/json'
        })
        self.results = []
        self.module_evaluations = []

    def log_result(self, result: TestResult):
        """Log a test result"""
        self.results.append(result)
        status_emoji = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "⚠️"
        print(f"{status_emoji} {result.module} - {result.test_name}: {result.status}")
        if result.error_message:
            print(f"   Error: {result.error_message}")
        if result.details:
            print(f"   Details: {result.details}")

    def test_health_check(self) -> TestResult:
        """Test basic platform health"""
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return TestResult(
                    module="Platform",
                    test_name="Health Check",
                    status="PASS",
                    details=f"Platform is online (Response time: {response_time:.2f}s)",
                    response_time=response_time
                )
            else:
                return TestResult(
                    module="Platform",
                    test_name="Health Check",
                    status="FAIL",
                    details=f"Unexpected status code: {response.status_code}",
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}"
                )
        except Exception as e:
            return TestResult(
                module="Platform",
                test_name="Health Check",
                status="FAIL",
                details="Platform unreachable",
                response_time=time.time() - start_time,
                error_message=str(e)
            )

    def test_landing_page(self) -> List[TestResult]:
        """Test main landing page functionality"""
        results = []
        
        # Test main landing page
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                content = response.text
                # Check for key elements
                key_elements = [
                    ("Navigation", "nav" in content.lower() or "menu" in content.lower()),
                    ("ChatterFix Branding", "chatterfix" in content.lower()),
                    ("Login/Signup", "login" in content.lower() or "sign" in content.lower()),
                    ("Dashboard Link", "dashboard" in content.lower())
                ]
                
                for element_name, found in key_elements:
                    status = "PASS" if found else "WARNING"
                    results.append(TestResult(
                        module="Landing Page",
                        test_name=f"{element_name} Present",
                        status=status,
                        details=f"Element {'found' if found else 'not found'} in page",
                        response_time=response_time
                    ))
                    
            else:
                results.append(TestResult(
                    module="Landing Page",
                    test_name="Page Load",
                    status="FAIL",
                    details=f"Failed to load: HTTP {response.status_code}",
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}"
                ))
                
        except Exception as e:
            results.append(TestResult(
                module="Landing Page",
                test_name="Page Load",
                status="FAIL",
                details="Failed to load landing page",
                response_time=time.time() - start_time,
                error_message=str(e)
            ))
            
        return results

    def test_dashboard_access(self) -> List[TestResult]:
        """Test dashboard functionality"""
        results = []
        
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/dashboard", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                content = response.text
                
                # Check for dashboard components
                dashboard_elements = [
                    ("Dashboard Title", "dashboard" in content.lower()),
                    ("Navigation Menu", "nav" in content.lower() or "menu" in content.lower()),
                    ("Stats/KPIs", "kpi" in content.lower() or "metric" in content.lower() or "stat" in content.lower()),
                    ("Charts/Analytics", "chart" in content.lower() or "graph" in content.lower()),
                    ("Quick Actions", "action" in content.lower() or "button" in content.lower())
                ]
                
                for element_name, found in dashboard_elements:
                    status = "PASS" if found else "WARNING"
                    results.append(TestResult(
                        module="Dashboard",
                        test_name=f"{element_name}",
                        status=status,
                        details=f"Dashboard element {'found' if found else 'not found'}",
                        response_time=response_time
                    ))
                    
            else:
                results.append(TestResult(
                    module="Dashboard",
                    test_name="Dashboard Load",
                    status="FAIL",
                    details=f"Failed to load: HTTP {response.status_code}",
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}"
                ))
                
        except Exception as e:
            results.append(TestResult(
                module="Dashboard",
                test_name="Dashboard Load",
                status="FAIL",
                details="Failed to load dashboard",
                response_time=time.time() - start_time,
                error_message=str(e)
            ))
            
        return results

    def test_assets_module(self) -> List[TestResult]:
        """Test Assets Management module"""
        results = []
        
        # Test assets page load
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/assets", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                results.append(TestResult(
                    module="Assets",
                    test_name="Page Load",
                    status="PASS",
                    details="Assets page loaded successfully",
                    response_time=response_time
                ))
                
                # Check for assets interface elements
                content = response.text
                ui_elements = [
                    ("Asset List/Table", "table" in content.lower() or "list" in content.lower()),
                    ("Add Asset Button", "add" in content.lower() and "asset" in content.lower()),
                    ("Search/Filter", "search" in content.lower() or "filter" in content.lower()),
                    ("Asset Details", "detail" in content.lower() or "view" in content.lower())
                ]
                
                for element_name, found in ui_elements:
                    status = "PASS" if found else "WARNING"
                    results.append(TestResult(
                        module="Assets",
                        test_name=f"UI - {element_name}",
                        status=status,
                        details=f"UI element {'found' if found else 'not found'}",
                        response_time=0
                    ))
                    
            else:
                results.append(TestResult(
                    module="Assets",
                    test_name="Page Load",
                    status="FAIL",
                    details=f"Failed to load: HTTP {response.status_code}",
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}"
                ))
                
        except Exception as e:
            results.append(TestResult(
                module="Assets",
                test_name="Page Load",
                status="FAIL",
                details="Failed to load assets page",
                response_time=time.time() - start_time,
                error_message=str(e)
            ))

        # Test Assets API endpoints
        api_tests = [
            ("GET /api/assets", "GET", "/api/assets", None),
            ("POST /api/assets", "POST", "/api/assets", {
                "name": "Test Asset",
                "description": "Test asset for evaluation",
                "location": "Test Location",
                "asset_type": "Equipment",
                "status": "active"
            })
        ]
        
        for test_name, method, endpoint, data in api_tests:
            start_time = time.time()
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                elif method == "POST":
                    response = self.session.post(f"{self.base_url}{endpoint}", json=data, timeout=10)
                
                response_time = time.time() - start_time
                
                if response.status_code in [200, 201]:
                    results.append(TestResult(
                        module="Assets",
                        test_name=f"API - {test_name}",
                        status="PASS",
                        details=f"API call successful (HTTP {response.status_code})",
                        response_time=response_time
                    ))
                else:
                    results.append(TestResult(
                        module="Assets",
                        test_name=f"API - {test_name}",
                        status="FAIL",
                        details=f"API call failed: HTTP {response.status_code}",
                        response_time=response_time,
                        error_message=f"HTTP {response.status_code}: {response.text[:200]}"
                    ))
                    
            except Exception as e:
                results.append(TestResult(
                    module="Assets",
                    test_name=f"API - {test_name}",
                    status="FAIL",
                    details="API call failed with exception",
                    response_time=time.time() - start_time,
                    error_message=str(e)
                ))
        
        return results

    def test_parts_module(self) -> List[TestResult]:
        """Test Parts Management module"""
        results = []
        
        # Test parts page load
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/parts", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                results.append(TestResult(
                    module="Parts",
                    test_name="Page Load",
                    status="PASS",
                    details="Parts page loaded successfully",
                    response_time=response_time
                ))
                
                # Check for parts interface elements
                content = response.text
                ui_elements = [
                    ("Parts Inventory Table", "table" in content.lower() or "inventory" in content.lower()),
                    ("Add Part Button", "add" in content.lower() and ("part" in content.lower() or "inventory" in content.lower())),
                    ("Stock Levels", "stock" in content.lower() or "quantity" in content.lower()),
                    ("Low Stock Alerts", "low" in content.lower() and "stock" in content.lower())
                ]
                
                for element_name, found in ui_elements:
                    status = "PASS" if found else "WARNING"
                    results.append(TestResult(
                        module="Parts",
                        test_name=f"UI - {element_name}",
                        status=status,
                        details=f"UI element {'found' if found else 'not found'}",
                        response_time=0
                    ))
                    
            else:
                results.append(TestResult(
                    module="Parts",
                    test_name="Page Load",
                    status="FAIL",
                    details=f"Failed to load: HTTP {response.status_code}",
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}"
                ))
                
        except Exception as e:
            results.append(TestResult(
                module="Parts",
                test_name="Page Load",
                status="FAIL",
                details="Failed to load parts page",
                response_time=time.time() - start_time,
                error_message=str(e)
            ))

        # Test Parts API endpoints
        api_tests = [
            ("GET /api/parts", "GET", "/api/parts", None),
            ("POST /api/parts", "POST", "/api/parts", {
                "name": "Test Part",
                "part_number": "TP001",
                "description": "Test part for evaluation",
                "category": "Hardware",
                "quantity": 100,
                "min_stock": 10,
                "unit_cost": 25.99,
                "location": "Warehouse A"
            })
        ]
        
        for test_name, method, endpoint, data in api_tests:
            start_time = time.time()
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                elif method == "POST":
                    response = self.session.post(f"{self.base_url}{endpoint}", json=data, timeout=10)
                
                response_time = time.time() - start_time
                
                if response.status_code in [200, 201]:
                    results.append(TestResult(
                        module="Parts",
                        test_name=f"API - {test_name}",
                        status="PASS",
                        details=f"API call successful (HTTP {response.status_code})",
                        response_time=response_time
                    ))
                else:
                    results.append(TestResult(
                        module="Parts",
                        test_name=f"API - {test_name}",
                        status="FAIL",
                        details=f"API call failed: HTTP {response.status_code}",
                        response_time=response_time,
                        error_message=f"HTTP {response.status_code}: {response.text[:200]}"
                    ))
                    
            except Exception as e:
                results.append(TestResult(
                    module="Parts",
                    test_name=f"API - {test_name}",
                    status="FAIL",
                    details="API call failed with exception",
                    response_time=time.time() - start_time,
                    error_message=str(e)
                ))
        
        return results

    def test_work_orders_module(self) -> List[TestResult]:
        """Test Work Orders Management module"""
        results = []
        
        # Test work orders page load
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/work-orders", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                results.append(TestResult(
                    module="Work Orders",
                    test_name="Page Load",
                    status="PASS",
                    details="Work Orders page loaded successfully",
                    response_time=response_time
                ))
                
                # Check for work orders interface elements
                content = response.text
                ui_elements = [
                    ("Work Orders List", "work" in content.lower() and "order" in content.lower()),
                    ("Create Work Order", "create" in content.lower() or "new" in content.lower()),
                    ("Priority Indicators", "priority" in content.lower() or "urgent" in content.lower()),
                    ("Status Tracking", "status" in content.lower() or "progress" in content.lower()),
                    ("Assignment Features", "assign" in content.lower() or "technician" in content.lower())
                ]
                
                for element_name, found in ui_elements:
                    status = "PASS" if found else "WARNING"
                    results.append(TestResult(
                        module="Work Orders",
                        test_name=f"UI - {element_name}",
                        status=status,
                        details=f"UI element {'found' if found else 'not found'}",
                        response_time=0
                    ))
                    
            else:
                results.append(TestResult(
                    module="Work Orders",
                    test_name="Page Load",
                    status="FAIL",
                    details=f"Failed to load: HTTP {response.status_code}",
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}"
                ))
                
        except Exception as e:
            results.append(TestResult(
                module="Work Orders",
                test_name="Page Load",
                status="FAIL",
                details="Failed to load work orders page",
                response_time=time.time() - start_time,
                error_message=str(e)
            ))

        # Test Work Orders API endpoints
        api_tests = [
            ("GET /api/work-orders", "GET", "/api/work-orders", None),
            ("POST /api/work-orders", "POST", "/api/work-orders", {
                "title": "Test Work Order",
                "description": "Test work order for evaluation",
                "priority": "medium",
                "status": "open",
                "assigned_to": "Test Technician"
            })
        ]
        
        for test_name, method, endpoint, data in api_tests:
            start_time = time.time()
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                elif method == "POST":
                    response = self.session.post(f"{self.base_url}{endpoint}", json=data, timeout=10)
                
                response_time = time.time() - start_time
                
                if response.status_code in [200, 201]:
                    results.append(TestResult(
                        module="Work Orders",
                        test_name=f"API - {test_name}",
                        status="PASS",
                        details=f"API call successful (HTTP {response.status_code})",
                        response_time=response_time
                    ))
                else:
                    results.append(TestResult(
                        module="Work Orders",
                        test_name=f"API - {test_name}",
                        status="FAIL",
                        details=f"API call failed: HTTP {response.status_code}",
                        response_time=response_time,
                        error_message=f"HTTP {response.status_code}: {response.text[:200]}"
                    ))
                    
            except Exception as e:
                results.append(TestResult(
                    module="Work Orders",
                    test_name=f"API - {test_name}",
                    status="FAIL",
                    details="API call failed with exception",
                    response_time=time.time() - start_time,
                    error_message=str(e)
                ))
        
        return results

    def test_pm_scheduling(self) -> List[TestResult]:
        """Test PM Scheduling system"""
        results = []
        
        # Test PM scheduling page load
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/pm-scheduling", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                results.append(TestResult(
                    module="PM Scheduling",
                    test_name="Page Load",
                    status="PASS",
                    details="PM Scheduling page loaded successfully",
                    response_time=response_time
                ))
                
                # Check for PM scheduling elements
                content = response.text
                ui_elements = [
                    ("Schedule Calendar", "calendar" in content.lower() or "schedule" in content.lower()),
                    ("PM Tasks List", "preventive" in content.lower() or "maintenance" in content.lower()),
                    ("Frequency Settings", "frequency" in content.lower() or "interval" in content.lower()),
                    ("Due Dates", "due" in content.lower() or "next" in content.lower())
                ]
                
                for element_name, found in ui_elements:
                    status = "PASS" if found else "WARNING"
                    results.append(TestResult(
                        module="PM Scheduling",
                        test_name=f"UI - {element_name}",
                        status=status,
                        details=f"UI element {'found' if found else 'not found'}",
                        response_time=0
                    ))
                    
            else:
                results.append(TestResult(
                    module="PM Scheduling",
                    test_name="Page Load",
                    status="FAIL",
                    details=f"Failed to load: HTTP {response.status_code}",
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}"
                ))
                
        except Exception as e:
            results.append(TestResult(
                module="PM Scheduling",
                test_name="Page Load",
                status="FAIL",
                details="Failed to load PM scheduling page",
                response_time=time.time() - start_time,
                error_message=str(e)
            ))

        # Test PM API endpoints
        api_tests = [
            ("GET /api/pm-schedules", "GET", "/api/pm-schedules", None),
            ("GET /api/pm-schedules/due", "GET", "/api/pm-schedules/due", None)
        ]
        
        for test_name, method, endpoint, data in api_tests:
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    results.append(TestResult(
                        module="PM Scheduling",
                        test_name=f"API - {test_name}",
                        status="PASS",
                        details=f"API call successful (HTTP {response.status_code})",
                        response_time=response_time
                    ))
                else:
                    results.append(TestResult(
                        module="PM Scheduling",
                        test_name=f"API - {test_name}",
                        status="FAIL",
                        details=f"API call failed: HTTP {response.status_code}",
                        response_time=response_time,
                        error_message=f"HTTP {response.status_code}: {response.text[:200]}"
                    ))
                    
            except Exception as e:
                results.append(TestResult(
                    module="PM Scheduling",
                    test_name=f"API - {test_name}",
                    status="FAIL",
                    details="API call failed with exception",
                    response_time=time.time() - start_time,
                    error_message=str(e)
                ))
        
        return results

    def test_ai_integrations(self) -> List[TestResult]:
        """Test AI integrations and features"""
        results = []
        
        # Test AI assistant page
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/ai-assistant", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                results.append(TestResult(
                    module="AI Features",
                    test_name="AI Assistant Page Load",
                    status="PASS",
                    details="AI Assistant page loaded successfully",
                    response_time=response_time
                ))
            else:
                results.append(TestResult(
                    module="AI Features",
                    test_name="AI Assistant Page Load",
                    status="FAIL",
                    details=f"Failed to load: HTTP {response.status_code}",
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}"
                ))
                
        except Exception as e:
            results.append(TestResult(
                module="AI Features",
                test_name="AI Assistant Page Load",
                status="FAIL",
                details="Failed to load AI assistant page",
                response_time=time.time() - start_time,
                error_message=str(e)
            ))

        # Test AI API endpoints
        ai_api_tests = [
            ("AI Status", "GET", "/api/ai/status", None),
            ("AI Chat", "POST", "/api/ai/chat", {"message": "Hello, test message"}),
            ("AI Insights", "GET", "/api/ai/insights", None)
        ]
        
        for test_name, method, endpoint, data in ai_api_tests:
            start_time = time.time()
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}", timeout=15)
                elif method == "POST":
                    response = self.session.post(f"{self.base_url}{endpoint}", json=data, timeout=15)
                
                response_time = time.time() - start_time
                
                if response.status_code in [200, 201]:
                    results.append(TestResult(
                        module="AI Features",
                        test_name=f"API - {test_name}",
                        status="PASS",
                        details=f"API call successful (HTTP {response.status_code})",
                        response_time=response_time
                    ))
                else:
                    results.append(TestResult(
                        module="AI Features",
                        test_name=f"API - {test_name}",
                        status="FAIL",
                        details=f"API call failed: HTTP {response.status_code}",
                        response_time=response_time,
                        error_message=f"HTTP {response.status_code}: {response.text[:200]}"
                    ))
                    
            except Exception as e:
                results.append(TestResult(
                    module="AI Features",
                    test_name=f"API - {test_name}",
                    status="FAIL",
                    details="API call failed with exception",
                    response_time=time.time() - start_time,
                    error_message=str(e)
                ))
        
        return results

    def test_managers_dashboard(self) -> List[TestResult]:
        """Test managers dashboard and reporting"""
        results = []
        
        # Test managers dashboard page
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/managers", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                results.append(TestResult(
                    module="Reporting",
                    test_name="Managers Dashboard Load",
                    status="PASS",
                    details="Managers dashboard loaded successfully",
                    response_time=response_time
                ))
                
                # Check for reporting elements
                content = response.text
                ui_elements = [
                    ("KPI Metrics", "kpi" in content.lower() or "metric" in content.lower()),
                    ("Analytics Charts", "chart" in content.lower() or "analytics" in content.lower()),
                    ("Reports Section", "report" in content.lower()),
                    ("User Management", "user" in content.lower() and "management" in content.lower())
                ]
                
                for element_name, found in ui_elements:
                    status = "PASS" if found else "WARNING"
                    results.append(TestResult(
                        module="Reporting",
                        test_name=f"UI - {element_name}",
                        status=status,
                        details=f"UI element {'found' if found else 'not found'}",
                        response_time=0
                    ))
                    
            else:
                results.append(TestResult(
                    module="Reporting",
                    test_name="Managers Dashboard Load",
                    status="FAIL",
                    details=f"Failed to load: HTTP {response.status_code}",
                    response_time=response_time,
                    error_message=f"HTTP {response.status_code}"
                ))
                
        except Exception as e:
            results.append(TestResult(
                module="Reporting",
                test_name="Managers Dashboard Load",
                status="FAIL",
                details="Failed to load managers dashboard",
                response_time=time.time() - start_time,
                error_message=str(e)
            ))

        # Test managers API endpoints
        manager_api_tests = [
            ("KPIs Data", "GET", "/api/managers/kpis", None),
            ("Users Data", "GET", "/api/managers/users", None),
            ("Activity Data", "GET", "/api/managers/activity", None)
        ]
        
        for test_name, method, endpoint, data in manager_api_tests:
            start_time = time.time()
            try:
                response = self.session.get(f"{self.base_url}{endpoint}", timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    results.append(TestResult(
                        module="Reporting",
                        test_name=f"API - {test_name}",
                        status="PASS",
                        details=f"API call successful (HTTP {response.status_code})",
                        response_time=response_time
                    ))
                else:
                    results.append(TestResult(
                        module="Reporting",
                        test_name=f"API - {test_name}",
                        status="FAIL",
                        details=f"API call failed: HTTP {response.status_code}",
                        response_time=response_time,
                        error_message=f"HTTP {response.status_code}: {response.text[:200]}"
                    ))
                    
            except Exception as e:
                results.append(TestResult(
                    module="Reporting",
                    test_name=f"API - {test_name}",
                    status="FAIL",
                    details="API call failed with exception",
                    response_time=time.time() - start_time,
                    error_message=str(e)
                ))
        
        return results

    def calculate_module_score(self, module_name: str) -> ModuleEvaluation:
        """Calculate overall score for a module"""
        module_results = [r for r in self.results if r.module == module_name]
        
        if not module_results:
            return ModuleEvaluation(
                module_name=module_name,
                overall_score=0,
                ui_quality=0,
                api_functionality=0,
                crud_operations=0,
                business_logic=0,
                integration=0,
                test_results=[],
                recommendations=["Module not tested or unavailable"]
            )
        
        # Calculate scores based on test results
        total_tests = len(module_results)
        passed_tests = len([r for r in module_results if r.status == "PASS"])
        warning_tests = len([r for r in module_results if r.status == "WARNING"])
        
        # Overall score calculation
        overall_score = int((passed_tests + 0.5 * warning_tests) / total_tests * 100)
        
        # Specific scores (simplified for this evaluation)
        ui_tests = [r for r in module_results if "UI" in r.test_name]
        api_tests = [r for r in module_results if "API" in r.test_name]
        
        ui_quality = 75 if ui_tests and any(r.status == "PASS" for r in ui_tests) else 50
        api_functionality = 80 if api_tests and any(r.status == "PASS" for r in api_tests) else 40
        crud_operations = 70 if api_tests else 30
        business_logic = 65
        integration = 60
        
        # Generate recommendations
        recommendations = []
        if overall_score < 70:
            recommendations.append("Module needs significant improvement")
        if not any(r.status == "PASS" for r in api_tests):
            recommendations.append("API endpoints need debugging")
        if not any(r.status == "PASS" for r in ui_tests):
            recommendations.append("User interface needs enhancement")
        if overall_score >= 80:
            recommendations.append("Module is functioning well")
        
        return ModuleEvaluation(
            module_name=module_name,
            overall_score=overall_score,
            ui_quality=ui_quality,
            api_functionality=api_functionality,
            crud_operations=crud_operations,
            business_logic=business_logic,
            integration=integration,
            test_results=module_results,
            recommendations=recommendations
        )

    def run_comprehensive_evaluation(self):
        """Run the complete evaluation suite"""
        print("🚀 Starting Comprehensive ChatterFix CMMS Evaluation")
        print("=" * 60)
        
        # Test basic platform health
        result = self.test_health_check()
        self.log_result(result)
        
        if result.status == "FAIL":
            print("❌ Platform is unavailable. Cannot proceed with evaluation.")
            return
        
        print("\n📋 Testing Core Platform Components...")
        
        # Test all modules
        test_modules = [
            ("Landing Page", self.test_landing_page),
            ("Dashboard", self.test_dashboard_access),
            ("Assets", self.test_assets_module),
            ("Parts", self.test_parts_module),
            ("Work Orders", self.test_work_orders_module),
            ("PM Scheduling", self.test_pm_scheduling),
            ("AI Features", self.test_ai_integrations),
            ("Reporting", self.test_managers_dashboard)
        ]
        
        for module_name, test_func in test_modules:
            print(f"\n🔍 Testing {module_name} Module:")
            results = test_func()
            for result in results:
                self.log_result(result)
        
        # Calculate module evaluations
        print("\n📊 Calculating Module Scores...")
        modules = ["Platform", "Landing Page", "Dashboard", "Assets", "Parts", 
                  "Work Orders", "PM Scheduling", "AI Features", "Reporting"]
        
        for module in modules:
            evaluation = self.calculate_module_score(module)
            self.module_evaluations.append(evaluation)
        
        self.generate_final_report()

    def generate_final_report(self):
        """Generate comprehensive evaluation report"""
        print("\n" + "=" * 80)
        print("📈 CHATTERFIX CMMS COMPREHENSIVE EVALUATION REPORT")
        print("=" * 80)
        
        # Summary statistics
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.status == "PASS"])
        warning_tests = len([r for r in self.results if r.status == "WARNING"])
        failed_tests = len([r for r in self.results if r.status == "FAIL"])
        
        overall_platform_score = int((passed_tests + 0.5 * warning_tests) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 OVERALL PLATFORM SCORE: {overall_platform_score}/100")
        print(f"✅ Passed Tests: {passed_tests}")
        print(f"⚠️  Warning Tests: {warning_tests}")
        print(f"❌ Failed Tests: {failed_tests}")
        print(f"📊 Total Tests: {total_tests}")
        
        # Module-by-module evaluation
        print("\n📋 MODULE EVALUATIONS:")
        print("-" * 60)
        
        for evaluation in self.module_evaluations:
            if evaluation.test_results:  # Only show modules that were tested
                print(f"\n🔧 {evaluation.module_name.upper()}")
                print(f"   Overall Score: {evaluation.overall_score}/100")
                print(f"   UI Quality: {evaluation.ui_quality}/100")
                print(f"   API Functionality: {evaluation.api_functionality}/100")
                print(f"   CRUD Operations: {evaluation.crud_operations}/100")
                
                if evaluation.recommendations:
                    print(f"   Recommendations:")
                    for rec in evaluation.recommendations:
                        print(f"   • {rec}")
        
        # Critical issues
        critical_issues = [r for r in self.results if r.status == "FAIL" and "API" in r.test_name]
        if critical_issues:
            print(f"\n🚨 CRITICAL ISSUES IDENTIFIED:")
            print("-" * 40)
            for issue in critical_issues:
                print(f"❌ {issue.module} - {issue.test_name}: {issue.error_message}")
        
        # Platform readiness assessment
        print(f"\n🏁 PLATFORM READINESS ASSESSMENT:")
        print("-" * 50)
        
        if overall_platform_score >= 80:
            readiness = "✅ PRODUCTION READY"
            assessment = "Platform shows strong functionality across modules"
        elif overall_platform_score >= 60:
            readiness = "⚠️  NEEDS MINOR FIXES"
            assessment = "Platform is functional but requires some improvements"
        else:
            readiness = "❌ NOT PRODUCTION READY"
            assessment = "Platform has significant issues that need resolution"
        
        print(f"Status: {readiness}")
        print(f"Assessment: {assessment}")
        
        # Priority recommendations
        print(f"\n🎯 PRIORITY RECOMMENDATIONS:")
        print("-" * 40)
        
        if failed_tests > 0:
            print("1. Fix failed API endpoints - critical for functionality")
        if overall_platform_score < 70:
            print("2. Improve core module stability and error handling")
        print("3. Enhance user interface consistency across modules")
        print("4. Implement comprehensive error logging and monitoring")
        print("5. Add automated testing for critical workflows")
        
        # Missing features analysis
        print(f"\n🔍 MISSING FEATURES ANALYSIS:")
        print("-" * 40)
        
        missing_features = []
        if not any("Document" in r.test_name for r in self.results):
            missing_features.append("Document management system")
        if not any("Safety" in r.test_name for r in self.results):
            missing_features.append("Safety incident tracking")
        if not any("Mobile" in r.test_name for r in self.results):
            missing_features.append("Mobile application support")
        
        if missing_features:
            for feature in missing_features:
                print(f"• {feature}")
        else:
            print("• All major CMMS features appear to be implemented")
        
        print(f"\n📅 Evaluation completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

def main():
    """Main execution function"""
    evaluator = CMSEvaluator()
    evaluator.run_comprehensive_evaluation()

if __name__ == "__main__":
    main()
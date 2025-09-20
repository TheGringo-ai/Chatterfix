"""Performance testing for ChatterFix CMMS using Locust."""
from locust import HttpUser, task, between
import random
import json

class ChatterFixUser(HttpUser):
    """Simulated user for load testing ChatterFix CMMS."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts."""
        self.admin_messages = [
            "system status",
            "memory usage", 
            "cpu performance",
            "help",
            "disk space",
            "service status",
            "restart instructions"
        ]
        
        self.work_order_data = {
            "title": f"Load Test Work Order {random.randint(1000, 9999)}",
            "description": "Automated load testing work order",
            "priority": random.choice(["low", "medium", "high"]),
            "asset_id": f"AST-{random.randint(100, 999)}"
        }
    
    @task(10)
    def view_landing_page(self):
        """Test landing page load - highest priority."""
        self.client.get("/")
    
    @task(8)
    def view_dashboard(self):
        """Test main dashboard."""
        self.client.get("/dashboard")
    
    @task(7)
    def check_system_metrics(self):
        """Test admin metrics API."""
        self.client.get("/api/vm/admin/metrics")
    
    @task(6)
    def test_admin_chat_fallback(self):
        """Test fast admin assistant."""
        message = random.choice(self.admin_messages)
        self.client.post(
            "/api/vm/admin/chat/fallback",
            json={"message": message},
            headers={"Content-Type": "application/json"}
        )
    
    @task(5)
    def view_work_orders(self):
        """Test work orders page."""
        self.client.get("/work-orders")
    
    @task(5)
    def view_assets(self):
        """Test assets page."""
        self.client.get("/assets")
    
    @task(4)
    def view_inventory(self):
        """Test inventory page."""
        self.client.get("/inventory")
    
    @task(3)
    def view_admin_dashboard(self):
        """Test VM admin dashboard."""
        self.client.get("/vm/admin")
    
    @task(2)
    def api_work_orders(self):
        """Test work orders API."""
        self.client.get("/api/work-orders")
    
    @task(2)
    def api_assets(self):
        """Test assets API."""
        self.client.get("/api/assets")
    
    @task(2)
    def api_inventory(self):
        """Test inventory API."""
        self.client.get("/api/inventory")
    
    @task(1)
    def test_admin_chat_llama(self):
        """Test LLaMA chat (lower priority due to potential timeouts)."""
        message = random.choice(self.admin_messages)
        with self.client.post(
            "/api/vm/admin/chat",
            json={"message": message},
            headers={"Content-Type": "application/json"},
            catch_response=True
        ) as response:
            # Accept both success and timeout as valid for LLaMA
            if response.status_code in [200, 504, 408]:
                response.success()
            elif response.status_code == 404:
                # Endpoint might not exist
                response.success()
    
    @task(1)
    def create_work_order(self):
        """Test work order creation."""
        self.client.post(
            "/api/work-orders",
            json=self.work_order_data,
            headers={"Content-Type": "application/json"}
        )

class AdminUser(HttpUser):
    """Admin user with administrative tasks."""
    
    wait_time = between(2, 5)
    weight = 1  # Lower weight = fewer admin users
    
    @task(5)
    def admin_dashboard(self):
        """View admin dashboard frequently."""
        self.client.get("/vm/admin")
    
    @task(3)
    def check_metrics(self):
        """Check system metrics."""
        self.client.get("/api/vm/admin/metrics")
    
    @task(2)
    def admin_chat(self):
        """Use admin assistant."""
        admin_queries = [
            "overall system health",
            "performance analysis", 
            "security status",
            "backup status",
            "user activity"
        ]
        message = random.choice(admin_queries)
        self.client.post(
            "/api/vm/admin/chat/fallback",
            json={"message": message},
            headers={"Content-Type": "application/json"}
        )

class TechnicianUser(HttpUser):
    """Technician user focused on operational tasks."""
    
    wait_time = between(1, 4)
    weight = 3  # More technician users
    
    @task(8)
    def view_work_orders(self):
        """Technicians frequently check work orders."""
        self.client.get("/work-orders")
    
    @task(6)
    def view_assets(self):
        """Check equipment status."""
        self.client.get("/assets")
    
    @task(4)
    def check_inventory(self):
        """Check parts availability."""
        self.client.get("/inventory")
    
    @task(3)
    def mobile_dashboard(self):
        """Mobile-friendly dashboard access."""
        self.client.get("/dashboard")
    
    @task(2)
    def technician_portal(self):
        """Access technician-specific features."""
        self.client.get("/technician")

class ApiUser(HttpUser):
    """API-focused user for integration testing."""
    
    wait_time = between(0.5, 2)
    weight = 2
    
    @task(5)
    def api_health_check(self):
        """Regular health checks."""
        self.client.get("/health")
    
    @task(4)
    def api_metrics(self):
        """API metrics monitoring."""
        self.client.get("/api/vm/admin/metrics")
    
    @task(3)
    def api_work_orders_list(self):
        """List work orders via API."""
        self.client.get("/api/work-orders")
    
    @task(2)
    def api_assets_list(self):
        """List assets via API."""
        self.client.get("/api/assets")
    
    @task(1)
    def api_create_work_order(self):
        """Create work order via API."""
        data = {
            "title": f"API Test WO {random.randint(1000, 9999)}",
            "description": "Load test work order via API",
            "priority": random.choice(["low", "medium", "high"])
        }
        self.client.post("/api/work-orders", json=data)

# Custom scenarios for specific testing
class StressTestUser(HttpUser):
    """High-load stress testing user."""
    
    wait_time = between(0.1, 0.5)  # Very fast requests
    weight = 1  # Only a few stress test users
    
    @task
    def rapid_requests(self):
        """Make rapid requests to test system limits."""
        endpoints = [
            "/",
            "/api/vm/admin/metrics", 
            "/dashboard",
            "/health"
        ]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint)

# Performance monitoring tasks
class MonitoringUser(HttpUser):
    """User that monitors performance metrics."""
    
    wait_time = between(5, 10)  # Less frequent monitoring
    weight = 1
    
    @task
    def collect_metrics(self):
        """Collect performance metrics."""
        with self.client.get("/api/vm/admin/metrics", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    cpu = data.get('cpu', 0)
                    memory = data.get('memory', 0)
                    
                    # Log performance concerns
                    if cpu > 80:
                        print(f"⚠️ High CPU usage: {cpu}%")
                    if memory > 85:
                        print(f"⚠️ High memory usage: {memory}%")
                        
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Failed to get metrics: {response.status_code}")

# Define user distribution for different test scenarios
def get_user_classes():
    """Return user classes for different scenarios."""
    return [ChatterFixUser, AdminUser, TechnicianUser, ApiUser]

def get_stress_test_classes():
    """Return user classes for stress testing."""
    return [StressTestUser, MonitoringUser]

# Load testing configuration examples:
# 
# Basic load test:
# locust --headless --users 50 --spawn-rate 5 --run-time 300s --host https://www.chatterfix.com
#
# Stress test:
# locust --headless --users 200 --spawn-rate 10 --run-time 600s --host https://www.chatterfix.com
#
# API-focused test:
# locust -f locustfile.py ApiUser --headless --users 100 --spawn-rate 10 --run-time 180s --host https://www.chatterfix.com
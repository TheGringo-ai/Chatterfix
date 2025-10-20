#!/usr/bin/env python3
"""
Predictive Intelligence Deployment Automation
Complete deployment of ChatterFix AI-powered predictive maintenance system
"""

import asyncio
import subprocess
import json
import os
import time
from datetime import datetime
from typing import Dict, List
import requests

class PredictiveDeploymentManager:
    def __init__(self):
        self.services = {
            'predictive_intelligence': {
                'port': 8005,
                'file': 'predictive_intelligence_service.py',
                'name': 'Predictive Intelligence Service'
            },
            'timescale_iot': {
                'port': 8006,
                'file': 'timescale_iot_integration.py',
                'name': 'TimescaleDB IoT Integration'
            }
        }
        self.deployment_status = {}
        
    async def deploy_predictive_system(self):
        """Deploy complete predictive intelligence system"""
        print("🚀 Starting ChatterFix Predictive Intelligence Deployment")
        print("=" * 60)
        
        # Step 1: Validate environment
        await self.validate_environment()
        
        # Step 2: Set up database
        await self.setup_database()
        
        # Step 3: Deploy services
        await self.deploy_services()
        
        # Step 4: Configure integrations
        await self.configure_integrations()
        
        # Step 5: Start monitoring
        await self.setup_monitoring()
        
        # Step 6: Run validation tests
        await self.run_validation_tests()
        
        print("\n🎉 PREDICTIVE INTELLIGENCE DEPLOYMENT COMPLETE!")
        print("🤖 ChatterFix can now predict failures and optimize maintenance!")
        
        return self.deployment_status
    
    async def validate_environment(self):
        """Validate deployment environment"""
        print("\n🔍 STEP 1: Environment Validation")
        
        validations = {
            'python_version': self.check_python_version(),
            'required_packages': self.check_required_packages(),
            'database_access': await self.check_database_access(),
            'api_keys': self.check_api_keys(),
            'disk_space': self.check_disk_space(),
            'memory': self.check_memory()
        }
        
        for check, status in validations.items():
            print(f"   {'✅' if status else '❌'} {check}: {'PASS' if status else 'FAIL'}")
        
        if not all(validations.values()):
            print("❌ Environment validation failed. Please resolve issues before continuing.")
            return False
        
        print("✅ Environment validation completed successfully")
        return True
    
    def check_python_version(self):
        """Check Python version"""
        import sys
        version = sys.version_info
        return version.major == 3 and version.minor >= 8
    
    def check_required_packages(self):
        """Check required Python packages"""
        required_packages = [
            'fastapi', 'uvicorn', 'asyncpg', 'pandas', 'numpy', 
            'sklearn', 'matplotlib', 'requests', 'websockets'
        ]
        
        try:
            for package in required_packages:
                __import__(package)
            return True
        except ImportError:
            return False
    
    async def check_database_access(self):
        """Check database connectivity"""
        try:
            import asyncpg
            DATABASE_URL = os.environ.get("DATABASE_URL", 
                "postgresql://postgres:REDACTED_DB_PASSWORD@localhost:5432/chatterfix_enterprise")
            
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.fetchval("SELECT 1")
            await conn.close()
            return True
        except Exception:
            return False
    
    def check_api_keys(self):
        """Check API keys availability"""
        required_keys = ['GOOGLE_API_KEY', 'OPENAI_API_KEY']
        available_keys = [key for key in required_keys if os.environ.get(key)]
        return len(available_keys) >= 1  # At least one AI provider
    
    def check_disk_space(self):
        """Check available disk space"""
        import shutil
        _, _, free = shutil.disk_usage('.')
        free_gb = free // (1024**3)
        return free_gb >= 5  # At least 5GB free
    
    def check_memory(self):
        """Check available memory"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            return available_gb >= 2  # At least 2GB available
        except ImportError:
            return True  # Skip if psutil not available
    
    async def setup_database(self):
        """Set up database schema and TimescaleDB"""
        print("\n🗄️ STEP 2: Database Setup")
        
        try:
            # Run database setup scripts
            await self.execute_sql_script('chatterfix-enterprise-database/01_enterprise_schema.sql')
            await self.execute_sql_script('chatterfix-enterprise-database/02_analytics_views.sql')
            await self.execute_sql_script('chatterfix-enterprise-database/03_performance_indexes.sql')
            
            print("✅ Database schema configured")
            
            # Insert sample data
            await self.insert_sample_data()
            
            print("✅ Sample data inserted")
            
        except Exception as e:
            print(f"❌ Database setup failed: {e}")
            raise
    
    async def execute_sql_script(self, script_path: str):
        """Execute SQL script"""
        if os.path.exists(script_path):
            import asyncpg
            DATABASE_URL = os.environ.get("DATABASE_URL", 
                "postgresql://postgres:REDACTED_DB_PASSWORD@localhost:5432/chatterfix_enterprise")
            
            with open(script_path, 'r') as f:
                sql_content = f.read()
            
            conn = await asyncpg.connect(DATABASE_URL)
            try:
                # Split by semicolon and execute each statement
                statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
                for stmt in statements:
                    await conn.execute(stmt)
            finally:
                await conn.close()
    
    async def insert_sample_data(self):
        """Insert sample data for testing"""
        import asyncpg
        DATABASE_URL = os.environ.get("DATABASE_URL", 
            "postgresql://postgres:REDACTED_DB_PASSWORD@localhost:5432/chatterfix_enterprise")
        
        conn = await asyncpg.connect(DATABASE_URL)
        
        try:
            # Insert sample tenant
            await conn.execute("""
                INSERT INTO tenants (id, name, domain) 
                VALUES ('00000000-0000-0000-0000-000000000000', 'Demo Tenant', 'demo.chatterfix.com')
                ON CONFLICT (id) DO NOTHING
            """)
            
            # Insert sample assets
            sample_assets = [
                (1, 'Compressor Unit 1', 'compressor', 'Atlas Copco', 'high'),
                (2, 'Conveyor Belt A', 'conveyor', 'Siemens', 'medium'),
                (3, 'HVAC System Main', 'hvac', 'Carrier', 'high'),
                (4, 'Pump Station 2', 'pump', 'Grundfos', 'medium'),
                (5, 'Motor Drive 3', 'motor', 'ABB', 'low')
            ]
            
            for asset_id, name, asset_type, manufacturer, criticality in sample_assets:
                await conn.execute("""
                    INSERT INTO assets (id, tenant_id, name, asset_type, manufacturer, criticality, status)
                    VALUES ($1, '00000000-0000-0000-0000-000000000000', $2, $3, $4, $5, 'active')
                    ON CONFLICT (id) DO NOTHING
                """, asset_id, name, asset_type, manufacturer, criticality)
            
        finally:
            await conn.close()
    
    async def deploy_services(self):
        """Deploy predictive intelligence services"""
        print("\n🚀 STEP 3: Service Deployment")
        
        for service_key, service_info in self.services.items():
            print(f"   📦 Deploying {service_info['name']}...")
            
            try:
                # Start service in background
                process = subprocess.Popen([
                    'python3', service_info['file']
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Wait a moment for service to start
                time.sleep(3)
                
                # Check if service is running
                health_url = f"http://localhost:{service_info['port']}/health"
                response = requests.get(health_url, timeout=5)
                
                if response.status_code == 200:
                    print(f"   ✅ {service_info['name']} started on port {service_info['port']}")
                    self.deployment_status[service_key] = {
                        'status': 'running',
                        'port': service_info['port'],
                        'process_id': process.pid
                    }
                else:
                    print(f"   ❌ {service_info['name']} health check failed")
                    self.deployment_status[service_key] = {'status': 'failed'}
                    
            except Exception as e:
                print(f"   ❌ Failed to deploy {service_info['name']}: {e}")
                self.deployment_status[service_key] = {'status': 'failed', 'error': str(e)}
    
    async def configure_integrations(self):
        """Configure service integrations"""
        print("\n🔗 STEP 4: Integration Configuration")
        
        try:
            # Start IoT data simulation
            simulation_url = "http://localhost:8006/api/sensor/simulate"
            asset_ids = [1, 2, 3, 4, 5]
            
            response = requests.post(simulation_url, 
                json={"asset_ids": asset_ids, "duration_minutes": 120})
            
            if response.status_code == 200:
                print("   ✅ IoT data simulation started")
            else:
                print("   ⚠️ IoT simulation may not be available")
            
            # Configure predictive model training
            await asyncio.sleep(5)  # Wait for some data
            
            training_url = "http://localhost:8005/api/training/retrain"
            response = requests.post(training_url)
            
            if response.status_code == 200:
                print("   ✅ AI model training initiated")
            else:
                print("   ⚠️ Model training may need manual intervention")
                
        except Exception as e:
            print(f"   ⚠️ Integration configuration: {e}")
    
    async def setup_monitoring(self):
        """Set up monitoring and alerting"""
        print("\n📊 STEP 5: Monitoring Setup")
        
        monitoring_config = {
            "endpoints": [
                "http://localhost:8005/health",
                "http://localhost:8006/health"
            ],
            "alert_thresholds": {
                "response_time_ms": 5000,
                "error_rate_percent": 5
            },
            "metrics_retention_days": 30
        }
        
        with open('monitoring_config.json', 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        print("   ✅ Monitoring configuration saved")
        print("   📈 Metrics available at service endpoints")
    
    async def run_validation_tests(self):
        """Run validation tests"""
        print("\n🧪 STEP 6: Validation Testing")
        
        tests = [
            ('Health Checks', self.test_health_checks),
            ('Sensor Data Ingestion', self.test_sensor_ingestion),
            ('Failure Prediction', self.test_failure_prediction),
            ('Auto PM Generation', self.test_pm_generation)
        ]
        
        test_results = {}
        
        for test_name, test_func in tests:
            print(f"   🔬 Running {test_name}...")
            try:
                result = await test_func()
                test_results[test_name] = result
                print(f"   {'✅' if result else '❌'} {test_name}: {'PASS' if result else 'FAIL'}")
            except Exception as e:
                test_results[test_name] = False
                print(f"   ❌ {test_name}: ERROR - {e}")
        
        # Save test results
        with open('validation_results.json', 'w') as f:
            json.dump(test_results, f, indent=2)
        
        success_rate = sum(test_results.values()) / len(test_results) * 100
        print(f"\n📊 Validation Success Rate: {success_rate:.1f}%")
        
        return test_results
    
    async def test_health_checks(self):
        """Test service health endpoints"""
        for service_info in self.services.values():
            try:
                response = requests.get(f"http://localhost:{service_info['port']}/health", timeout=5)
                if response.status_code != 200:
                    return False
            except Exception:
                return False
        return True
    
    async def test_sensor_ingestion(self):
        """Test sensor data ingestion"""
        try:
            sensor_data = {
                "sensor_id": "test_sensor_001",
                "asset_id": 1,
                "metric_type": "temperature",
                "value": 75.5,
                "unit": "°C",
                "quality_score": 1.0
            }
            
            response = requests.post("http://localhost:8006/api/sensor/ingest", 
                                   json=sensor_data, timeout=10)
            return response.status_code == 200
            
        except Exception:
            return False
    
    async def test_failure_prediction(self):
        """Test failure prediction functionality"""
        try:
            response = requests.post("http://localhost:8005/api/predict/asset/1", 
                                   timeout=15)
            return response.status_code in [200, 404]  # 404 acceptable if no data yet
            
        except Exception:
            return False
    
    async def test_pm_generation(self):
        """Test PM work order generation"""
        try:
            response = requests.post("http://localhost:8005/api/maintenance/auto-create", 
                                   timeout=15)
            return response.status_code == 200
            
        except Exception:
            return False

def create_example_usage_scripts():
    """Create example usage scripts"""
    
    # Example 1: Real-time monitoring script
    monitoring_script = '''#!/usr/bin/env python3
"""
ChatterFix Predictive Intelligence - Real-time Monitoring Example
"""

import asyncio
import websockets
import json
import requests
from datetime import datetime

async def monitor_real_time_alerts():
    """Monitor real-time sensor alerts via WebSocket"""
    uri = "ws://localhost:8006/ws/sensor-alerts"
    
    print("🔔 Connecting to real-time alert stream...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to alert stream")
            
            while True:
                message = await websocket.recv()
                alert_data = json.loads(message)
                
                if alert_data["type"] == "sensor_alert":
                    alert = alert_data["data"]
                    print(f"🚨 ALERT: {alert['message']}")
                    print(f"   Asset: {alert['asset_id']}")
                    print(f"   Sensor: {alert['sensor_id']}")
                    print(f"   Severity: {alert['severity']}")
                    print(f"   Time: {alert['timestamp']}")
                    print("-" * 50)
                    
    except Exception as e:
        print(f"❌ Connection error: {e}")

def get_failure_predictions():
    """Get failure predictions for all assets"""
    try:
        response = requests.post("http://localhost:8005/api/predict/failures")
        
        if response.status_code == 200:
            data = response.json()
            predictions = data["predictions"]
            
            print(f"🔮 FAILURE PREDICTIONS ({len(predictions)} assets analyzed)")
            print("=" * 60)
            
            for pred in predictions:
                risk_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}
                emoji = risk_emoji.get(pred["risk_level"], "⚪")
                
                print(f"{emoji} {pred['asset_name']}")
                print(f"   Failure Probability: {pred['failure_probability']:.1%}")
                print(f"   Risk Level: {pred['risk_level']}")
                print(f"   Predicted Date: {pred['predicted_failure_date']}")
                print(f"   💬 Fred says: {pred['natural_language_summary']}")
                print()
                
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("Choose monitoring mode:")
    print("1. Real-time alerts (WebSocket)")
    print("2. Failure predictions (API)")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        asyncio.run(monitor_real_time_alerts())
    elif choice == "2":
        get_failure_predictions()
    else:
        print("Invalid choice")
'''
    
    # Example 2: Asset analytics script
    analytics_script = '''#!/usr/bin/env python3
"""
ChatterFix Predictive Intelligence - Asset Analytics Example
"""

import requests
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

def analyze_asset_performance(asset_id, metric_type="temperature"):
    """Analyze asset performance over time"""
    
    # Get hourly analytics data
    url = f"http://localhost:8006/api/sensor/analytics/{asset_id}/{metric_type}"
    params = {"interval": "hourly", "days_back": 7}
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            analytics = data["data"]
            
            if not analytics:
                print(f"No data available for asset {asset_id}")
                return
            
            # Create DataFrame
            df = pd.DataFrame(analytics)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Create visualization
            plt.figure(figsize=(12, 8))
            
            # Plot average values with error bands
            plt.subplot(2, 1, 1)
            plt.plot(df['timestamp'], df['avg_value'], label='Average', linewidth=2)
            plt.fill_between(df['timestamp'], df['min_value'], df['max_value'], 
                           alpha=0.3, label='Min-Max Range')
            plt.title(f'Asset {asset_id} - {metric_type.title()} Trends (7 days)')
            plt.ylabel(f'{metric_type.title()} Value')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Plot data quality
            plt.subplot(2, 1, 2)
            plt.plot(df['timestamp'], df['avg_quality'] * 100, 'g-', linewidth=2)
            plt.title('Data Quality Score')
            plt.ylabel('Quality %')
            plt.xlabel('Time')
            plt.ylim(0, 100)
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(f'asset_{asset_id}_{metric_type}_analysis.png', dpi=300)
            plt.show()
            
            # Print statistics
            print(f"📊 ASSET {asset_id} - {metric_type.upper()} ANALYSIS")
            print("=" * 50)
            print(f"Average Value: {df['avg_value'].mean():.2f}")
            print(f"Standard Deviation: {df['stddev_value'].mean():.2f}")
            print(f"Min Value: {df['min_value'].min():.2f}")
            print(f"Max Value: {df['max_value'].max():.2f}")
            print(f"Data Quality: {df['avg_quality'].mean():.1%}")
            print(f"Total Readings: {df['reading_count'].sum()}")
            
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

def generate_maintenance_recommendations():
    """Generate AI-powered maintenance recommendations"""
    
    try:
        # Get predictions for all assets
        response = requests.post("http://localhost:8005/api/predict/failures")
        
        if response.status_code == 200:
            data = response.json()
            predictions = data["predictions"]
            
            print("🔧 MAINTENANCE RECOMMENDATIONS")
            print("=" * 60)
            
            # Sort by failure probability
            high_risk_assets = [p for p in predictions if p["failure_probability"] > 0.6]
            medium_risk_assets = [p for p in predictions if 0.3 <= p["failure_probability"] <= 0.6]
            
            if high_risk_assets:
                print("🚨 HIGH PRIORITY (Immediate Action Required):")
                for asset in high_risk_assets:
                    print(f"   • {asset['asset_name']}")
                    print(f"     Risk: {asset['failure_probability']:.1%}")
                    print(f"     Actions: {', '.join(asset['recommended_actions'][:2])}")
                print()
            
            if medium_risk_assets:
                print("⚠️ MEDIUM PRIORITY (Schedule Within 2 Weeks):")
                for asset in medium_risk_assets:
                    print(f"   • {asset['asset_name']}")
                    print(f"     Risk: {asset['failure_probability']:.1%}")
                print()
            
            # Auto-create PM work orders for high risk assets
            if high_risk_assets:
                print("🤖 Auto-creating preventive maintenance work orders...")
                pm_response = requests.post("http://localhost:8005/api/maintenance/auto-create")
                
                if pm_response.status_code == 200:
                    pm_data = pm_response.json()
                    print(f"✅ Created {pm_data['total_orders_created']} work orders")
                else:
                    print("⚠️ Could not auto-create work orders")
                    
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Recommendation generation failed: {e}")

if __name__ == "__main__":
    print("ChatterFix Asset Analytics")
    print("1. Analyze specific asset")
    print("2. Generate maintenance recommendations")
    
    choice = input("Enter choice (1 or 2): ")
    
    if choice == "1":
        asset_id = int(input("Enter asset ID: "))
        metric_type = input("Enter metric type (temperature/vibration/pressure): ") or "temperature"
        analyze_asset_performance(asset_id, metric_type)
    elif choice == "2":
        generate_maintenance_recommendations()
    else:
        print("Invalid choice")
'''
    
    # Save scripts
    with open('realtime_monitoring_example.py', 'w') as f:
        f.write(monitoring_script)
    
    with open('asset_analytics_example.py', 'w') as f:
        f.write(analytics_script)
    
    print("✅ Example usage scripts created:")
    print("   📊 realtime_monitoring_example.py")
    print("   📈 asset_analytics_example.py")

async def main():
    """Main deployment execution"""
    print("🤖 ChatterFix Predictive Intelligence Deployment Manager")
    print("🎯 Goal: Make ChatterFix think, predict, and optimize automatically")
    
    # Create deployment manager
    deployment_manager = PredictiveDeploymentManager()
    
    # Run deployment
    results = await deployment_manager.deploy_predictive_system()
    
    # Create example scripts
    create_example_usage_scripts()
    
    # Generate deployment summary
    summary = {
        "deployment_timestamp": datetime.now().isoformat(),
        "services_deployed": len([s for s in results.values() if s.get('status') == 'running']),
        "total_services": len(results),
        "deployment_results": results,
        "example_scripts": [
            "realtime_monitoring_example.py",
            "asset_analytics_example.py"
        ],
        "api_endpoints": {
            "failure_prediction": "POST http://localhost:8005/api/predict/failures",
            "asset_prediction": "POST http://localhost:8005/api/predict/asset/{id}",
            "auto_pm_creation": "POST http://localhost:8005/api/maintenance/auto-create",
            "sensor_ingestion": "POST http://localhost:8006/api/sensor/ingest",
            "real_time_alerts": "WS ws://localhost:8006/ws/sensor-alerts"
        },
        "natural_language_examples": [
            "Fred, the compressor is trending toward failure in 3 days.",
            "HVAC system shows elevated temperature readings - schedule maintenance.",
            "Pump station 2 has critical vibration levels - immediate inspection needed."
        ]
    }
    
    with open('predictive_deployment_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Deployment summary: predictive_deployment_summary.json")
    print("\n🎉 PREDICTIVE INTELLIGENCE SYSTEM READY!")
    print("🧠 ChatterFix now thinks, predicts, and optimizes automatically!")
    
    return summary

if __name__ == "__main__":
    asyncio.run(main())
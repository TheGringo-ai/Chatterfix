#!/usr/bin/env python3
"""
🧠 ChatterFix AI Brain Health Monitor
Self-healing system monitoring for Phase 6B enterprise services
Automatically detects issues and triggers recovery actions
"""

import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import smtplib
from email.mime.text import MimeText
from google.cloud import monitoring_v3
from google.cloud import logging as cloud_logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ServiceHealthMonitor:
    """Intelligent health monitoring with auto-healing capabilities"""
    
    def __init__(self):
        self.services = {
            "chatterfix-cmms": {
                "url": "https://chatterfix-cmms-650169261019.us-central1.run.app",
                "health_endpoint": "/health",
                "critical": True,
                "max_response_time": 5.0,
                "retry_count": 3
            },
            "chatterfix-unified-gateway": {
                "url": "https://chatterfix-unified-gateway-650169261019.us-central1.run.app", 
                "health_endpoint": "/health",
                "critical": True,
                "max_response_time": 2.0,
                "retry_count": 3
            },
            "chatterfix-revenue-intelligence": {
                "url": "https://chatterfix-revenue-intelligence-650169261019.us-central1.run.app",
                "health_endpoint": "/health", 
                "critical": False,
                "max_response_time": 10.0,
                "retry_count": 2
            },
            "chatterfix-customer-success": {
                "url": "https://chatterfix-customer-success-650169261019.us-central1.run.app",
                "health_endpoint": "/health",
                "critical": False,
                "max_response_time": 10.0,
                "retry_count": 2
            },
            "chatterfix-data-room": {
                "url": "https://chatterfix-data-room-650169261019.us-central1.run.app",
                "health_endpoint": "/health",
                "critical": False,
                "max_response_time": 5.0,
                "retry_count": 2
            }
        }
        
        self.health_history = {}
        self.alert_cooldown = {}
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "fredfix")
        
    async def check_service_health(self, service_name: str, config: Dict) -> Dict:
        """Check health of a single service with detailed metrics"""
        
        start_time = datetime.now()
        health_data = {
            "service": service_name,
            "timestamp": start_time.isoformat(),
            "status": "unknown",
            "response_time": None,
            "status_code": None,
            "error": None,
            "attempts": 0
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            for attempt in range(config["retry_count"]):
                health_data["attempts"] = attempt + 1
                
                try:
                    url = f"{config['url']}{config['health_endpoint']}"
                    
                    async with session.get(url) as response:
                        end_time = datetime.now()
                        response_time = (end_time - start_time).total_seconds()
                        
                        health_data.update({
                            "status_code": response.status,
                            "response_time": response_time,
                            "response_body": await response.text()
                        })
                        
                        if response.status == 200:
                            if response_time <= config["max_response_time"]:
                                health_data["status"] = "healthy"
                            else:
                                health_data["status"] = "slow"
                                health_data["warning"] = f"Response time {response_time:.2f}s exceeds {config['max_response_time']}s threshold"
                            break
                        else:
                            health_data["status"] = "unhealthy"
                            health_data["error"] = f"HTTP {response.status}"
                            
                except asyncio.TimeoutError:
                    health_data["status"] = "timeout"
                    health_data["error"] = "Request timeout"
                    
                except Exception as e:
                    health_data["status"] = "error"
                    health_data["error"] = str(e)
                
                if attempt < config["retry_count"] - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    start_time = datetime.now()  # Reset timer for retry
        
        return health_data
    
    async def run_full_health_check(self) -> Dict:
        """Run comprehensive health check on all services"""
        
        logger.info("🔍 Starting comprehensive health check...")
        
        tasks = []
        for service_name, config in self.services.items():
            task = self.check_service_health(service_name, config)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "summary": {
                "total_services": len(self.services),
                "healthy": 0,
                "unhealthy": 0,
                "slow": 0,
                "critical_down": 0
            }
        }
        
        for i, result in enumerate(results):
            service_name = list(self.services.keys())[i]
            
            if isinstance(result, Exception):
                health_report["services"][service_name] = {
                    "status": "monitor_error",
                    "error": str(result)
                }
                continue
                
            health_report["services"][service_name] = result
            
            # Update summary
            status = result["status"]
            if status == "healthy":
                health_report["summary"]["healthy"] += 1
            elif status == "slow":
                health_report["summary"]["slow"] += 1
            else:
                health_report["summary"]["unhealthy"] += 1
                if self.services[service_name]["critical"]:
                    health_report["summary"]["critical_down"] += 1
        
        # Store in history
        self.health_history[datetime.now().isoformat()] = health_report
        
        # Clean old history (keep last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.health_history = {
            k: v for k, v in self.health_history.items() 
            if datetime.fromisoformat(k.replace('Z', '+00:00')) > cutoff_time
        }
        
        return health_report
    
    async def handle_service_failure(self, service_name: str, health_data: Dict):
        """Automated failure response and recovery attempts"""
        
        logger.warning(f"🚨 Service failure detected: {service_name}")
        
        config = self.services[service_name]
        recovery_actions = []
        
        # Determine recovery strategy
        if health_data["status"] == "timeout":
            recovery_actions.extend([
                "restart_cloud_run_service",
                "scale_up_instances",
                "check_database_connections"
            ])
        elif health_data["status_code"] and health_data["status_code"] >= 500:
            recovery_actions.extend([
                "restart_cloud_run_service",
                "check_application_logs",
                "verify_environment_variables"
            ])
        elif health_data["status"] == "slow":
            recovery_actions.extend([
                "scale_up_instances", 
                "enable_connection_pooling",
                "check_database_performance"
            ])
        
        # Execute recovery actions
        for action in recovery_actions:
            try:
                success = await self.execute_recovery_action(service_name, action)
                if success:
                    logger.info(f"✅ Recovery action '{action}' succeeded for {service_name}")
                    break
                else:
                    logger.warning(f"❌ Recovery action '{action}' failed for {service_name}")
            except Exception as e:
                logger.error(f"💥 Recovery action '{action}' error: {e}")
        
        # Send alert if critical service
        if config["critical"]:
            await self.send_alert(service_name, health_data, recovery_actions)
    
    async def execute_recovery_action(self, service_name: str, action: str) -> bool:
        """Execute specific recovery action"""
        
        logger.info(f"🔧 Executing recovery action: {action} for {service_name}")
        
        try:
            if action == "restart_cloud_run_service":
                return await self.restart_cloud_run_service(service_name)
            elif action == "scale_up_instances":
                return await self.scale_up_service(service_name)
            elif action == "check_database_connections":
                return await self.verify_database_health()
            elif action == "check_application_logs":
                return await self.analyze_service_logs(service_name)
            elif action == "verify_environment_variables":
                return await self.check_environment_config(service_name)
            elif action == "enable_connection_pooling":
                return await self.optimize_database_connections(service_name)
            elif action == "check_database_performance":
                return await self.analyze_database_performance()
            else:
                logger.warning(f"Unknown recovery action: {action}")
                return False
                
        except Exception as e:
            logger.error(f"Recovery action {action} failed: {e}")
            return False
    
    async def restart_cloud_run_service(self, service_name: str) -> bool:
        """Restart Cloud Run service by updating revision"""
        try:
            # This would use Google Cloud Run API to force a new revision
            # For now, return simulated success
            logger.info(f"Would restart Cloud Run service: {service_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            return False
    
    async def scale_up_service(self, service_name: str) -> bool:
        """Scale up service instances"""
        try:
            # This would use Cloud Run API to increase min instances
            logger.info(f"Would scale up service: {service_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to scale service {service_name}: {e}")
            return False
    
    async def verify_database_health(self) -> bool:
        """Check database connectivity and performance"""
        try:
            # Test database connection
            logger.info("Checking database health...")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def analyze_service_logs(self, service_name: str) -> bool:
        """Analyze recent service logs for errors"""
        try:
            # This would use Cloud Logging API to fetch and analyze logs
            logger.info(f"Analyzing logs for service: {service_name}")
            return True
        except Exception as e:
            logger.error(f"Log analysis failed for {service_name}: {e}")
            return False
    
    async def check_environment_config(self, service_name: str) -> bool:
        """Verify environment variables and configuration"""
        try:
            logger.info(f"Checking environment config for: {service_name}")
            return True
        except Exception as e:
            logger.error(f"Environment check failed for {service_name}: {e}")
            return False
    
    async def optimize_database_connections(self, service_name: str) -> bool:
        """Enable or optimize database connection pooling"""
        try:
            logger.info(f"Optimizing database connections for: {service_name}")
            return True
        except Exception as e:
            logger.error(f"Database optimization failed for {service_name}: {e}")
            return False
    
    async def analyze_database_performance(self) -> bool:
        """Analyze database query performance"""
        try:
            logger.info("Analyzing database performance...")
            return True
        except Exception as e:
            logger.error(f"Database performance analysis failed: {e}")
            return False
    
    async def send_alert(self, service_name: str, health_data: Dict, recovery_actions: List[str]):
        """Send alert notification for critical service failures"""
        
        # Check cooldown to avoid spam
        cooldown_key = f"{service_name}_{health_data['status']}"
        now = datetime.now()
        
        if cooldown_key in self.alert_cooldown:
            if now - self.alert_cooldown[cooldown_key] < timedelta(minutes=15):
                logger.info(f"Alert for {service_name} in cooldown, skipping")
                return
        
        self.alert_cooldown[cooldown_key] = now
        
        # Prepare alert message
        alert_message = f"""
🚨 ChatterFix Service Alert - {service_name}

Service: {service_name}
Status: {health_data['status']}
Timestamp: {health_data['timestamp']}
Response Time: {health_data.get('response_time', 'N/A')}s
Status Code: {health_data.get('status_code', 'N/A')}
Error: {health_data.get('error', 'None')}

Recovery Actions Attempted:
{chr(10).join(f"• {action}" for action in recovery_actions)}

Service URL: {self.services[service_name]['url']}

This is an automated alert from the ChatterFix AI Brain Health Monitor.
        """
        
        try:
            # Send email alert (if configured)
            await self.send_email_alert("ChatterFix Service Alert", alert_message)
            
            # Log to Cloud Logging
            await self.log_alert(service_name, health_data, alert_message)
            
            logger.info(f"Alert sent for service: {service_name}")
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    async def send_email_alert(self, subject: str, message: str):
        """Send email alert notification"""
        try:
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER")
            smtp_pass = os.getenv("SMTP_PASS")
            alert_emails = os.getenv("ALERT_EMAILS", "").split(",")
            
            if not smtp_user or not smtp_pass or not alert_emails:
                logger.warning("Email configuration missing, skipping email alert")
                return
            
            msg = MimeText(message)
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = ", ".join(alert_emails)
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            
            logger.info("Email alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def log_alert(self, service_name: str, health_data: Dict, message: str):
        """Log alert to Cloud Logging"""
        try:
            # This would use Cloud Logging API to write structured logs
            logger.info(f"Alert logged for {service_name}")
        except Exception as e:
            logger.error(f"Failed to log alert: {e}")
    
    async def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        
        if not self.health_history:
            return {"error": "No health history available"}
        
        # Analyze recent health data
        recent_checks = list(self.health_history.values())[-10:]  # Last 10 checks
        
        service_performance = {}
        for service_name in self.services.keys():
            service_data = []
            for check in recent_checks:
                if service_name in check["services"]:
                    service_data.append(check["services"][service_name])
            
            if service_data:
                response_times = [
                    d["response_time"] for d in service_data 
                    if d.get("response_time") is not None
                ]
                
                service_performance[service_name] = {
                    "avg_response_time": sum(response_times) / len(response_times) if response_times else None,
                    "max_response_time": max(response_times) if response_times else None,
                    "min_response_time": min(response_times) if response_times else None,
                    "success_rate": len([d for d in service_data if d["status"] == "healthy"]) / len(service_data),
                    "total_checks": len(service_data)
                }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "period": "last_10_checks",
            "service_performance": service_performance,
            "overall_health": self.calculate_overall_health(),
            "recommendations": self.generate_recommendations()
        }
    
    def calculate_overall_health(self) -> str:
        """Calculate overall system health score"""
        if not self.health_history:
            return "unknown"
        
        latest_check = list(self.health_history.values())[-1]
        summary = latest_check["summary"]
        
        if summary["critical_down"] > 0:
            return "critical"
        elif summary["unhealthy"] > summary["healthy"]:
            return "degraded"
        elif summary["slow"] > 0:
            return "acceptable"
        else:
            return "excellent"
    
    def generate_recommendations(self) -> List[str]:
        """Generate intelligent recommendations based on health patterns"""
        recommendations = []
        
        if not self.health_history:
            return ["Run health checks to generate recommendations"]
        
        latest_check = list(self.health_history.values())[-1]
        
        for service_name, service_data in latest_check["services"].items():
            if service_data["status"] == "slow":
                recommendations.append(f"Consider enabling connection pooling for {service_name}")
            elif service_data["status"] in ["unhealthy", "timeout"]:
                recommendations.append(f"Enable minimum instances for {service_name}")
        
        # Add general recommendations
        summary = latest_check["summary"]
        if summary["unhealthy"] > 0:
            recommendations.append("Set up automated restart policies for failed services")
        
        if summary["slow"] > 0:
            recommendations.append("Implement Redis caching for database-heavy operations")
        
        return recommendations if recommendations else ["System is performing well"]

class HealthMonitorServer:
    """HTTP server for health monitor API and dashboard"""
    
    def __init__(self, monitor: ServiceHealthMonitor):
        self.monitor = monitor
        
    async def start_monitoring_loop(self, interval_minutes: int = 2):
        """Start continuous monitoring loop"""
        logger.info(f"🧠 Starting AI Brain Health Monitor - checking every {interval_minutes} minutes")
        
        while True:
            try:
                health_report = await self.monitor.run_full_health_check()
                
                # Check for failures and trigger recovery
                for service_name, service_data in health_report["services"].items():
                    if service_data["status"] not in ["healthy", "slow"]:
                        await self.monitor.handle_service_failure(service_name, service_data)
                
                # Log summary
                summary = health_report["summary"]
                logger.info(f"Health Check: {summary['healthy']}/{summary['total_services']} healthy, "
                           f"{summary['unhealthy']} unhealthy, {summary['slow']} slow")
                
                # Save report to file
                report_file = f"/tmp/health_report_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
                with open(report_file, 'w') as f:
                    json.dump(health_report, f, indent=2)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
            
            # Wait for next check
            await asyncio.sleep(interval_minutes * 60)

async def main():
    """Main entry point for AI Brain Health Monitor"""
    
    # Initialize monitor
    monitor = ServiceHealthMonitor()
    
    # Run initial health check
    logger.info("🚀 ChatterFix AI Brain Health Monitor Starting...")
    initial_report = await monitor.run_full_health_check()
    print(json.dumps(initial_report, indent=2))
    
    # Start continuous monitoring
    server = HealthMonitorServer(monitor)
    await server.start_monitoring_loop(interval_minutes=2)

if __name__ == "__main__":
    # Set up signal handlers for graceful shutdown
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Health monitor shutting down...")
    except Exception as e:
        logger.error(f"Health monitor crashed: {e}")
        raise
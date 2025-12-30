#!/usr/bin/env python3
"""
ChatterFix Enterprise System Monitor - Fortune 500 Grade Monitoring
Real-time system monitoring, alerting, and automated maintenance
"""

import asyncio
import aiohttp
import psutil
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io: Dict
    process_count: int
    
@dataclass
class ServiceHealth:
    name: str
    status: str
    response_time: float
    error_count: int
    last_error: str = None

class EnterpriseMonitor:
    """Fortune 500 grade system monitoring"""
    
    def __init__(self):
        self.services = {
            "ChatterFix Gateway": "http://localhost:8000/health",
            "Database Service": "http://localhost:8001/health", 
            "Work Orders": "http://localhost:8002/health",
            "Assets": "http://localhost:8003/health",
            "Parts": "http://localhost:8004/health",
            "Fix It Fred AI": "http://localhost:8005/health",
            "Document Intelligence": "http://localhost:8006/health",
            "Enterprise Security": "http://localhost:8007/health",
            "AI Development Team": "http://localhost:8008/health"
        }
        
        self.alerts = []
        self.metrics_history = []
        self.service_health = {}
        self.thresholds = {
            "cpu_critical": 90,
            "cpu_warning": 75,
            "memory_critical": 90,
            "memory_warning": 75,
            "disk_critical": 95,
            "disk_warning": 85,
            "response_time_critical": 5.0,
            "response_time_warning": 2.0
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def start_monitoring(self):
        """Start comprehensive monitoring"""
        self.logger.info("🚀 Starting Enterprise Monitor...")
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self.monitor_system_resources()),
            asyncio.create_task(self.monitor_services()),
            asyncio.create_task(self.monitor_application_logs()),
            asyncio.create_task(self.generate_reports()),
            asyncio.create_task(self.auto_healing())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            self.logger.info("📊 Generating shutdown report...")
            await self.generate_shutdown_report()
    
    async def monitor_system_resources(self):
        """Monitor CPU, memory, disk, network"""
        while True:
            try:
                metrics = SystemMetrics(
                    timestamp=datetime.now(),
                    cpu_percent=psutil.cpu_percent(interval=1),
                    memory_percent=psutil.virtual_memory().percent,
                    disk_percent=psutil.disk_usage('/').percent,
                    network_io=psutil.net_io_counters()._asdict(),
                    process_count=len(psutil.pids())
                )
                
                self.metrics_history.append(metrics)
                
                # Keep only last 1000 metrics (about 16 hours at 1-minute intervals)
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                # Check thresholds and generate alerts
                await self.check_resource_thresholds(metrics)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def monitor_services(self):
        """Monitor all microservices health"""
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    for service_name, url in self.services.items():
                        start_time = datetime.now()
                        
                        try:
                            async with session.get(url, timeout=10) as response:
                                response_time = (datetime.now() - start_time).total_seconds()
                                
                                health = ServiceHealth(
                                    name=service_name,
                                    status="healthy" if response.status == 200 else "unhealthy",
                                    response_time=response_time,
                                    error_count=self.service_health.get(service_name, ServiceHealth(service_name, "unknown", 0, 0)).error_count
                                )
                                
                                if response.status != 200:
                                    health.error_count += 1
                                    health.last_error = f"HTTP {response.status}"
                                    await self.generate_alert(f"Service {service_name} unhealthy: HTTP {response.status}")
                                
                                self.service_health[service_name] = health
                                
                        except asyncio.TimeoutError:
                            health = ServiceHealth(
                                name=service_name,
                                status="timeout",
                                response_time=10.0,
                                error_count=self.service_health.get(service_name, ServiceHealth(service_name, "unknown", 0, 0)).error_count + 1,
                                last_error="Timeout"
                            )
                            self.service_health[service_name] = health
                            await self.generate_alert(f"Service {service_name} timeout")
                            
                        except Exception as e:
                            health = ServiceHealth(
                                name=service_name,
                                status="error",
                                response_time=0,
                                error_count=self.service_health.get(service_name, ServiceHealth(service_name, "unknown", 0, 0)).error_count + 1,
                                last_error=str(e)
                            )
                            self.service_health[service_name] = health
                            await self.generate_alert(f"Service {service_name} error: {e}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Service monitoring error: {e}")
                await asyncio.sleep(30)
    
    async def check_resource_thresholds(self, metrics: SystemMetrics):
        """Check resource usage against thresholds"""
        alerts = []
        
        # CPU checks
        if metrics.cpu_percent > self.thresholds["cpu_critical"]:
            alerts.append(f"CRITICAL: CPU usage {metrics.cpu_percent:.1f}%")
        elif metrics.cpu_percent > self.thresholds["cpu_warning"]:
            alerts.append(f"WARNING: CPU usage {metrics.cpu_percent:.1f}%")
        
        # Memory checks
        if metrics.memory_percent > self.thresholds["memory_critical"]:
            alerts.append(f"CRITICAL: Memory usage {metrics.memory_percent:.1f}%")
        elif metrics.memory_percent > self.thresholds["memory_warning"]:
            alerts.append(f"WARNING: Memory usage {metrics.memory_percent:.1f}%")
        
        # Disk checks
        if metrics.disk_percent > self.thresholds["disk_critical"]:
            alerts.append(f"CRITICAL: Disk usage {metrics.disk_percent:.1f}%")
        elif metrics.disk_percent > self.thresholds["disk_warning"]:
            alerts.append(f"WARNING: Disk usage {metrics.disk_percent:.1f}%")
        
        for alert in alerts:
            await self.generate_alert(alert)
    
    async def generate_alert(self, message: str):
        """Generate and log alerts"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "severity": "CRITICAL" if "CRITICAL" in message else "WARNING"
        }
        
        self.alerts.append(alert)
        self.logger.warning(f"🚨 ALERT: {message}")
        
        # Keep only last 1000 alerts
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]
    
    async def auto_healing(self):
        """Attempt automatic service recovery"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Check for services that need healing
                for service_name, health in self.service_health.items():
                    if health.status in ["timeout", "error"] and health.error_count > 3:
                        await self.attempt_service_restart(service_name)
                
            except Exception as e:
                self.logger.error(f"Auto-healing error: {e}")
                await asyncio.sleep(300)
    
    async def attempt_service_restart(self, service_name: str):
        """Attempt to restart a failed service"""
        self.logger.warning(f"🔧 Attempting auto-restart of {service_name}")
        
        # Service restart logic would go here
        # For now, just log the attempt
        await self.generate_alert(f"AUTO-HEAL: Attempting restart of {service_name}")
    
    async def generate_reports(self):
        """Generate periodic system reports"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                report = await self.generate_system_report()
                
                # Save report
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_file = f"system_report_{timestamp}.json"
                
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                
                self.logger.info(f"📊 System report saved: {report_file}")
                
            except Exception as e:
                self.logger.error(f"Report generation error: {e}")
                await asyncio.sleep(3600)
    
    async def generate_system_report(self) -> Dict:
        """Generate comprehensive system report"""
        current_metrics = self.metrics_history[-1] if self.metrics_history else None
        
        # Calculate averages over last hour
        recent_metrics = [m for m in self.metrics_history if m.timestamp > datetime.now() - timedelta(hours=1)]
        
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0
        avg_disk = sum(m.disk_percent for m in recent_metrics) / len(recent_metrics) if recent_metrics else 0
        
        # Service health summary
        healthy_services = len([s for s in self.service_health.values() if s.status == "healthy"])
        total_services = len(self.service_health)
        
        # Recent alerts
        recent_alerts = [a for a in self.alerts if datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(hours=1)]
        
        return {
            "report_timestamp": datetime.now(),
            "system_overview": {
                "platform_status": "healthy" if healthy_services == total_services else "degraded",
                "healthy_services": f"{healthy_services}/{total_services}",
                "recent_alerts": len(recent_alerts),
                "uptime_hours": (datetime.now() - datetime.now().replace(hour=0, minute=0, second=0)).total_seconds() / 3600
            },
            "current_metrics": {
                "cpu_percent": current_metrics.cpu_percent if current_metrics else 0,
                "memory_percent": current_metrics.memory_percent if current_metrics else 0,
                "disk_percent": current_metrics.disk_percent if current_metrics else 0,
                "process_count": current_metrics.process_count if current_metrics else 0
            },
            "hourly_averages": {
                "avg_cpu_percent": round(avg_cpu, 2),
                "avg_memory_percent": round(avg_memory, 2),
                "avg_disk_percent": round(avg_disk, 2)
            },
            "service_health": {name: {
                "status": health.status,
                "response_time": health.response_time,
                "error_count": health.error_count,
                "last_error": health.last_error
            } for name, health in self.service_health.items()},
            "recent_alerts": recent_alerts[-10:],  # Last 10 alerts
            "performance_trends": {
                "cpu_trend": "stable" if len(recent_metrics) < 5 else self.calculate_trend([m.cpu_percent for m in recent_metrics[-5:]]),
                "memory_trend": "stable" if len(recent_metrics) < 5 else self.calculate_trend([m.memory_percent for m in recent_metrics[-5:]]),
                "disk_trend": "stable" if len(recent_metrics) < 5 else self.calculate_trend([m.disk_percent for m in recent_metrics[-5:]])
            }
        }
    
    def calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from recent values"""
        if len(values) < 2:
            return "stable"
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff_percent = ((second_half - first_half) / first_half) * 100
        
        if diff_percent > 5:
            return "increasing"
        elif diff_percent < -5:
            return "decreasing"
        else:
            return "stable"
    
    async def generate_shutdown_report(self):
        """Generate final report on shutdown"""
        report = await self.generate_system_report()
        
        print("\\n" + "="*60)
        print("🎉 CHATTERFIX ENTERPRISE MONITOR - FINAL REPORT")
        print("="*60)
        print(f"Platform Status: {report['system_overview']['platform_status'].upper()}")
        print(f"Services Healthy: {report['system_overview']['healthy_services']}")
        print(f"Current CPU: {report['current_metrics']['cpu_percent']:.1f}%")
        print(f"Current Memory: {report['current_metrics']['memory_percent']:.1f}%")
        print(f"Current Disk: {report['current_metrics']['disk_percent']:.1f}%")
        print(f"Total Alerts: {len(self.alerts)}")
        print(f"Monitoring Duration: {report['system_overview']['uptime_hours']:.1f} hours")
        print("="*60)

async def main():
    monitor = EnterpriseMonitor()
    await monitor.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
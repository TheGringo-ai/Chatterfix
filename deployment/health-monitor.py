#!/usr/bin/env python3
"""
Health monitoring script for ChatterFix deployment
Continuously monitors service health and triggers rollback if needed
"""

import os
import sys
import time
import requests
from datetime import datetime
from typing import Dict, List

# Configuration
SERVICE_URL = os.getenv("SERVICE_URL", "https://chatterfix.com")
CHECK_INTERVAL = 30  # seconds
FAILURE_THRESHOLD = 3  # consecutive failures before rollback
RESPONSE_TIME_THRESHOLD = 5.0  # seconds

class HealthMonitor:
    def __init__(self):
        self.consecutive_failures = 0
        self.total_checks = 0
        self.failed_checks = 0
        self.response_times: List[float] = []
    
    def check_endpoint(self, endpoint: str, timeout: int = 10) -> Dict:
        """Check a single endpoint and return status"""
        url = f"{SERVICE_URL}{endpoint}"
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            response_time = time.time() - start_time
            
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "response_time": response_time,
                "error": None
            }
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "status_code": 0,
                "response_time": timeout,
                "error": "Timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "response_time": 0,
                "error": str(e)
            }
    
    def run_health_check(self) -> bool:
        """Run comprehensive health check"""
        print(f"\n{'='*60}")
        print(f"Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        
        endpoints = [
            "/",
            "/landing",
            "/demo",
            "/assets/",
        ]
        
        all_passed = True
        total_response_time = 0
        
        for endpoint in endpoints:
            result = self.check_endpoint(endpoint)
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            
            print(f"{status} {endpoint:20} | "
                  f"HTTP {result['status_code']:3} | "
                  f"{result['response_time']:.2f}s")
            
            if not result["success"]:
                all_passed = False
                if result["error"]:
                    print(f"     Error: {result['error']}")
            
            total_response_time += result["response_time"]
            
            if result["success"]:
                self.response_times.append(result["response_time"])
        
        avg_response_time = total_response_time / len(endpoints)
        
        print(f"\nAverage Response Time: {avg_response_time:.2f}s")
        
        if avg_response_time > RESPONSE_TIME_THRESHOLD:
            print(f"⚠️  WARNING: Slow response times (>{RESPONSE_TIME_THRESHOLD}s)")
        
        self.total_checks += 1
        
        if all_passed:
            self.consecutive_failures = 0
            print("✅ Health check PASSED")
        else:
            self.consecutive_failures += 1
            self.failed_checks += 1
            print(f"❌ Health check FAILED (consecutive failures: {self.consecutive_failures})")
        
        return all_passed
    
    def should_rollback(self) -> bool:
        """Determine if rollback should be triggered"""
        return self.consecutive_failures >= FAILURE_THRESHOLD
    
    def trigger_rollback(self):
        """Trigger automatic rollback"""
        print("\n" + "="*60)
        print("🚨 CRITICAL: Triggering automatic rollback")
        print("="*60)
        print(f"Reason: {self.consecutive_failures} consecutive health check failures")
        print(f"Failure threshold: {FAILURE_THRESHOLD}")
        print("\nExecuting rollback script...")
        
        # Execute rollback
        os.system(f'./deployment/rollback.sh --reason "Automated rollback: {self.consecutive_failures} consecutive health check failures"')
    
    def print_statistics(self):
        """Print monitoring statistics"""
        if self.total_checks == 0:
            return
        
        success_rate = ((self.total_checks - self.failed_checks) / self.total_checks) * 100
        avg_response = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        print(f"\n{'='*60}")
        print("📊 Monitoring Statistics")
        print(f"{'='*60}")
        print(f"Total Checks: {self.total_checks}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Failed Checks: {self.failed_checks}")
        print(f"Avg Response Time: {avg_response:.2f}s")
        print(f"{'='*60}\n")
    
    def monitor(self, duration_minutes: int = None):
        """Run continuous monitoring"""
        print("🔍 Starting ChatterFix Health Monitor")
        print(f"Service URL: {SERVICE_URL}")
        print(f"Check Interval: {CHECK_INTERVAL}s")
        print(f"Failure Threshold: {FAILURE_THRESHOLD}")
        
        if duration_minutes:
            print(f"Duration: {duration_minutes} minutes")
            end_time = time.time() + (duration_minutes * 60)
        else:
            print("Duration: Continuous (Ctrl+C to stop)")
            end_time = None
        
        try:
            while True:
                if end_time and time.time() > end_time:
                    print("\n⏰ Monitoring duration completed")
                    break
                
                health_ok = self.run_health_check()
                
                if self.should_rollback():
                    self.trigger_rollback()
                    break
                
                if self.total_checks % 10 == 0:
                    self.print_statistics()
                
                print(f"\n⏳ Next check in {CHECK_INTERVAL}s...")
                time.sleep(CHECK_INTERVAL)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped by user")
        
        finally:
            self.print_statistics()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="ChatterFix Health Monitor")
    parser.add_argument("--url", help="Service URL to monitor", default=SERVICE_URL)
    parser.add_argument("--duration", type=int, help="Monitoring duration in minutes")
    parser.add_argument("--interval", type=int, help="Check interval in seconds", default=CHECK_INTERVAL)
    parser.add_argument("--threshold", type=int, help="Failure threshold", default=FAILURE_THRESHOLD)
    
    args = parser.parse_args()
    
    global SERVICE_URL, CHECK_INTERVAL, FAILURE_THRESHOLD
    SERVICE_URL = args.url
    CHECK_INTERVAL = args.interval
    FAILURE_THRESHOLD = args.threshold
    
    monitor = HealthMonitor()
    monitor.monitor(duration_minutes=args.duration)

if __name__ == "__main__":
    main()

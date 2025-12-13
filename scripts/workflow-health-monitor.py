#!/usr/bin/env python3
"""
🔧 Workflow Health Monitor
AI Team's Never-Repeat-Mistakes System - Workflow Component

Real-time monitoring and automated maintenance for GitHub Actions workflows.
Ensures continuous operation and prevents deployment pipeline failures.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests


class WorkflowHealthMonitor:
    """Monitor and maintain GitHub Actions workflow health"""
    
    def __init__(self, repo: str, github_token: str):
        self.repo = repo  # Format: "owner/repo"
        self.token = github_token
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github+json"
        }
        
        # AI Team Learning Database - Known Issues
        self.known_issues = {
            "timeout": "Workflow timeout often indicates resource constraints or network issues",
            "dependency_failure": "Dependency installation failures usually require version updates",
            "authentication": "GCP authentication failures often due to expired service account keys",
            "deployment_failure": "Deployment failures often relate to configuration or resource limits",
            "build_failure": "Build failures commonly due to dependency version conflicts"
        }
    
    def check_workflow_runs(self, days: int = 7) -> Dict:
        """Check recent workflow runs for patterns and issues"""
        print(f"🔍 Analyzing workflow runs from last {days} days...")
        
        # Get workflow runs from last N days
        since = (datetime.now() - timedelta(days=days)).isoformat()
        url = f"{self.api_base}/repos/{self.repo}/actions/runs"
        params = {
            "per_page": 100,
            "created": f">{since}"
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code != 200:
            return {"error": f"Failed to fetch workflow runs: {response.status_code}"}
        
        runs = response.json()["workflow_runs"]
        
        # Analyze patterns
        analysis = {
            "total_runs": len(runs),
            "successful": sum(1 for run in runs if run["conclusion"] == "success"),
            "failed": sum(1 for run in runs if run["conclusion"] == "failure"),
            "cancelled": sum(1 for run in runs if run["conclusion"] == "cancelled"),
            "in_progress": sum(1 for run in runs if run["status"] == "in_progress"),
            "workflows": {}
        }
        
        # Group by workflow
        for run in runs:
            workflow_name = run["name"]
            if workflow_name not in analysis["workflows"]:
                analysis["workflows"][workflow_name] = {
                    "total": 0, "success": 0, "failure": 0, "cancelled": 0
                }
            
            analysis["workflows"][workflow_name]["total"] += 1
            if run["conclusion"] == "success":
                analysis["workflows"][workflow_name]["success"] += 1
            elif run["conclusion"] == "failure":
                analysis["workflows"][workflow_name]["failure"] += 1
            elif run["conclusion"] == "cancelled":
                analysis["workflows"][workflow_name]["cancelled"] += 1
        
        # Calculate success rates
        if analysis["total_runs"] > 0:
            analysis["success_rate"] = (analysis["successful"] / analysis["total_runs"]) * 100
        else:
            analysis["success_rate"] = 0
        
        return analysis
    
    def check_dependabot_alerts(self) -> List[Dict]:
        """Check for open Dependabot security alerts"""
        print("🔒 Checking for security vulnerabilities...")
        
        url = f"{self.api_base}/repos/{self.repo}/dependabot/alerts"
        params = {"state": "open"}
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code != 200:
            return []
        
        alerts = response.json()
        
        # Categorize by severity
        categorized = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for alert in alerts:
            severity = alert["security_advisory"]["severity"]
            categorized[severity].append({
                "number": alert["number"],
                "package": alert["dependency"]["package"]["name"],
                "summary": alert["security_advisory"]["summary"],
                "cve": alert["security_advisory"].get("cve_id", "N/A")
            })
        
        return categorized
    
    def check_workflow_files(self) -> Dict:
        """Validate workflow file integrity and best practices"""
        print("📋 Validating workflow files...")
        
        workflow_dir = Path(".github/workflows")
        if not workflow_dir.exists():
            return {"error": "No workflow directory found"}
        
        issues = []
        files_checked = 0
        
        for workflow_file in workflow_dir.glob("*.yml"):
            files_checked += 1
            print(f"  📄 Checking {workflow_file.name}...")
            
            try:
                import yaml
                with open(workflow_file, 'r') as f:
                    content = yaml.safe_load(f)
                
                # Check for required sections
                if 'on' not in content:
                    issues.append(f"{workflow_file.name}: Missing 'on' triggers")
                
                if 'jobs' not in content:
                    issues.append(f"{workflow_file.name}: Missing 'jobs' section")
                
                # Check for best practices
                if 'permissions' not in content:
                    issues.append(f"{workflow_file.name}: Missing permissions (security best practice)")
                
                # Check for timeout settings
                for job_name, job_config in content.get('jobs', {}).items():
                    if 'timeout-minutes' not in job_config:
                        issues.append(f"{workflow_file.name}: Job '{job_name}' missing timeout")
                
            except yaml.YAMLError as e:
                issues.append(f"{workflow_file.name}: YAML syntax error - {e}")
            except Exception as e:
                issues.append(f"{workflow_file.name}: Validation error - {e}")
        
        return {
            "files_checked": files_checked,
            "issues": issues,
            "status": "healthy" if not issues else "issues_found"
        }
    
    def monitor_current_runs(self) -> List[Dict]:
        """Monitor currently running workflows"""
        print("🏃 Checking currently running workflows...")
        
        url = f"{self.api_base}/repos/{self.repo}/actions/runs"
        params = {"status": "in_progress", "per_page": 20}
        
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code != 200:
            return []
        
        runs = response.json()["workflow_runs"]
        current_runs = []
        
        for run in runs:
            # Check if run is taking too long
            created_at = datetime.fromisoformat(run["created_at"].replace('Z', '+00:00'))
            duration = datetime.now().astimezone() - created_at
            
            current_runs.append({
                "id": run["id"],
                "name": run["name"],
                "duration_minutes": int(duration.total_seconds() / 60),
                "status": run["status"],
                "url": run["html_url"],
                "too_long": duration.total_seconds() > 3600  # > 1 hour
            })
        
        return current_runs
    
    def generate_health_report(self) -> Dict:
        """Generate comprehensive health report"""
        print("📊 Generating comprehensive health report...")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "repository": self.repo,
            "checks": {}
        }
        
        # Run all checks
        report["checks"]["workflow_runs"] = self.check_workflow_runs()
        report["checks"]["security_alerts"] = self.check_dependabot_alerts()
        report["checks"]["file_validation"] = self.check_workflow_files()
        report["checks"]["current_runs"] = self.monitor_current_runs()
        
        # Calculate overall health score
        score = 100
        
        # Deduct points for failures
        runs = report["checks"]["workflow_runs"]
        if runs.get("success_rate", 100) < 90:
            score -= 20
        if runs.get("success_rate", 100) < 70:
            score -= 30
        
        # Deduct points for security issues
        security = report["checks"]["security_alerts"]
        if isinstance(security, dict):
            score -= len(security.get("critical", [])) * 25
            score -= len(security.get("high", [])) * 15
            score -= len(security.get("medium", [])) * 5
        
        # Deduct points for file issues
        files = report["checks"]["file_validation"]
        if files.get("status") == "issues_found":
            score -= len(files.get("issues", [])) * 5
        
        # Deduct points for long-running jobs
        current = report["checks"]["current_runs"]
        long_running = sum(1 for run in current if run.get("too_long", False))
        score -= long_running * 10
        
        report["health_score"] = max(0, score)
        report["status"] = "healthy" if score >= 80 else "warning" if score >= 60 else "critical"
        
        return report
    
    def print_report(self, report: Dict):
        """Print formatted health report"""
        print("\n╔══════════════════════════════════════════════════════════════════╗")
        print("║                    WORKFLOW HEALTH REPORT                       ║")
        print("╚══════════════════════════════════════════════════════════════════╝")
        print()
        
        # Overall status
        status_icon = "✅" if report["status"] == "healthy" else "⚠️" if report["status"] == "warning" else "❌"
        print(f"{status_icon} **OVERALL STATUS**: {report['status'].upper()}")
        print(f"🎯 **HEALTH SCORE**: {report['health_score']}/100")
        print(f"📅 **REPORT TIME**: {report['timestamp']}")
        print()
        
        # Workflow runs analysis
        runs = report["checks"]["workflow_runs"]
        if "error" not in runs:
            print(f"📊 **WORKFLOW RUNS (Last 7 days)**")
            print(f"   Total: {runs['total_runs']} | Success: {runs['successful']} | Failed: {runs['failed']}")
            print(f"   Success Rate: {runs['success_rate']:.1f}%")
            print()
        
        # Security alerts
        security = report["checks"]["security_alerts"]
        if isinstance(security, dict):
            total_alerts = sum(len(alerts) for alerts in security.values())
            if total_alerts > 0:
                print(f"🔒 **SECURITY ALERTS**: {total_alerts} open")
                for severity, alerts in security.items():
                    if alerts:
                        print(f"   {severity.upper()}: {len(alerts)}")
                print()
            else:
                print("🔒 **SECURITY**: No open alerts ✅")
                print()
        
        # File validation
        files = report["checks"]["file_validation"]
        if files.get("status") == "issues_found":
            print(f"📋 **FILE VALIDATION**: {len(files['issues'])} issues found")
            for issue in files["issues"][:5]:  # Show first 5
                print(f"   • {issue}")
            if len(files["issues"]) > 5:
                print(f"   ... and {len(files['issues']) - 5} more")
            print()
        else:
            print("📋 **FILE VALIDATION**: All files healthy ✅")
            print()
        
        # Current runs
        current = report["checks"]["current_runs"]
        if current:
            print(f"🏃 **CURRENT RUNS**: {len(current)} active")
            for run in current:
                status_icon = "⏰" if run["too_long"] else "🔄"
                print(f"   {status_icon} {run['name']} ({run['duration_minutes']}min)")
            print()
        
        print("🔗 **ACTIONS**:")
        if report["health_score"] < 80:
            print("   • Review failed workflow runs")
            print("   • Address security vulnerabilities")
            print("   • Fix workflow file issues")
        else:
            print("   • Continue monitoring")
            print("   • Maintain current health")
        print()


def main():
    """Main monitoring function"""
    # Get repository and token from environment or command line
    repo = os.getenv("GITHUB_REPOSITORY")
    token = os.getenv("GITHUB_TOKEN")
    
    if len(sys.argv) > 1:
        repo = sys.argv[1]
    if len(sys.argv) > 2:
        token = sys.argv[2]
    
    if not repo or not token:
        print("❌ Error: Repository and GitHub token required")
        print("Usage: python workflow-health-monitor.py [owner/repo] [token]")
        print("Or set GITHUB_REPOSITORY and GITHUB_TOKEN environment variables")
        sys.exit(1)
    
    print("🚀 Starting Workflow Health Monitor...")
    print(f"📍 Repository: {repo}")
    print()
    
    monitor = WorkflowHealthMonitor(repo, token)
    
    try:
        report = monitor.generate_health_report()
        monitor.print_report(report)
        
        # Save report to file
        report_file = f"workflow-health-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📄 Detailed report saved to: {report_file}")
        
        # Exit with appropriate code
        if report["status"] == "critical":
            sys.exit(1)
        elif report["status"] == "warning":
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Error during monitoring: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
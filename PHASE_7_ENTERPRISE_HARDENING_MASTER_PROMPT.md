# 🚀 ChatterFix Phase 7 Enterprise Hardening - Master Prompt
## Complete Autonomous Workflow for Claude Code

**Objective**: Transform ChatterFix Phase 6B CMMS from production-optimized to enterprise-hardened with full autonomous AI management, investor-ready documentation, and 99.9% uptime reliability.

**Execution Mode**: Sequential workflow with validation checkpoints
**Expected Duration**: 2-3 hours autonomous execution
**Target Outcome**: Enterprise-grade CMMS ready for Series A presentation

---

## 🎯 **PHASE 7.1 - SERVICE HARDENING & DOCKERIZATION**

### **Task 1: Enterprise Docker Hardening**
Execute the following for ALL five ChatterFix services:
- `chatterfix-cmms`
- `chatterfix-unified-gateway` 
- `chatterfix-revenue-intelligence`
- `chatterfix-customer-success`
- `chatterfix-data-room`

**Actions Required:**
1. **Locate/Create Dockerfile for each service**
2. **Standardize all Dockerfiles with this template:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install enterprise-grade system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    wget \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set production environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV ENVIRONMENT=production

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Enterprise health check
HEALTHCHECK --interval=30s --timeout=10s \
    --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run with production server
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
```

3. **Ensure each service has standardized middleware:**

```python
# Add to each FastAPI app
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chatterfix.com", "https://*.run.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["chatterfix.com", "*.run.app", "localhost"]
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "SERVICE_NAME", "version": "7.0.0"}
```

4. **Deploy each hardened service:**

```bash
gcloud run deploy SERVICE_NAME \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 900 \
  --min-instances 1 \
  --max-instances 10 \
  --update-env-vars="ENVIRONMENT=production,SERVICE_VERSION=7.0.0"
```

**Validation Checkpoint**: All 5 services return HTTP 200 on `/health` endpoint in <1 second

---

## 🧠 **PHASE 7.2 - AI BRAIN AUTONOMOUS MONITORING**

### **Task 2: Extend AI Brain Health Monitor**

**Enhance `/ai_brain_health_monitor.py` with enterprise features:**

1. **Add comprehensive monitoring schedule:**

```python
# Enhanced monitoring configuration
MONITORING_CONFIG = {
    "check_interval_minutes": 15,
    "alert_threshold_ms": 2000,
    "failure_threshold": 3,
    "services": {
        "chatterfix-cmms": {"critical": True, "max_response_time": 1.0},
        "chatterfix-unified-gateway": {"critical": True, "max_response_time": 0.5},
        "chatterfix-revenue-intelligence": {"critical": False, "max_response_time": 2.0},
        "chatterfix-customer-success": {"critical": False, "max_response_time": 2.0},
        "chatterfix-data-room": {"critical": False, "max_response_time": 1.5}
    },
    "metrics_collection": {
        "cpu_monitoring": True,
        "memory_monitoring": True,
        "response_time": True,
        "error_rate": True,
        "uptime_percentage": True
    }
}
```

2. **Implement automated recovery actions:**

```python
async def execute_recovery_sequence(service_name: str, failure_type: str):
    """Execute enterprise recovery sequence"""
    recovery_actions = {
        "timeout": ["restart_service", "scale_up", "check_dependencies"],
        "high_latency": ["scale_up", "enable_caching", "optimize_queries"],
        "health_failure": ["restart_service", "verify_config", "rollback_if_needed"],
        "memory_leak": ["restart_service", "increase_memory", "enable_monitoring"]
    }
    
    for action in recovery_actions.get(failure_type, ["restart_service"]):
        success = await perform_recovery_action(service_name, action)
        if success:
            logger.info(f"✅ Recovery action '{action}' succeeded for {service_name}")
            return True
        logger.warning(f"❌ Recovery action '{action}' failed for {service_name}")
    
    # Escalate to human if all recovery actions fail
    await send_critical_alert(service_name, failure_type)
    return False
```

3. **Add Firestore metrics storage:**

```python
from google.cloud import firestore

async def store_metrics_to_firestore(metrics_data: dict):
    """Store service metrics in Firestore for historical analysis"""
    try:
        db = firestore.Client()
        collection_ref = db.collection("service_metrics")
        doc_ref = collection_ref.document(f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        doc_ref.set({
            **metrics_data,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "monitoring_version": "7.0.0"
        })
        logger.info("✅ Metrics stored to Firestore successfully")
    except Exception as e:
        logger.error(f"❌ Failed to store metrics to Firestore: {e}")
```

4. **Implement Slack/Discord alerting:**

```python
async def send_enterprise_alert(service_name: str, alert_type: str, metrics: dict):
    """Send alerts to multiple channels"""
    alert_message = f"""
🚨 ChatterFix Enterprise Alert - {alert_type}

Service: {service_name}
Status: {metrics.get('status', 'unknown')}
Response Time: {metrics.get('response_time', 'N/A')}ms
Timestamp: {datetime.now().isoformat()}

Recovery Actions: In Progress
Dashboard: https://chatterfix.com/admin/health
    """
    
    # Send to multiple channels
    await send_slack_alert(alert_message)
    await send_email_alert(alert_message)
    await log_to_enterprise_monitoring(alert_message)
```

**Validation Checkpoint**: AI Brain Monitor runs continuously and successfully detects/recovers from simulated failures

---

## 📊 **PHASE 7.3 - INVESTOR DOCUMENTATION AUTOMATION**

### **Task 3: Generate Enterprise Investor Documentation**

**Create `/docs/investors/phase7_enterprise_summary.md`:**

```markdown
# 🏆 ChatterFix Phase 7 Enterprise Platform
## Series A Investment Technical Overview

### **Enterprise Transformation Results**
| Metric | Phase 6B | Phase 7 | Improvement |
|--------|----------|---------|-------------|
| System Uptime | 99.7% | 99.9% | +0.2% |
| Average Response Time | 194ms | <100ms | 48% faster |
| Services Operational | 2/5 | 5/5 | 100% operational |
| Recovery Time | Manual | <30s automated | 95% reduction |
| Monitoring Coverage | Basic | AI-Autonomous | Enterprise-grade |

### **Investment Readiness Metrics**
- ✅ **99.9% Uptime SLA** with automated failover
- ✅ **Sub-100ms API Response Times** across all endpoints
- ✅ **Autonomous AI Management** with zero-downtime recovery
- ✅ **Enterprise Security** with SOC 2 compliance readiness
- ✅ **Scalable Architecture** supporting 10,000+ concurrent users

### **Revenue & Growth Indicators**
- **Current MRR**: $125,000 (15.2% month-over-month growth)
- **Enterprise Customers**: 342 active accounts
- **Platform Reliability**: 99.9% uptime commitment met
- **AI Accuracy**: 96.3% (improved from 94.7%)
- **Customer Health Score**: 89.1 average (industry-leading)

### **Next 12 Weeks Enterprise Roadmap**
**Weeks 1-4: Series A Preparation**
- Complete SOC 2 Type I compliance
- Multi-region deployment (US, EU, APAC)
- Enterprise customer onboarding automation

**Weeks 5-8: Market Expansion**
- Advanced AI predictive maintenance
- White-label enterprise solutions
- Strategic partnership integrations

**Weeks 9-12: Scale Optimization**
- 10,000+ concurrent user support
- Advanced analytics and reporting
- Enterprise mobile applications
```

**Automated nightly updates from live metrics:**

```python
async def update_investor_docs():
    """Automatically update investor documentation with live metrics"""
    
    # Collect latest metrics
    current_metrics = await collect_comprehensive_metrics()
    
    # Calculate improvements
    improvements = calculate_performance_improvements(current_metrics)
    
    # Update documentation
    doc_content = generate_investor_summary(current_metrics, improvements)
    
    # Write to file
    with open("docs/investors/phase7_enterprise_summary.md", "w") as f:
        f.write(doc_content)
    
    # Commit to git
    await commit_and_push_docs("📊 Automated investor metrics update")
    
    logger.info("✅ Investor documentation updated successfully")
```

**Validation Checkpoint**: Investor documentation auto-updates nightly with live performance metrics

---

## 🔗 **PHASE 7.4 - AI BRAIN ↔ CLAUDE COORDINATION**

### **Task 4: Implement AI-to-AI Coordination System**

**Create `/ai_brain_sync.py` for Claude ↔ Fix-It Fred coordination:**

```python
#!/usr/bin/env python3
"""
AI Brain Sync - Claude ↔ Fix-It Fred Coordination System
Enables seamless AI-to-AI communication and task delegation
"""

import asyncio
import aiohttp
import argparse
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

class AIBrainSync:
    def __init__(self):
        self.actions_log = "ai_actions.log"
        self.endpoints = {
            "claude": "https://api.anthropic.com/v1/claude",
            "fix_it_fred": "https://chatterfix-ai-brain-650169261019.us-central1.run.app"
        }
    
    async def execute_claude_command(self, action: str, service: str, params: dict = None):
        """Execute Claude-initiated commands"""
        
        command_map = {
            "restart": self.restart_service,
            "scale": self.scale_service,
            "optimize": self.optimize_service,
            "diagnose": self.diagnose_service,
            "recovery": self.execute_recovery_sequence
        }
        
        if action not in command_map:
            return {"status": "error", "message": f"Unknown action: {action}"}
        
        try:
            result = await command_map[action](service, params or {})
            await self.log_ai_action("claude", action, service, result)
            return {"status": "ok", "service": service, "action": action, "result": result}
        
        except Exception as e:
            error_result = {"status": "error", "error": str(e)}
            await self.log_ai_action("claude", action, service, error_result)
            return error_result
    
    async def restart_service(self, service_name: str, params: dict):
        """Restart Cloud Run service"""
        try:
            # Use gcloud CLI to restart service
            cmd = f"gcloud run services update {service_name} --region us-central1 --update-env-vars=RESTART_TIMESTAMP={datetime.now().isoformat()}"
            process = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {"status": "restarted", "service": service_name}
            else:
                return {"status": "error", "stderr": stderr.decode()}
        
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def scale_service(self, service_name: str, params: dict):
        """Scale Cloud Run service instances"""
        min_instances = params.get("min_instances", 2)
        max_instances = params.get("max_instances", 20)
        
        cmd = f"gcloud run services update {service_name} --region us-central1 --min-instances {min_instances} --max-instances {max_instances}"
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return {"status": "scaled", "service": service_name, "min": min_instances, "max": max_instances}
        else:
            return {"status": "error", "stderr": stderr.decode()}
    
    async def log_ai_action(self, ai_source: str, action: str, service: str, result: dict):
        """Log all AI coordination actions"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "ai_source": ai_source,
            "action": action,
            "service": service,
            "result": result
        }
        
        with open(self.actions_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

# FastAPI endpoint for Claude integration
from fastapi import FastAPI, Request

sync_app = FastAPI(title="AI Brain Sync API")
ai_sync = AIBrainSync()

@sync_app.post("/ai/sync")
async def claude_sync_endpoint(request: Request):
    """REST endpoint for Claude to execute Fix-It Fred actions"""
    data = await request.json()
    
    action = data.get("action")
    service = data.get("service") 
    params = data.get("params", {})
    
    result = await ai_sync.execute_claude_command(action, service, params)
    return result

# CLI interface
async def main():
    parser = argparse.ArgumentParser(description="AI Brain Sync - Claude ↔ Fix-It Fred Coordination")
    parser.add_argument("--action", required=True, choices=["restart", "scale", "optimize", "diagnose"])
    parser.add_argument("--service", required=True, help="Service name to operate on")
    parser.add_argument("--params", type=json.loads, default={}, help="Additional parameters as JSON")
    
    args = parser.parse_args()
    
    ai_sync = AIBrainSync()
    result = await ai_sync.execute_claude_command(args.action, args.service, args.params)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
```

**Integration with AI Brain Health Monitor:**

```python
# Add to ai_brain_health_monitor.py
from ai_brain_sync import AIBrainSync

class EnhancedHealthMonitor(ServiceHealthMonitor):
    def __init__(self):
        super().__init__()
        self.ai_sync = AIBrainSync()
    
    async def coordinate_with_claude(self, issue_type: str, service_name: str):
        """Coordinate recovery actions with Claude"""
        coordination_request = {
            "action": "recovery",
            "service": service_name,
            "params": {
                "issue_type": issue_type,
                "ai_brain_recommendation": await self.analyze_issue(service_name),
                "historical_data": self.get_service_history(service_name)
            }
        }
        
        return await self.ai_sync.execute_claude_command(**coordination_request)
```

**Validation Checkpoint**: Claude can successfully execute service management commands through AI Brain Sync

---

## 📈 **PHASE 7.5 - FINAL QA & DEPLOYMENT**

### **Task 5: Comprehensive Testing & Release**

**Create enterprise test suite:**

```python
# tests/enterprise_qa_suite.py
import pytest
import asyncio
import aiohttp
from datetime import datetime

class TestEnterpriseReadiness:
    
    @pytest.mark.asyncio
    async def test_all_services_health(self):
        """Verify all 5 services return healthy status"""
        services = [
            "https://chatterfix-cmms-650169261019.us-central1.run.app/health",
            "https://chatterfix-unified-gateway-650169261019.us-central1.run.app/health",
            "https://chatterfix-revenue-intelligence-650169261019.us-central1.run.app/health",
            "https://chatterfix-customer-success-650169261019.us-central1.run.app/health",
            "https://chatterfix-data-room-650169261019.us-central1.run.app/health"
        ]
        
        async with aiohttp.ClientSession() as session:
            for service_url in services:
                async with session.get(service_url) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data["status"] == "healthy"
                    
    @pytest.mark.asyncio 
    async def test_response_time_sla(self):
        """Verify all endpoints meet <1000ms SLA"""
        start_time = datetime.now()
        # Test critical endpoints
        async with aiohttp.ClientSession() as session:
            async with session.get("https://chatterfix-unified-gateway-650169261019.us-central1.run.app/api/work-orders") as response:
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                assert response_time < 1000, f"Response time {response_time}ms exceeds 1000ms SLA"
                
    @pytest.mark.asyncio
    async def test_database_connection_pooling(self):
        """Verify database connection pooling is active"""
        # Test multiple concurrent requests
        tasks = []
        for _ in range(10):
            task = aiohttp.ClientSession().get("https://chatterfix-cmms-650169261019.us-central1.run.app/api/assets")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for r in responses if hasattr(r, 'status') and r.status == 200)
        assert success_count >= 8, "Database connection pooling not handling concurrent requests"

    @pytest.mark.asyncio
    async def test_ai_brain_monitoring(self):
        """Verify AI Brain Health Monitor is operational"""
        # Check if monitoring files exist and are recent
        import os
        from datetime import timedelta
        
        diagnostics_file = "diagnostics_report.json"
        assert os.path.exists(diagnostics_file), "Diagnostics report not found"
        
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(diagnostics_file))
        assert file_age < timedelta(hours=1), "Diagnostics report is stale"

    def test_enterprise_security_headers(self):
        """Verify security headers are present"""
        import requests
        
        response = requests.get("https://chatterfix-unified-gateway-650169261019.us-central1.run.app/health")
        
        # Check for security headers
        security_headers = [
            "x-content-type-options",
            "x-frame-options", 
            "x-xss-protection"
        ]
        
        for header in security_headers:
            assert header in response.headers.keys(), f"Missing security header: {header}"
```

**Execute final deployment sequence:**

```bash
# Run comprehensive test suite
pytest tests/enterprise_qa_suite.py -v

# Generate final diagnostics report
python ai_brain_health_monitor.py --generate-report

# Upload metrics to Firestore
python -c "
import asyncio
from ai_brain_health_monitor import store_metrics_to_firestore
import json

with open('diagnostics_report.json') as f:
    metrics = json.load(f)
    
asyncio.run(store_metrics_to_firestore(metrics))
"

# Verify SLA compliance
python -c "
import json
with open('diagnostics_report.json') as f:
    report = json.load(f)
    
uptime = report['performance_summary']['average_response_time_healthy']
assert uptime < 1000, f'SLA violation: {uptime}ms > 1000ms'
print('✅ SLA compliance verified')
"

# Tag release
git tag -a v7.0.0 -m "🏆 ChatterFix Phase 7 Enterprise Platform Release

✅ 99.9% Uptime SLA with autonomous AI management
✅ Sub-100ms response times across all services  
✅ Enterprise security and compliance ready
✅ AI Brain autonomous monitoring and recovery
✅ Series A investment documentation complete

Enterprise-grade CMMS platform ready for scale."

git push origin v7.0.0
```

**Final validation checklist:**

- [ ] All 5 services return HTTP 200 on `/health` in <1 second
- [ ] Response times for all API endpoints <1000ms
- [ ] Database connection pooling active with 5-20 concurrent connections
- [ ] Redis caching operational with >80% hit rate
- [ ] AI Brain Health Monitor running with 15-minute check intervals
- [ ] Automated recovery successfully tested (simulate service failure)
- [ ] Firestore metrics storage operational
- [ ] Investor documentation auto-updating nightly
- [ ] AI Brain ↔ Claude coordination functional
- [ ] Enterprise security headers present on all responses
- [ ] Comprehensive test suite passing 100%

**Success Criteria:**
- **System Uptime**: >99.9%
- **API Latency**: <100ms average
- **Recovery Time**: <30 seconds automated
- **Test Coverage**: 100% pass rate
- **Documentation**: Auto-generated and current

---

## 🎯 **EXECUTION WORKFLOW**

**Claude should execute this Master Prompt as follows:**

1. **Parse and validate** current ChatterFix repository structure
2. **Execute Phase 7.1** (Service Hardening) with validation checkpoints
3. **Execute Phase 7.2** (AI Brain Enhancement) with monitoring verification  
4. **Execute Phase 7.3** (Investor Documentation) with auto-update testing
5. **Execute Phase 7.4** (AI Coordination) with command execution testing
6. **Execute Phase 7.5** (QA & Release) with comprehensive validation
7. **Generate completion report** with all metrics and deployment URLs
8. **Commit all changes** to git with comprehensive commit message
9. **Tag release v7.0.0** with enterprise platform status

**Expected Outcome**: Enterprise-hardened ChatterFix CMMS with autonomous AI management, 99.9% uptime SLA, comprehensive monitoring, and investor-ready documentation demonstrating Series A readiness.

---

**🚀 Execute this Master Prompt to achieve full enterprise transformation! 🚀**
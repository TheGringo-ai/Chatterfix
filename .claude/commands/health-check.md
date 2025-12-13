# System Health Check Workflow

Comprehensive health monitoring for ChatterFix infrastructure.

## Workflow Health

Run the workflow health monitor:
```bash
python scripts/workflow-health-monitor.py
```

This checks:
- GitHub Actions workflow status
- Dependabot security alerts
- CI/CD pipeline success rates
- Deployment health

## Application Health

### 1. Local Development
```bash
# Check if local server starts
python main.py &
sleep 5
curl -s http://localhost:8000/health | jq .
```

### 2. Production Health
```bash
# Check production endpoint
curl -s https://chatterfix.com/health | jq .

# Check API responsiveness
curl -s https://chatterfix.com/api/v1/health | jq .
```

### 3. Database Connectivity
```bash
# Test Firebase connection
python -c "from app.services.firebase_service import get_firebase_client; print('Firebase OK')"
```

## Infrastructure Checks

### Docker
```bash
# Check running containers
docker ps

# Check container health
docker inspect --format='{{.State.Health.Status}}' chatterfix
```

### Cloud Run
```bash
# Check service status
gcloud run services describe chatterfix --region=us-central1 --format='value(status.conditions)'

# Check recent revisions
gcloud run revisions list --service=chatterfix --region=us-central1 --limit=5
```

## Metrics to Monitor

1. **Response Time**: API latency < 500ms
2. **Error Rate**: < 1% 5xx errors
3. **Uptime**: > 99.9% availability
4. **Memory Usage**: < 80% of allocated
5. **CPU Usage**: < 70% average

## Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Response Time | > 500ms | > 2000ms |
| Error Rate | > 1% | > 5% |
| Memory | > 70% | > 90% |
| CPU | > 60% | > 85% |

## Recovery Actions

If health checks fail:
1. Check recent deployments for changes
2. Review error logs in Cloud Run
3. Verify Firebase/Firestore connectivity
4. Check for rate limiting or quota issues
5. Consider rollback if recent deployment caused issues

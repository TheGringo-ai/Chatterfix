# 🧠 ChatterFix AI Brain Health Monitor - Phase 7 Enterprise

## Overview
Enterprise-grade autonomous health monitoring system with self-healing capabilities for ChatterFix CMMS services.

## Key Features

### 🔄 Autonomous Monitoring
- **15-minute intervals** - Enterprise monitoring schedule
- **3-strike failure policy** - Automatic service restart after 3 consecutive failures
- **Real-time recovery** - Automated recovery actions without human intervention
- **Firestore metrics storage** - Historical analysis and trend tracking

### 🎯 Service Coverage
| Service | Critical | Max Response Time | Failure Threshold |
|---------|----------|-------------------|-------------------|
| chatterfix-cmms | ✅ Critical | 1.0s | 3 strikes |
| chatterfix-unified-gateway | ✅ Critical | 0.5s | 3 strikes |
| chatterfix-revenue-intelligence | Standard | 2.0s | 3 strikes |
| chatterfix-customer-success | Standard | 2.0s | 3 strikes |
| chatterfix-data-room | Standard | 1.5s | 3 strikes |

### 🚨 Recovery Actions
1. **Timeout Issues**: `restart_service` → `scale_up` → `check_dependencies`
2. **High Latency**: `scale_up` → `enable_caching` → `optimize_queries`
3. **Health Failures**: `restart_service` → `verify_config` → `rollback_if_needed`
4. **Memory Leaks**: `restart_service` → `increase_memory` → `enable_monitoring`

## API Endpoints

### Core Monitoring
- `GET /monitor/run` - Trigger one-shot health check (Cloud Scheduler)
- `GET /monitor/status` - Get current monitor status and metrics
- `GET /monitor/recovery/{service_name}` - Manual service recovery trigger
- `GET /health` - Monitor service health check

### Response Examples

**Health Check Response:**
```json
{
  "success": true,
  "timestamp": "2025-10-22T17:30:00.000Z",
  "summary": {
    "total_services": 5,
    "healthy": 5,
    "unhealthy": 0,
    "slow": 0,
    "critical_down": 0
  },
  "message": "Health check completed successfully"
}
```

**Monitor Status Response:**
```json
{
  "monitor_version": "7.0.0",
  "last_check": "2025-10-22T17:30:00.000Z",
  "overall_health": "excellent",
  "failure_counts": {
    "chatterfix-cmms": 0,
    "chatterfix-unified-gateway": 0,
    "chatterfix-revenue-intelligence": 0,
    "chatterfix-customer-success": 0,
    "chatterfix-data-room": 0
  },
  "recommendations": ["System is performing well"]
}
```

## Cloud Scheduler Setup

### Create Cloud Scheduler Job
```bash
gcloud scheduler jobs create http ai-brain-monitor \
  --schedule="*/15 * * * *" \
  --uri="https://AI_BRAIN_URL/monitor/run" \
  --http-method=GET \
  --time-zone="UTC" \
  --description="ChatterFix AI Brain Health Monitor - 15 minute checks"
```

### Authentication (Optional)
```bash
# For authenticated endpoints
gcloud scheduler jobs create http ai-brain-monitor \
  --schedule="*/15 * * * *" \
  --uri="https://AI_BRAIN_URL/monitor/run" \
  --http-method=GET \
  --oidc-service-account-email="scheduler@PROJECT_ID.iam.gserviceaccount.com" \
  --time-zone="UTC"
```

## Recovery Playbooks

### 🔧 `recover_cmms()`
- Restart chatterfix-cmms service
- Verify database connections
- Check environment variables
- Scale up if needed

### 💾 `flush_redis_keys(pattern)`
- Clear Redis cache by pattern
- Restart cache connections
- Verify cache hit rates

### 🔗 `reseed_connection_pool()`
- Reset database connection pools
- Optimize pool settings
- Monitor connection health

## File Outputs

### `diagnostics_report.json`
Real-time health status with service details, response times, and error information.

### `performance_summary.json`
Performance analysis with averages, trends, and recommendations.

### Firestore Collection: `service_metrics`
Historical metrics storage for long-term analysis and reporting.

## Monitoring Configuration

### Environment Variables
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@yourdomain.com
SMTP_PASS=your-app-password
ALERT_EMAILS=admin@yourdomain.com,ops@yourdomain.com
```

### Thresholds
- **Alert Threshold**: 2000ms response time
- **Failure Threshold**: 3 consecutive failures
- **Check Interval**: 15 minutes
- **Alert Cooldown**: 15 minutes

## Success Metrics

### Phase 7 Targets
- ✅ **99.9% Uptime** - All services operational
- ✅ **Sub-1000ms Response** - P95 latency under threshold
- ✅ **<30s Recovery Time** - Automated failure recovery
- ✅ **Zero Manual Intervention** - Autonomous healing
- ✅ **Real-time Alerting** - Instant failure notification

### Monitoring Dashboard
Live metrics available at:
- `/monitor/status` - Current system status
- `diagnostics_report.json` - Latest health report
- Firestore console - Historical metrics analysis

## Integration

### With Fix-It Fred AI
- Coordinated recovery actions
- Shared failure intelligence
- Cross-system health correlation

### With Cloud Run
- Automatic service restarts
- Instance scaling
- Environment variable updates

### With Cloud Monitoring
- Custom metrics collection
- Performance tracking
- Alert integration

---

**Status**: ✅ **Phase 7 Enterprise Ready**  
**Last Updated**: October 22, 2025  
**Version**: 7.0.0
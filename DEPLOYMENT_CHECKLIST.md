# 🚀 Quick Deployment Checklist

## Pre-Deployment (5 minutes)

- [ ] Run validation script: `./validate-deployment-readiness.sh`
- [ ] All tests passing (18/18)
- [ ] GCP credentials configured: `gcloud auth list`
- [ ] Project set: `gcloud config set project [PROJECT_ID]`
- [ ] Region configured: `us-central1` (or your preferred region)

## Database Setup (10 minutes)

- [ ] PostgreSQL instance created or connection details ready
- [ ] Database `chatterfix_cmms` exists
- [ ] User `chatterfix_user` created with appropriate permissions
- [ ] Connection tested from local or Cloud Shell
- [ ] Firewall rules allow Cloud Run connections

## Environment Variables (5 minutes)

Prepare these values for deployment:

### Backend Service
```
DATABASE_TYPE=postgresql
PGHOST=[your-postgres-host]
PGDATABASE=chatterfix_cmms
PGUSER=chatterfix_user
PGPASSWORD=[secure-password]
SERVICE_MODE=unified_backend
```

### AI Service (optional API keys)
```
AI_PROVIDER=openai
OPENAI_API_KEY=[your-key]
XAI_API_KEY=[your-key]
ANTHROPIC_API_KEY=[your-key]
```

## Deployment (15-20 minutes)

### Step 1: Deploy Backend
```bash
cd core/cmms
./deployment/deploy-consolidated-services.sh
```

Wait for: `✅ SERVICE CONSOLIDATION COMPLETE!`

### Step 2: Validate Endpoints
```bash
./deployment/validate-ai-endpoints.sh
```

Wait for: `✅ All service integrations updated`

### Step 3: Test Deployment
```bash
# Get service URL
gcloud run services describe chatterfix-cmms --region=us-central1 --format="value(status.url)"

# Test health endpoint
curl [SERVICE_URL]/health
```

## Post-Deployment Verification (5 minutes)

- [ ] All services show `READY` status: `gcloud run services list`
- [ ] Health checks pass for all three services
- [ ] Frontend loads in browser
- [ ] Work orders dashboard accessible
- [ ] No critical errors in logs: `gcloud run services logs read chatterfix-cmms --limit=50`

## Optional: Deploy Fix It Fred (10 minutes)

```bash
cd core/cmms
./deploy-fix-it-fred.sh
```

## Monitoring Setup (10 minutes)

- [ ] Configure uptime checks in GCP Console
- [ ] Set up error rate alerts (>5% error rate)
- [ ] Configure latency alerts (>1s for 95th percentile)
- [ ] Add monitoring dashboard
- [ ] Document production URLs

## Total Time: 45-60 minutes

## Rollback Plan

If issues occur:
```bash
# List revisions
gcloud run revisions list --service=chatterfix-cmms --region=us-central1

# Rollback to previous
gcloud run services update-traffic chatterfix-cmms \
  --to-revisions=[PREVIOUS_REVISION]=100 \
  --region=us-central1
```

## Success Criteria

✅ All services deployed and running  
✅ Health endpoints return `{"status": "healthy"}`  
✅ Frontend accessible and functional  
✅ Error rate < 1%  
✅ Response time < 500ms (P95)  

## Support

- **Logs**: `gcloud run services logs read [service-name] --limit=100`
- **Status**: `gcloud run services describe [service-name]`
- **Full Guide**: See `DEPLOYMENT_GUIDE.md`
- **Troubleshooting**: Check deployment logs and validate environment variables

---

**Quick Start Command**:
```bash
# One-line validation and deployment
./validate-deployment-readiness.sh && cd core/cmms && ./deployment/deploy-consolidated-services.sh && ./deployment/validate-ai-endpoints.sh
```

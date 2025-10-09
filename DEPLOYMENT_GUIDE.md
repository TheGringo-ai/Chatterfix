# 🚀 ChatterFix CMMS - Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying ChatterFix CMMS to Google Cloud Platform (GCP) with all working changes merged into the main branch.

## ✅ Pre-Deployment Checklist

### 1. Code Validation Complete
- [x] All Python syntax validated
- [x] 18 unit tests passing
- [x] Import validation successful
- [x] Security scan completed

### 2. Merged Components
The following production-ready features have been merged from `main-clean`:

- **AI Brain Service**: Multi-provider AI support (OpenAI, xAI, Anthropic, Ollama)
- **Fix It Fred MVP**: Lead generation service with AI troubleshooting
- **Production Bug Fixes**: Template literals, API URLs, error handling
- **Enhanced Features**: Settings page, document intelligence
- **Deployment Scripts**: Automated GCP deployment and validation

### 3. Architecture

```
ChatterFix CMMS Platform
├── Backend Unified Service (1 CPU, 1Gi RAM)
│   ├── Database (PostgreSQL)
│   ├── Work Orders
│   ├── Assets Management
│   └── Parts Inventory
├── AI Unified Service (1 CPU, 1Gi RAM)
│   ├── AI Brain (Multi-provider)
│   └── Document Intelligence
└── Frontend Gateway (1 CPU, 512Mi RAM)
    └── Main UI and API Gateway
```

## 📋 GCP Prerequisites

### Required GCP Resources
1. **GCP Project**: `fredfix` or your project ID
2. **Cloud Run**: Enabled in project
3. **Artifact Registry**: For container images
4. **Cloud SQL**: PostgreSQL instance (optional, can use managed DB)
5. **IAM Permissions**: Cloud Run Admin, Service Account User

### Required Credentials
- GCP Service Account Key with Cloud Run permissions
- PostgreSQL database credentials (if using Cloud SQL)
- Optional: API keys for AI providers (OpenAI, xAI, Anthropic)

## 🔧 Configuration

### 1. Update GCP Project Settings

Edit `core/cmms/deployment/deploy-consolidated-services.sh`:

```bash
REGION="us-central1"  # Your preferred region
PROJECT_ID="your-project-id"
```

### 2. Set Environment Variables

The deployment will configure these environment variables in Cloud Run:

**Backend Service:**
```bash
DATABASE_TYPE=postgresql
PGHOST=your-postgres-host
PGDATABASE=chatterfix_cmms
PGUSER=chatterfix_user
PGPASSWORD=your-secure-password
SERVICE_MODE=unified_backend
```

**AI Service:**
```bash
DATABASE_SERVICE_URL=https://your-backend-url
SERVICE_MODE=unified_ai
OLLAMA_ENABLED=false
AI_PROVIDER=openai  # or xai, anthropic, ollama
OPENAI_API_KEY=your-key  # if using OpenAI
```

**Frontend Gateway:**
```bash
BACKEND_SERVICE_URL=https://your-backend-url
AI_SERVICE_URL=https://your-ai-url
```

## 🚀 Deployment Steps

### Step 1: Validate Deployment Readiness

```bash
./validate-deployment-readiness.sh
```

Expected output:
```
✅ ERRORS: 0
⚠️ WARNINGS: 1
🎉 DEPLOYMENT READY!
```

### Step 2: Authenticate with GCP

```bash
gcloud auth login
gcloud config set project your-project-id
```

### Step 3: Deploy Consolidated Services

```bash
cd core/cmms
./deployment/deploy-consolidated-services.sh
```

This will deploy three unified services:
1. `chatterfix-backend-unified` - Backend and database
2. `chatterfix-ai-unified` - AI and intelligence
3. `chatterfix-cmms` - Frontend gateway

### Step 4: Validate AI Endpoints

```bash
./deployment/validate-ai-endpoints.sh
```

This script will:
- Test health endpoints for all services
- Validate AI Brain functionality
- Update environment variables with correct service URLs
- Verify integration between services

### Step 5: Optional - Deploy Fix It Fred MVP

```bash
./deploy-fix-it-fred.sh
```

This deploys the standalone Fix It Fred service for lead generation.

## 🔍 Post-Deployment Validation

### 1. Check Service Status

```bash
gcloud run services list --region=us-central1
```

All services should show status: `READY`

### 2. Test Health Endpoints

```bash
# Backend health
curl https://chatterfix-backend-unified-[hash].run.app/health

# AI service health
curl https://chatterfix-ai-unified-[hash].run.app/health

# Frontend health
curl https://chatterfix-cmms-[hash].run.app/health
```

Expected response: `{"status": "healthy"}`

### 3. Test Main Application

Visit the frontend URL in your browser:
```
https://chatterfix-cmms-[hash].run.app
```

Verify:
- Landing page loads
- Work orders dashboard accessible
- Assets management functional
- AI assistant responds (if configured)

### 4. Monitor Logs

```bash
# View logs for main service
gcloud run services logs read chatterfix-cmms --region=us-central1

# View logs for AI service
gcloud run services logs read chatterfix-ai-unified --region=us-central1

# View logs for backend service
gcloud run services logs read chatterfix-backend-unified --region=us-central1
```

## 📊 Monitoring and Maintenance

### Service Metrics

Monitor in GCP Console:
- **Request Count**: Requests per second
- **Request Latency**: P50, P95, P99 latency
- **Error Rate**: 4xx and 5xx errors
- **Instance Count**: Active container instances

### Cost Optimization

Current configuration:
- **CPU Allocation**: 3 CPUs total (71% reduction from 7-service architecture)
- **Memory**: 2.5 Gi total
- **Max Instances**: 7 total (cost-controlled scaling)
- **Estimated Cost**: ~$50-150/month depending on traffic

### Scaling Configuration

Services auto-scale based on:
- **Concurrency**: 80 requests per instance
- **CPU Utilization**: Scale up at 60% CPU
- **Min Instances**: 0 (scale to zero when idle)
- **Max Instances**: 2-3 per service

## 🔄 Updates and Rollbacks

### Deploy Updates

```bash
# Pull latest changes
git pull origin main

# Validate changes
./validate-deployment-readiness.sh

# Deploy updates
cd core/cmms
./deployment/deploy-consolidated-services.sh
```

### Rollback to Previous Version

```bash
# List revisions
gcloud run revisions list --service=chatterfix-cmms --region=us-central1

# Rollback to specific revision
gcloud run services update-traffic chatterfix-cmms \
  --to-revisions=chatterfix-cmms-00001-abc=100 \
  --region=us-central1
```

## 🐛 Troubleshooting

### Service Won't Start

1. Check logs: `gcloud run services logs read [service-name]`
2. Verify environment variables are set correctly
3. Ensure database connection is working
4. Check that port is correctly set (8080)

### Database Connection Issues

1. Verify PostgreSQL instance is running
2. Check firewall rules allow Cloud Run connections
3. Verify database credentials in environment variables
4. Test connection from Cloud Shell

### AI Service Not Responding

1. Check AI_PROVIDER environment variable
2. Verify API keys are set correctly
3. Test with OLLAMA_ENABLED=false for external providers
4. Check service-to-service authentication

### High Error Rate

1. Review error logs for patterns
2. Check database query performance
3. Verify sufficient memory allocation
4. Monitor CPU throttling

## 📞 Support and Documentation

### Additional Resources

- **GitHub Actions**: `.github/workflows/deploy.yml` - Automated deployment pipeline
- **Pre-commit Hooks**: `.pre-commit-config.yaml` - Code quality checks
- **Testing**: `core/cmms/tests/` - Unit and integration tests
- **Fix It Fred Guide**: `core/cmms/FIX_IT_FRED_README.md`
- **TechBot Guide**: `core/cmms/TECHBOT_DEPLOYMENT_GUIDE.md`

### Architecture Documentation

- **Microservices**: `core/cmms/MICROSERVICES_ARCHITECTURE.md`
- **AI Platform**: `core/cmms/CHATTERFIX_AI_PLATFORM_DOCUMENTATION.md`
- **Document Intelligence**: `core/cmms/DOCUMENT_INTELLIGENCE_API.md`

## ✅ Deployment Success Criteria

- [ ] All services deployed and showing READY status
- [ ] Health endpoints returning healthy status
- [ ] Frontend accessible and rendering correctly
- [ ] Work orders dashboard functional
- [ ] Assets management working
- [ ] AI assistant responding (if configured)
- [ ] Database operations successful
- [ ] Error rate below 1%
- [ ] Response time under 500ms for 95th percentile

## 🎉 Production Launch

Once all success criteria are met:

1. **Configure Custom Domain** (optional)
   ```bash
   gcloud run domain-mappings create \
     --service=chatterfix-cmms \
     --domain=chatterfix.com \
     --region=us-central1
   ```

2. **Set Up Monitoring Alerts**
   - Configure error rate alerts
   - Set up latency monitoring
   - Create uptime checks

3. **Enable Backup Strategy**
   - Configure Cloud SQL automated backups
   - Set up point-in-time recovery
   - Test backup restoration process

4. **Document Production URLs**
   - Main application URL
   - API endpoints
   - Admin dashboard URL

## 🔐 Security Considerations

- All services use HTTPS by default
- Environment variables stored securely in Cloud Run
- Database credentials managed through Secret Manager (recommended)
- API authentication enabled for sensitive endpoints
- Regular security updates via GitHub Dependabot
- Pre-commit hooks scan for secrets

## 📈 Next Steps

After successful deployment:

1. Monitor performance for 24-48 hours
2. Review logs for any errors or warnings
3. Test all critical user flows
4. Configure alerting and monitoring dashboards
5. Document any production-specific configuration
6. Plan for regular maintenance windows

---

**Deployment Date**: _To be completed_  
**Deployed By**: _To be completed_  
**Production URL**: _To be completed_  
**Status**: ✅ Ready for Deployment

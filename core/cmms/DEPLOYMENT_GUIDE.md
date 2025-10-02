# ChatterFix CMMS - Microservices Deployment Guide

## Quick Start

Deploy the complete ChatterFix CMMS microservices architecture to resolve the 503 deployment issues:

```bash
# One-command deployment
./deploy-microservices.sh
```

This will deploy both the database service and main application to Cloud Run, configure domain mapping, and set up service-to-service communication.

## What This Solves

✅ **Resolved Cloud Run 503 Errors** - Separated complex monolith into lightweight services  
✅ **Database Connectivity Issues** - Dedicated database service with proper connection management  
✅ **Deployment Timeouts** - Reduced startup time with minimal dependencies per service  
✅ **Scalability Problems** - Independent scaling of database and application layers  

## Architecture

```
Internet → chatterfix.com → Main App Service → Database Service → PostgreSQL
```

- **Main App**: UI, business logic, authentication (2Gi RAM, 2 CPU)
- **Database Service**: All database operations (1Gi RAM, 1 CPU)

## Prerequisites

1. **Google Cloud Setup**:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Enable Required APIs**:
   ```bash
   gcloud services enable run.googleapis.com
   gcloud services enable cloudbuild.googleapis.com
   ```

## Deployment Options

### Option 1: Complete Deployment (Recommended)
```bash
./deploy-microservices.sh
```

### Option 2: Step-by-Step Deployment
```bash
# Deploy database service first
./deploy-database-service.sh

# Deploy main application
./deploy-main-app.sh
```

### Option 3: Local Testing First
```bash
# Test locally with Docker Compose
./test-microservices.sh

# If tests pass, deploy to Cloud Run
./deploy-microservices.sh
```

## Verification

After deployment, your services will be available at:

- **Production URL**: https://chatterfix.com
- **Direct Cloud Run URLs**:
  - Main App: `https://chatterfix-cmms-[region]-[project].a.run.app`
  - Database: `https://chatterfix-database-[region]-[project].a.run.app`

### Health Checks

```bash
# Check main application
curl https://chatterfix.com/health

# Check database service
curl https://chatterfix-database-[region]-[project].a.run.app/health
```

### Test Functionality

1. Open https://chatterfix.com
2. Navigate to Work Orders, Assets, Parts pages
3. Try creating new work orders and assets
4. Verify data persistence

## Configuration

### Environment Variables Set Automatically

**Database Service**:
- `DATABASE_URL`: PostgreSQL connection string
- `ENVIRONMENT`: production

**Main Application**:
- `DATABASE_SERVICE_URL`: Auto-detected database service URL
- `DOMAIN`: chatterfix.com
- `JWT_SECRET`: Authentication secret

### Custom Configuration

Modify the deployment scripts to customize:

```bash
# In deploy-main-app.sh or deploy-database-service.sh
--set-env-vars "CUSTOM_VAR=value,ANOTHER_VAR=value"
```

## Monitoring

### View Logs
```bash
# Main application logs
gcloud logs tail --service=chatterfix-cmms

# Database service logs
gcloud logs tail --service=chatterfix-database
```

### Monitor Resources
```bash
# Service status
gcloud run services list

# Service details
gcloud run services describe chatterfix-cmms --region=us-central1
gcloud run services describe chatterfix-database --region=us-central1
```

## Troubleshooting

### Common Issues

1. **Domain not resolving**:
   - Configure DNS: Point chatterfix.com to `ghs.googlehosted.com`
   - Check domain mapping: `gcloud run domain-mappings list`

2. **Database connection errors**:
   - Verify PostgreSQL is accessible
   - Check database service health: `/health` endpoint
   - Review database service logs

3. **Service communication errors**:
   - Ensure both services are deployed
   - Check `DATABASE_SERVICE_URL` environment variable
   - Verify internal networking

### Recovery Commands

```bash
# Redeploy database service
./deploy-database-service.sh

# Redeploy main application
./deploy-main-app.sh

# Full redeployment
./deploy-microservices.sh
```

## Development Workflow

### Local Development
```bash
# Start local services
docker-compose up --build

# Test changes
./test-microservices.sh

# Deploy when ready
./deploy-microservices.sh
```

### Making Changes

1. **Database Service Changes**: Edit `database_service.py`, redeploy with `./deploy-database-service.sh`
2. **Main App Changes**: Edit `app_microservice.py`, redeploy with `./deploy-main-app.sh`
3. **Schema Changes**: Update schema in `database_service.py` initialization

## Files Created

### Core Services
- `/Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms/database_service.py` - Database microservice
- `/Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms/app_microservice.py` - Main application
- `/Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms/database_client.py` - HTTP client for database service

### Deployment Infrastructure
- `/Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms/Dockerfile.database` - Database service container
- `/Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms/Dockerfile.app` - Main application container
- `/Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms/deploy-microservices.sh` - Complete deployment script
- `/Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms/docker-compose.yml` - Local development environment

### Configuration
- `/Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms/database_service_requirements.txt` - Database service dependencies
- `/Users/fredtaylor/Desktop/Projects/ai-tools/core/cmms/app_microservice_requirements.txt` - Main app dependencies

## Success Metrics

After deployment, you should see:

✅ **Fast deployment times** (< 5 minutes total)  
✅ **Stable service startup** (no 503 errors)  
✅ **Responsive UI** at chatterfix.com  
✅ **Working database operations** (CRUD operations)  
✅ **Independent service scaling**  
✅ **Clear error handling and logging**  

## Support

If you encounter issues:

1. Check the comprehensive logs from both services
2. Verify all prerequisites are met
3. Test locally first with Docker Compose
4. Review the detailed architecture documentation

The microservices architecture provides a robust, scalable foundation for ChatterFix CMMS that resolves the previous deployment issues while maintaining all functionality.
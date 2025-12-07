# ChatterFix CMMS - Deployment Documentation

## Table of Contents
1. [Overview](#overview)
2. [Automated Deployment](#automated-deployment)
3. [Manual Deployment](#manual-deployment)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Rollback Procedures](#rollback-procedures)
7. [Monitoring](#monitoring)

---

## Overview

ChatterFix CMMS is deployed to Google Cloud Run, a fully managed serverless platform. The application supports both automated CI/CD deployment via GitHub Actions and manual deployment using scripts.

### Deployment Architecture

- **Platform**: Google Cloud Run (fully managed)
- **Region**: us-central1
- **Project ID**: fredfix
- **Service Name**: chatterfix-cmms
- **Container Registry**: Google Container Registry (GCR)
- **Database**: Firebase Firestore
- **Authentication**: Firebase Authentication

### Key Features

- ✅ Automatic deployment on push to `main` branch
- ✅ Staging environment for testing pull requests
- ✅ Health check verification
- ✅ Zero-downtime deployments
- ✅ Automatic rollback on failure
- ✅ Environment variable management

---

## Automated Deployment

### GitHub Actions Workflows

The repository includes multiple deployment workflows:

#### 1. **Production Deployment** (`.github/workflows/deploy.yml`)

Automatically deploys to production on push to `main` branch.

**Triggers:**
- Push to `main` branch
- Manual workflow dispatch

**Features:**
- Pre-deployment validation checks
- Secret validation
- Automated health checks
- Deployment status notifications
- Rollback capability

**Configuration:**
```yaml
name: Deploy to Production
on:
  push:
    branches: [main]
  workflow_dispatch:
```

#### 2. **Staging Deployment** (`.github/workflows/staging-deploy.yml`)

Deploys to staging environment for testing.

**Triggers:**
- Push to `develop` or `staging` branches
- Pull requests to `main`
- Manual workflow dispatch

**Features:**
- Staging environment testing
- PR preview comments
- Health checks

#### 3. **Quick Deploy** (`.github/workflows/deploy-now.yml`)

Manual deployment that skips pre-checks for urgent fixes.

**Triggers:**
- Manual workflow dispatch only

---

## Configuration

### Required GitHub Secrets

Configure these secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

| Secret Name | Description | Required |
|------------|-------------|----------|
| `GCP_SA_KEY` | Google Cloud Service Account JSON key | ✅ Yes |
| `FIREBASE_API_KEY` | Firebase Web API key | ✅ Yes |
| `GEMINI_API_KEY` | Google Gemini AI API key | ✅ Yes |
| `OPENAI_API_KEY` | OpenAI API key | ✅ Yes |
| `GROK_API_KEY` | Grok AI API key | ✅ Yes |

### Setting Up Google Cloud Service Account

1. **Create a Service Account:**
   ```bash
   gcloud iam service-accounts create chatterfix-deploy \
     --display-name="ChatterFix Deployment Service Account" \
     --project=fredfix
   ```

2. **Grant Required Permissions:**
   ```bash
   # Cloud Run Admin
   gcloud projects add-iam-policy-binding fredfix \
     --member="serviceAccount:chatterfix-deploy@fredfix.iam.gserviceaccount.com" \
     --role="roles/run.admin"
   
   # Storage Admin (for Container Registry)
   gcloud projects add-iam-policy-binding fredfix \
     --member="serviceAccount:chatterfix-deploy@fredfix.iam.gserviceaccount.com" \
     --role="roles/storage.admin"
   
   # Service Account User
   gcloud projects add-iam-policy-binding fredfix \
     --member="serviceAccount:chatterfix-deploy@fredfix.iam.gserviceaccount.com" \
     --role="roles/iam.serviceAccountUser"
   
   # Cloud Build Service Account
   gcloud projects add-iam-policy-binding fredfix \
     --member="serviceAccount:chatterfix-deploy@fredfix.iam.gserviceaccount.com" \
     --role="roles/cloudbuild.builds.builder"
   ```

3. **Generate Service Account Key:**
   ```bash
   gcloud iam service-accounts keys create key.json \
     --iam-account=chatterfix-deploy@fredfix.iam.gserviceaccount.com
   ```

4. **Add Key to GitHub Secrets:**
   - Copy the contents of `key.json`
   - Go to GitHub repository settings
   - Navigate to `Secrets and variables > Actions`
   - Click `New repository secret`
   - Name: `GCP_SA_KEY`
   - Value: Paste the entire JSON content
   - Click `Add secret`

### Workload Identity Federation (Recommended Alternative)

For enhanced security, use Workload Identity Federation instead of service account keys:

1. **Create Workload Identity Pool:**
   ```bash
   gcloud iam workload-identity-pools create "github-pool" \
     --project="fredfix" \
     --location="global" \
     --display-name="GitHub Actions Pool"
   ```

2. **Create Workload Identity Provider:**
   ```bash
   gcloud iam workload-identity-pools providers create-oidc "github-provider" \
     --project="fredfix" \
     --location="global" \
     --workload-identity-pool="github-pool" \
     --display-name="GitHub Actions Provider" \
     --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
     --issuer-uri="https://token.actions.githubusercontent.com"
   ```

3. **Grant Service Account Access:**
   ```bash
   gcloud iam service-accounts add-iam-policy-binding \
     "chatterfix-deploy@fredfix.iam.gserviceaccount.com" \
     --project="fredfix" \
     --role="roles/iam.workloadIdentityUser" \
     --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/TheGringo-ai/Chatterfix"
   ```

4. **Update GitHub Workflow:**
   ```yaml
   - name: Authenticate to Google Cloud
     uses: google-github-actions/auth@v2
     with:
       workload_identity_provider: 'projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
       service_account: 'chatterfix-deploy@fredfix.iam.gserviceaccount.com'
   ```

### Environment Variables

The following environment variables are automatically set during deployment:

| Variable | Value | Description |
|----------|-------|-------------|
| `USE_FIRESTORE` | `true` | Enable Firestore database |
| `GOOGLE_CLOUD_PROJECT` | `fredfix` | GCP project ID |
| `ENVIRONMENT` | `production` | Deployment environment |
| `CMMS_PORT` | `8080` | Application port |
| `LOG_LEVEL` | `info` | Logging level |
| `FIREBASE_API_KEY` | (secret) | Firebase configuration |
| `GEMINI_API_KEY` | (secret) | AI service key |
| `OPENAI_API_KEY` | (secret) | AI service key |
| `GROK_API_KEY` | (secret) | AI service key |

---

## Manual Deployment

### Using deploy.sh Script

The `deploy.sh` script provides a unified deployment interface.

#### Direct Deployment (Fast)

```bash
./deploy.sh direct
```

This method:
- Builds Docker image locally
- Pushes to Google Container Registry
- Deploys directly to Cloud Run
- Fastest deployment method

#### Cloud Build Deployment (Recommended for CI/CD)

```bash
./deploy.sh cloudbuild
```

This method:
- Uses Google Cloud Build
- Builds in cloud infrastructure
- Better for CI/CD pipelines
- More reliable for large builds

### Prerequisites for Manual Deployment

1. **Install Google Cloud SDK:**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Linux
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   ```

2. **Authenticate:**
   ```bash
   gcloud auth login
   gcloud config set project fredfix
   ```

3. **Docker Authentication:**
   ```bash
   gcloud auth configure-docker
   ```

4. **Required Tools:**
   - Docker Desktop or Docker Engine
   - Git
   - gcloud CLI

### Step-by-Step Manual Deployment

1. **Clone Repository:**
   ```bash
   git clone https://github.com/TheGringo-ai/Chatterfix.git
   cd Chatterfix
   ```

2. **Verify Configuration:**
   ```bash
   # Check GCP project
   gcloud config get-value project
   
   # Verify service exists
   gcloud run services describe chatterfix-cmms --region=us-central1
   ```

3. **Deploy:**
   ```bash
   # Using deploy script
   ./deploy.sh direct
   
   # Or using gcloud directly
   gcloud run deploy chatterfix-cmms \
     --source . \
     --region us-central1 \
     --set-env-vars="USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=fredfix" \
     --memory=4Gi \
     --cpu=2 \
     --min-instances=1 \
     --max-instances=10 \
     --allow-unauthenticated
   ```

4. **Verify Deployment:**
   ```bash
   # Get service URL
   URL=$(gcloud run services describe chatterfix-cmms \
     --region us-central1 \
     --format='value(status.url)')
   
   # Test health endpoint
   curl "$URL/health"
   ```

---

## Troubleshooting

### Common Issues

#### 1. **Deployment Fails with "Service Not Found"**

**Error:**
```
ERROR: (gcloud.run.services.describe) The requested resource does not exist.
```

**Solution:**
Create the service first:
```bash
gcloud run deploy chatterfix-cmms \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

#### 2. **Permission Denied Errors**

**Error:**
```
ERROR: (gcloud.run.deploy) PERMISSION_DENIED: Permission denied
```

**Solution:**
Check service account permissions:
```bash
gcloud projects get-iam-policy fredfix \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:YOUR_SA_EMAIL"
```

Ensure the service account has:
- `roles/run.admin`
- `roles/storage.admin`
- `roles/iam.serviceAccountUser`

#### 3. **Build Timeout**

**Error:**
```
ERROR: build step timed out
```

**Solution:**
Increase timeout in cloudbuild.yaml:
```yaml
timeout: "2400s"  # 40 minutes
```

#### 4. **Health Check Failures**

**Error:**
```
Health check failed - service returned 503
```

**Solutions:**
1. Check application logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=chatterfix-cmms" \
     --limit 50 \
     --format json
   ```

2. Verify environment variables:
   ```bash
   gcloud run services describe chatterfix-cmms \
     --region us-central1 \
     --format="value(spec.template.spec.containers[0].env)"
   ```

3. Test locally:
   ```bash
   docker run -p 8080:8080 \
     -e USE_FIRESTORE=true \
     -e GOOGLE_CLOUD_PROJECT=fredfix \
     gcr.io/fredfix/chatterfix-cmms:latest
   ```

#### 5. **Container Start Timeout**

**Error:**
```
Container failed to start. Failed to start and then listen on the port defined by the PORT environment variable.
```

**Solution:**
1. Increase container startup time:
   ```bash
   gcloud run services update chatterfix-cmms \
     --region us-central1 \
     --timeout=300
   ```

2. Check if the application is binding to the correct port:
   ```python
   # main.py should use PORT from environment
   PORT = int(os.getenv("PORT", 8080))
   ```

#### 6. **Memory Limit Exceeded**

**Error:**
```
Container exceeded memory limit
```

**Solution:**
Increase memory allocation:
```bash
gcloud run services update chatterfix-cmms \
  --region us-central1 \
  --memory=4Gi
```

### Debugging Commands

```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 \
  --project fredfix

# Check service status
gcloud run services describe chatterfix-cmms \
  --region us-central1

# List all revisions
gcloud run revisions list \
  --service chatterfix-cmms \
  --region us-central1

# Get current traffic split
gcloud run services describe chatterfix-cmms \
  --region us-central1 \
  --format="value(status.traffic)"

# Test deployment locally
docker build -t chatterfix-test .
docker run -p 8080:8080 chatterfix-test
```

---

## Rollback Procedures

### Automatic Rollback

GitHub Actions workflow includes automatic rollback on deployment failure. If health checks fail, the previous revision remains active.

### Manual Rollback

#### 1. **List Available Revisions**

```bash
gcloud run revisions list \
  --service chatterfix-cmms \
  --region us-central1 \
  --format="table(name,creationTimestamp,status)"
```

#### 2. **Rollback to Specific Revision**

```bash
# Rollback to previous revision
PREVIOUS_REVISION=$(gcloud run revisions list \
  --service chatterfix-cmms \
  --region us-central1 \
  --format="value(name)" \
  --limit=2 | tail -1)

gcloud run services update-traffic chatterfix-cmms \
  --to-revisions=$PREVIOUS_REVISION=100 \
  --region us-central1
```

#### 3. **Rollback to Named Revision**

```bash
gcloud run services update-traffic chatterfix-cmms \
  --to-revisions=chatterfix-cmms-00042-abc=100 \
  --region us-central1
```

#### 4. **Gradual Rollback (Canary)**

```bash
# Split traffic: 80% old, 20% new
gcloud run services update-traffic chatterfix-cmms \
  --to-revisions=REVISION_OLD=80,REVISION_NEW=20 \
  --region us-central1
```

#### 5. **Emergency Rollback via GitHub Actions**

1. Go to GitHub Actions
2. Select "Deploy to Production" workflow
3. Click "Run workflow"
4. Select the previous successful commit SHA
5. Run deployment

### Post-Rollback Verification

```bash
# Get current active revision
CURRENT=$(gcloud run services describe chatterfix-cmms \
  --region us-central1 \
  --format='value(status.latestReadyRevisionName)')

echo "Active revision: $CURRENT"

# Verify health
SERVICE_URL=$(gcloud run services describe chatterfix-cmms \
  --region us-central1 \
  --format='value(status.url)')

curl "$SERVICE_URL/health"
```

---

## Monitoring

### Health Check Endpoint

**URL:** `https://chatterfix-cmms-XXXXX-uc.a.run.app/health`

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-07T02:42:00.000Z",
  "database": "firestore_ok",
  "version": "2.2.0-interactive-planner",
  "service": "chatterfix-cmms"
}
```

### Cloud Logging

```bash
# Stream logs in real-time
gcloud logging tail "resource.type=cloud_run_revision" \
  --project fredfix

# View errors only
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit 50 \
  --project fredfix

# Filter by service
gcloud logging read "resource.labels.service_name=chatterfix-cmms" \
  --limit 100 \
  --project fredfix
```

### Metrics and Alerts

Monitor key metrics in Google Cloud Console:

1. **Request Latency**: Target < 500ms
2. **Error Rate**: Target < 1%
3. **Instance Count**: Min 1, Max 10
4. **Memory Usage**: Target < 80% of 4GB
5. **CPU Usage**: Target < 80%

Set up alerts:
```bash
# Create alert policy for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="ChatterFix High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05
```

### Deployment Status

Check deployment status:
```bash
# Latest deployment
gcloud run revisions list \
  --service chatterfix-cmms \
  --region us-central1 \
  --limit 1

# Traffic distribution
gcloud run services describe chatterfix-cmms \
  --region us-central1 \
  --format="table(status.traffic[].revisionName,status.traffic[].percent)"
```

---

## Best Practices

### Security

1. **Never commit secrets** to the repository
2. **Use least-privilege service accounts** with only necessary permissions
3. **Enable Cloud Armor** for DDoS protection
4. **Use HTTPS** for all endpoints (automatic with Cloud Run)
5. **Rotate service account keys** regularly (every 90 days)
6. **Use Workload Identity Federation** instead of service account keys when possible

### Performance

1. **Set minimum instances** to 1 for production to avoid cold starts
2. **Use appropriate memory** allocation (4GB recommended)
3. **Enable HTTP/2** for better performance
4. **Use Cloud CDN** for static assets
5. **Monitor and optimize** container size

### Cost Optimization

1. **Set maximum instances** to prevent runaway costs
2. **Use staging environment** with 0 minimum instances
3. **Clean up old revisions** regularly:
   ```bash
   gcloud run revisions list --service chatterfix-cmms --region us-central1 \
     --format="value(name)" | tail -n +6 | xargs -I {} gcloud run revisions delete {} --region us-central1 --quiet
   ```
4. **Monitor billing** alerts

### Deployment

1. **Test in staging** before production
2. **Use semantic versioning** for releases
3. **Maintain deployment logs** for audit trail
4. **Document all configuration** changes
5. **Perform health checks** after every deployment

---

## Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Firebase Documentation](https://firebase.google.com/docs)
- [ChatterFix CMMS GitHub Repository](https://github.com/TheGringo-ai/Chatterfix)

---

## Support

For deployment issues or questions:
- Open an issue on GitHub: https://github.com/TheGringo-ai/Chatterfix/issues
- Check Cloud Run logs: `gcloud logging read "resource.type=cloud_run_revision"`
- Review GitHub Actions logs in the Actions tab

---

**Last Updated:** December 2025  
**Version:** 2.2.0-interactive-planner

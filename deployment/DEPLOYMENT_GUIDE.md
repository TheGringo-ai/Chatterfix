# ChatterFix CMMS - GCP Deployment Guide

## Prerequisites

1. **Google Cloud Account**
   - Create account at https://cloud.google.com
   - Enable billing
   - $300 free credit for new users

2. **Install Google Cloud SDK**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Or download from
   https://cloud.google.com/sdk/docs/install
   ```

3. **Install Docker** (for local testing)
   ```bash
   brew install docker
   ```

## Quick Start Deployment

### 1. Run Setup Script

```bash
cd deployment
./setup-gcp.sh
```

This script will:
- Enable required GCP APIs
- Create App Engine application
- Set up Cloud Storage bucket
- Create service account for CI/CD
- Generate service account key

### 2. Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

- `GCP_SA_KEY`: Contents of `gcp-key.json`
- `GCP_PROJECT_ID`: Your GCP project ID

### 3. Deploy

```bash
# Manual deployment
gcloud app deploy deployment/app.yaml

# Or push to main branch for automatic deployment
git push origin main
```

## Manual Setup (Step by Step)

### 1. Create GCP Project

```bash
# Set project ID
export PROJECT_ID="chatterfix-prod"

# Create project
gcloud projects create $PROJECT_ID

# Set as default
gcloud config set project $PROJECT_ID
```

### 2. Enable APIs

```bash
gcloud services enable appengine.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable storage.googleapis.com
```

### 3. Create App Engine App

```bash
gcloud app create --region=us-central1
```

### 4. Deploy Application

```bash
gcloud app deploy deployment/app.yaml
```

## Environment Variables

Update `deployment/app.yaml` with your environment variables:

```yaml
env_variables:
  SECRET_KEY: "your-production-secret-key"
  GEMINI_API_KEY: "your-gemini-api-key"
  XAI_API_KEY: "your-xai-api-key"
```

Or use Secret Manager (recommended):

```bash
# Create secrets
echo -n "your-secret-key" | gcloud secrets create secret-key --data-file=-
echo -n "your-gemini-key" | gcloud secrets create gemini-api-key --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding secret-key \
  --member="serviceAccount:PROJECT_ID@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Custom Domain Setup

### 1. Verify Domain Ownership

```bash
gcloud app domain-mappings create chatterfix.com
```

### 2. Update DNS Records

Add these records to your domain registrar:

```
Type: A
Name: @
Value: [IP from previous command]

Type: AAAA
Name: @
Value: [IPv6 from previous command]

Type: CNAME
Name: www
Value: ghs.googlehosted.com
```

### 3. Enable SSL

SSL is automatically provisioned by Google. Wait 15-30 minutes for certificate.

## Database Options

### Option 1: SQLite (Simple, Low Cost)

Current setup uses SQLite stored in App Engine filesystem.

**Pros:**
- Simple setup
- No additional cost
- Good for small-medium deployments

**Cons:**
- Data lost on instance restart
- Not suitable for high traffic

### Option 2: Cloud SQL (Production)

```bash
# Create Cloud SQL instance
gcloud sql instances create chatterfix-db \
  --database-version=POSTGRES_14 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create cmms --instance=chatterfix-db

# Update app.yaml
env_variables:
  CMMS_DB_PATH: "/cloudsql/PROJECT_ID:REGION:chatterfix-db"
```

## Monitoring & Logs

### View Logs

```bash
# Real-time logs
gcloud app logs tail

# Recent logs
gcloud app logs read --limit=50
```

### View Metrics

Visit: https://console.cloud.google.com/appengine

## Cost Optimization

### Free Tier

- 28 instance hours/day free (F1/F2 instances)
- 1GB outbound data/day free
- 5GB Cloud Storage free

### Estimated Monthly Costs

**Minimal Usage:**
- App Engine F2: $0 (within free tier)
- Total: **$0/month**

**Medium Usage:**
- App Engine F2: $50-100
- Cloud SQL db-f1-micro: $10-15
- Cloud Storage: $1-5
- Total: **$60-120/month**

### Cost Reduction Tips

1. Use automatic scaling with min_instances: 0
2. Use Cloud Storage for static files
3. Enable Cloud CDN
4. Use SQLite instead of Cloud SQL for small deployments

## CI/CD Pipeline

### GitHub Actions Workflow

Automatically deploys on push to main:

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]
```

### Manual Deployment

```bash
# Deploy specific version
gcloud app deploy --version=v1 --no-promote

# Test staging
curl https://v1-dot-PROJECT_ID.appspot.com

# Promote to production
gcloud app services set-traffic default --splits=v1=1
```

## Rollback

```bash
# List versions
gcloud app versions list

# Rollback
gcloud app versions migrate PREVIOUS_VERSION
```

## Troubleshooting

### Application Won't Start

```bash
# Check logs
gcloud app logs tail

# Common issues:
# - Missing dependencies in requirements.txt
# - Database connection errors
# - Port configuration (must use 8080)
```

### 502 Bad Gateway

- Check instance class (F2 recommended)
- Verify gunicorn configuration
- Check startup time (increase timeout if needed)

### Database Errors

```bash
# Verify database path
gcloud app instances list
gcloud app instances ssh INSTANCE_ID
ls -la /app/data/
```

## Security Checklist

- [ ] Use Secret Manager for API keys
- [ ] Enable HTTPS only
- [ ] Set secure session cookies
- [ ] Configure CORS properly
- [ ] Enable Cloud Armor (DDoS protection)
- [ ] Set up Cloud IAM roles
- [ ] Enable audit logging

## Support

For issues:
1. Check logs: `gcloud app logs tail`
2. Review documentation: https://cloud.google.com/appengine/docs
3. GitHub Issues: https://github.com/TheGringo-ai/Chatterfix/issues

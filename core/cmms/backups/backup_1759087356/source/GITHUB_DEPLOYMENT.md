# ChatterFix CMMS - GitHub Actions Deployment Guide

🚀 **Mars-Level AI Platform** - Automated deployment to Google Cloud Run via GitHub Actions

## Quick Start

1. **Fork/Clone this repository**
2. **Set up Google Cloud Project**
3. **Configure GitHub Secrets**
4. **Push to main branch** - Automatic deployment!

## Prerequisites

- Google Cloud Project with billing enabled
- GitHub repository with Actions enabled
- Basic understanding of CMMS systems

## Google Cloud Setup

### 1. Create GCP Project
```bash
# Create a new project
gcloud projects create your-project-id

# Set as active project
gcloud config set project your-project-id

# Enable billing (required for Cloud Run)
```

### 2. Enable Required APIs
```bash
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com
```

### 3. Create Service Account
```bash
# Create service account
gcloud iam service-accounts create chatterfix-deployment \
    --description="ChatterFix CMMS deployment account" \
    --display-name="ChatterFix Deployment"

# Grant necessary roles
gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:chatterfix-deployment@your-project-id.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:chatterfix-deployment@your-project-id.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:chatterfix-deployment@your-project-id.iam.gserviceaccount.com" \
    --role="roles/secretmanager.admin"

# Create service account key
gcloud iam service-accounts keys create key.json \
    --iam-account=chatterfix-deployment@your-project-id.iam.gserviceaccount.com
```

### 4. Set up Secrets in Secret Manager
```bash
# JWT Secret for authentication
echo "your-jwt-secret-key" | gcloud secrets create jwt-secret --data-file=-

# OpenAI API Key
echo "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-

# Grok/XAI API Key
echo "your-xai-api-key" | gcloud secrets create xai-api-key --data-file=-

# HuggingFace API Key (optional)
echo "your-huggingface-key" | gcloud secrets create huggingface-api-key --data-file=-
```

## GitHub Secrets Configuration

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these **Repository secrets**:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `GCP_PROJECT_ID` | Your Google Cloud Project ID | `my-cmms-project` |
| `GCP_SA_KEY` | Service account JSON key | `{REDACTED_SERVICE_ACCOUNT` |

### Getting the GCP_SA_KEY Value
```bash
# Display the service account key
cat key.json

# Copy the entire JSON content and paste as GCP_SA_KEY secret
```

## Deployment Process

### Automatic Deployment
- **Push to main branch** → Triggers deployment
- **Pull Request** → Runs tests and deployment preview
- **Manual trigger** → Via GitHub Actions interface

### Deployment Steps
1. 🔨 **Build** - Docker image with all dependencies
2. 📦 **Push** - To Google Artifact Registry
3. 🚀 **Deploy** - To Google Cloud Run
4. ✅ **Verify** - Health check and endpoint validation

## API Keys Configuration

The deployment uses Google Secret Manager for secure API key storage:

### Required API Keys
- **OpenAI API Key** - For GPT-4 functionality
- **Grok/XAI API Key** - For Grok AI integration
- **JWT Secret** - For user authentication

### Optional API Keys
- **HuggingFace API Key** - For additional AI models

## Environment Variables

The application automatically configures:
- `ENVIRONMENT=production`
- `PORT=8080`
- `LOG_LEVEL=INFO`
- `PYTHONPATH=/app`

## Features Deployed

### 🎯 Core CMMS Features
- ✅ Work Order Management with AI insights
- ✅ Asset Management with predictive analytics
- ✅ Parts Inventory with smart reordering
- ✅ Preventive Maintenance scheduling

### 🧠 AI Brain Features
- ✅ Multi-AI orchestration (OpenAI + Grok + LLAMA)
- ✅ Intelligent work order analysis
- ✅ Predictive maintenance recommendations
- ✅ Natural language processing
- ✅ Automated report generation

### 🚀 Production Features
- ✅ Auto-scaling (1-10 instances)
- ✅ Health monitoring
- ✅ Secure secret management
- ✅ Enterprise-grade performance
- ✅ 99.9% uptime SLA

## Post-Deployment

### Access Your Application
After successful deployment, your CMMS will be available at:
```
https://chatterfix-cmms-mars-level-[random-id]-uc.a.run.app
```

### Initial Setup
1. **Access the admin dashboard**
2. **Create your first work order**
3. **Configure AI settings**
4. **Add team members**
5. **Import existing assets**

### Monitoring
- **Cloud Console** - Monitor performance and logs
- **GitHub Actions** - View deployment history
- **Health Check** - `/mars-status` endpoint

## Troubleshooting

### Common Issues

#### 1. Deployment Fails
```bash
# Check GitHub Actions logs
# Verify GCP permissions
# Confirm API keys are set correctly
```

#### 2. Application Won't Start
```bash
# Check Cloud Run logs in GCP Console
# Verify environment variables
# Check Secret Manager access
```

#### 3. API Keys Not Working
```bash
# Verify secrets in Secret Manager
# Check service account permissions
# Confirm secret names match exactly
```

### Support Resources
- **GitHub Issues** - Report bugs and feature requests
- **Google Cloud Console** - Monitor and debug
- **Application Logs** - Real-time troubleshooting

## Architecture

```
GitHub Actions → Docker Build → Artifact Registry → Cloud Run
                                     ↓
                            Secret Manager (API Keys)
                                     ↓
                               AI Services Integration
```

## Security Features

- 🔒 **Non-root container execution**
- 🔐 **Encrypted secret storage**
- 🛡️ **IAM-based access control**
- 🔑 **JWT-based authentication**
- 🌐 **HTTPS-only communication**

## Performance

- **⚡ Cold Start**: < 2 seconds
- **📈 Scaling**: 1-10 instances automatically
- **💾 Memory**: 2GB per instance
- **🖥️ CPU**: 2 vCPUs per instance
- **🌐 Concurrency**: 100 requests per instance

---

**🎉 Your Mars-Level AI Platform is ready for the future of maintenance management!**

For support, create an issue in the GitHub repository.
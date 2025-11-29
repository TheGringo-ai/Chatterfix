# ChatterFix CLI Deployment Guide

Complete deployment of ChatterFix to `chatterfix.com` via Google Cloud CLI.

## 🚀 One-Command Deployment

```bash
./deploy-cli.sh
```

## 📋 Prerequisites

1. **Google Cloud CLI installed**
   ```bash
   # macOS
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   
   # Or via Homebrew
   brew install --cask google-cloud-sdk
   ```

2. **Docker installed and running**

3. **Domain ownership** of `chatterfix.com`

## 🔧 Manual Step-by-Step (if needed)

### 1. Authenticate and Set Project

```bash
# Login to Google Cloud
gcloud auth login

# Set project ID
export PROJECT_ID="chatterfix-cmms"
gcloud config set project $PROJECT_ID

# Create project if needed
gcloud projects create $PROJECT_ID --name="ChatterFix CMMS"
```

### 2. Enable Required APIs

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com  
gcloud services enable containerregistry.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable firebase.googleapis.com
```

### 3. Set Up Firestore Database

```bash
gcloud firestore databases create \
    --region=us-central1 \
    --type=firestore-native
```

### 4. Build and Push Container

```bash
# Configure Docker for gcloud
gcloud auth configure-docker

# Build the image
docker build -t gcr.io/$PROJECT_ID/chatterfix-cmms:latest .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/chatterfix-cmms:latest
```

### 5. Deploy to Cloud Run

```bash
gcloud run deploy chatterfix-cmms \
    --image=gcr.io/$PROJECT_ID/chatterfix-cmms:latest \
    --region=us-central1 \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,LOG_LEVEL=info" \
    --memory=2Gi \
    --cpu=1 \
    --max-instances=10 \
    --min-instances=1
```

### 6. Set Up Custom Domain

**First, verify domain ownership:**
1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add `chatterfix.com` as a property
3. Complete domain verification

**Then create domain mapping:**
```bash
gcloud run domain-mappings create \
    --service=chatterfix-cmms \
    --domain=chatterfix.com \
    --region=us-central1
```

**Get DNS records:**
```bash
gcloud run domain-mappings describe chatterfix.com \
    --region=us-central1 \
    --format="table(status.resourceRecords[].name,status.resourceRecords[].type,status.resourceRecords[].rrdata)"
```

### 7. Configure DNS Records

Add these to your DNS provider:

**CNAME Record:**
```
Name: @ (or chatterfix.com)
Type: CNAME
Value: ghs.googlehosted.com
TTL: 300
```

**TXT Record (for SSL verification):**
```
Name: _acme-challenge.chatterfix.com
Type: TXT
Value: [from gcloud output]
TTL: 300
```

### 8. Set Up Firebase Authentication

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login and set project
firebase login
firebase use $PROJECT_ID

# Configure authentication (manual via console)
echo "Go to: https://console.firebase.google.com/project/$PROJECT_ID"
echo "Enable Authentication > Email/Password"
echo "Add chatterfix.com to authorized domains"
```

## 🔍 Verification Commands

```bash
# Check service status
gcloud run services describe chatterfix-cmms --region=us-central1

# Check domain mapping
gcloud run domain-mappings describe chatterfix.com --region=us-central1

# Test health endpoint
curl https://chatterfix-cmms-[hash]-uc.a.run.app/health

# View logs
gcloud run logs read --service=chatterfix-cmms --region=us-central1
```

## 🛠️ Troubleshooting

### Service Won't Start
```bash
# Check logs
gcloud run logs read --service=chatterfix-cmms --region=us-central1 --limit=50

# Check environment variables
gcloud run services describe chatterfix-cmms --region=us-central1 \
    --format="value(spec.template.spec.template.spec.containers[0].env[].name,spec.template.spec.template.spec.containers[0].env[].value)"
```

### Domain Mapping Issues
```bash
# Check domain verification
gcloud domains list-user-verified

# Check mapping status
gcloud run domain-mappings describe chatterfix.com --region=us-central1 \
    --format="table(status.conditions[].type,status.conditions[].status,status.conditions[].reason)"
```

### SSL Certificate Issues
```bash
# Check certificate status
gcloud run domain-mappings describe chatterfix.com --region=us-central1 \
    --format="value(status.certificate.status)"
```

### Build Issues
```bash
# Check build history
gcloud builds list --limit=5

# View build logs
gcloud builds log [BUILD_ID]
```

## 📊 Monitoring & Maintenance

### View Live Logs
```bash
gcloud run logs tail --service=chatterfix-cmms --region=us-central1
```

### Update Deployment
```bash
# Build new image
docker build -t gcr.io/$PROJECT_ID/chatterfix-cmms:latest .
docker push gcr.io/$PROJECT_ID/chatterfix-cmms:latest

# Deploy update
gcloud run deploy chatterfix-cmms \
    --image=gcr.io/$PROJECT_ID/chatterfix-cmms:latest \
    --region=us-central1
```

### Scale Service
```bash
gcloud run services update chatterfix-cmms \
    --region=us-central1 \
    --max-instances=20 \
    --min-instances=2
```

## 🎯 Expected Results

After successful deployment:

- ✅ **Cloud Run Service**: Running at generated URL
- ✅ **Custom Domain**: `https://chatterfix.com` 
- ✅ **SSL Certificate**: Auto-provisioned by Google
- ✅ **Firestore**: Database ready for production
- ✅ **Firebase Auth**: Authentication system active
- ✅ **Health Check**: `/health` endpoint responding
- ✅ **Auto-scaling**: Based on traffic demand

## 📞 Support

If you encounter issues:

1. **Check the logs**: `gcloud run logs read --service=chatterfix-cmms`
2. **Verify DNS**: Use online DNS checkers
3. **Test endpoints**: `curl https://[service-url]/health`
4. **Review IAM**: Ensure service account has correct permissions

---

**🎉 Success**: ChatterFix CMMS deployed to `https://chatterfix.com` with enterprise features!
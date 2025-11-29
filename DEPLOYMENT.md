# ChatterFix Deployment Guide - GUARANTEED CONSISTENT DEPLOYMENT

## 🎯 IMPORTANT: Your Production Service

Your app **ALWAYS** deploys to the same place:
- **Service**: `chatterfix-cmms` 
- **Project**: `fredfix`
- **Region**: `us-central1`
- **Domains**: https://chatterfix.com, https://www.chatterfix.com

## 🚀 Foolproof Deploy (ONE COMMAND)

```bash
./deploy-production.sh
```

**This script guarantees you'll never deploy to the wrong place because it:**
- ✅ Verifies correct GCP project (`fredfix`)
- ✅ Confirms target service exists (`chatterfix-cmms`)  
- ✅ Only updates the existing service (never creates new ones)
- ✅ Tests the deployment after completion
- ✅ Shows you exactly where your app is live

## 📋 Prerequisites

- Google Cloud Account with billing enabled
- Google Cloud CLI (`gcloud`) installed
- Firebase CLI (`firebase`) installed (script will install if needed)
- Docker installed (optional, for local testing)

## 🔧 Detailed Setup

### 1. Google Cloud Project Setup

```bash
# Create a new project (optional)
gcloud projects create chatterfix-cmms --set-as-default

# Or use existing project
gcloud config set project YOUR_PROJECT_ID
```

### 2. Enable Required APIs

The deployment script automatically enables these APIs:
- Cloud Build API
- Cloud Run API
- Container Registry API
- Firestore API
- Firebase API
- IAM API

### 3. Firebase Configuration

**Automatic Setup:**
```bash
./setup-firebase.sh
```

**Manual Setup:**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Enable Authentication → Sign-in method → Email/Password
4. Go to Project Settings → General → Your apps
5. Create a Web app
6. Copy the Firebase config values to `.env.production`

### 4. Deploy to Cloud Run

**Automatic Deployment:**
```bash
./deploy-gcp.sh
```

**Manual Deployment:**
```bash
# Build and deploy
gcloud builds submit --config=deployment/cloudbuild-cloudrun.yaml .

# Or deploy directly
gcloud run deploy chatterfix-cmms \
  --source . \
  --region=us-central1 \
  --allow-unauthenticated \
  --set-env-vars="USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project)"
```

## 🏗️ Architecture

**Local Development:**
- Database: SQLite
- Auth: Local user management
- Environment: `USE_FIRESTORE=false`

**Production (GCP):**
- Database: Firestore
- Auth: Firebase Authentication
- Environment: `USE_FIRESTORE=true`
- Platform: Cloud Run

## 🔐 Environment Variables

**Production Environment Variables:**
```bash
USE_FIRESTORE=true
GOOGLE_CLOUD_PROJECT=your-project-id
LOG_LEVEL=info
PORT=8080

# Firebase Config (set these in .env.production)
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
```

## 🛠️ Database Adapter

ChatterFix automatically switches between databases based on the environment:

```python
# Uses SQLite locally
USE_FIRESTORE=false

# Uses Firestore in production
USE_FIRESTORE=true
```

The database adapter (`app/core/db_adapter.py`) provides a consistent API for both backends.

## 🔥 Firebase Features

**Implemented:**
- ✅ Firebase Authentication
- ✅ Firestore database
- ✅ User management
- ✅ Session handling
- ✅ Profile management

**Authentication Flow:**
1. Frontend authenticates with Firebase
2. Backend verifies Firebase ID tokens
3. User data stored/retrieved from Firestore
4. Seamless integration with existing CMMS features

## 📊 Monitoring

**Health Endpoints:**
- `/health` - Basic health check
- `/readiness` - Dependency health checks
- `/liveness` - Application alive check

**Cloud Monitoring:**
- Logs: Cloud Logging
- Metrics: Cloud Monitoring
- Errors: Error Reporting
- Traces: Cloud Trace

## 🚀 Deployment Options

### Option 1: Cloud Run (Recommended)
- **Pros**: Serverless, auto-scaling, cost-effective
- **Use**: `./deploy-gcp.sh` or `cloudbuild-cloudrun.yaml`

### Option 2: App Engine
- **Pros**: Fully managed, integrated services
- **Use**: `gcloud app deploy deployment/app.yaml`

### Option 3: GKE
- **Pros**: Full Kubernetes control, complex workloads
- **Use**: Deploy with `deployment/cloudrun.yaml` as base

## 🔍 Troubleshooting

**Common Issues:**

1. **Firebase not initialized:**
   ```bash
   # Check service account permissions
   gcloud iam service-accounts get-iam-policy chatterfix-service-account@PROJECT_ID.iam.gserviceaccount.com
   ```

2. **Firestore permissions:**
   ```bash
   # Grant Firestore access
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:chatterfix-service-account@PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/datastore.user"
   ```

3. **Build failures:**
   ```bash
   # Check build logs
   gcloud builds list --limit=5
   gcloud builds log BUILD_ID
   ```

**Debug Commands:**
```bash
# Check service status
gcloud run services describe chatterfix-cmms --region=us-central1

# View logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=chatterfix-cmms" --limit=50

# Test health endpoint
curl https://YOUR_SERVICE_URL/health
```

## 🎯 Next Steps

After deployment:

1. **Configure Firebase:**
   - Set up authentication providers
   - Configure security rules
   - Test user registration/login

2. **Customize Application:**
   - Update branding and UI
   - Configure CMMS workflows
   - Set up user roles

3. **Monitor & Scale:**
   - Set up alerting
   - Monitor performance
   - Configure auto-scaling

## 📞 Support

For deployment issues:
1. Check the troubleshooting section
2. Review Cloud Build logs
3. Test health endpoints
4. Submit issues to the project repository

---

**🎉 Congratulations!** Your ChatterFix CMMS is now deployed to Google Cloud Platform with enterprise-grade Firebase Authentication and Firestore database!
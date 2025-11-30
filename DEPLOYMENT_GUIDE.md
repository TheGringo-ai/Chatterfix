# ChatterFix CMMS - Firebase & GCP Deployment Guide

## 🔥 Firebase Configuration Complete

ChatterFix is now configured to use Firebase Auth and Firestore exclusively, with no SQLite dependencies for production deployment.

## 📋 Prerequisites

- Google Cloud Project: `fredfix`
- Firebase project linked to GCP
- Cloud Run, Firestore, and Firebase Auth enabled

## 🚀 Quick Deployment Options

### Option 1: Automated Cloud Build (Recommended)
```bash
# Deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml .
```

### Option 2: Direct Cloud Run Deployment
```bash
# Deploy from source
gcloud run deploy chatterfix \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "ENVIRONMENT=production,USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=fredfix"
```

### Option 3: Docker Build & Deploy
```bash
# Build and push Docker image
docker build -f Dockerfile.gcp -t gcr.io/fredfix/chatterfix-cmms .
docker push gcr.io/fredfix/chatterfix-cmms

# Deploy to Cloud Run
gcloud run deploy chatterfix \
  --image gcr.io/fredfix/chatterfix-cmms \
  --region us-central1 \
  --allow-unauthenticated
```

## 🔧 Environment Configuration

### Production (GCP) - Automatically Configured
```bash
ENVIRONMENT=production
USE_FIRESTORE=true
GOOGLE_CLOUD_PROJECT=fredfix
CMMS_PORT=8080
```

### Local Development Setup
```bash
# 1. Download Firebase service account key
# 2. Save as firebase-credentials.json
# 3. Set environment variables:
USE_FIRESTORE=true
GOOGLE_CLOUD_PROJECT=fredfix
GOOGLE_APPLICATION_CREDENTIALS=./firebase-credentials.json
```

## 🗄️ Database Architecture

### Firestore Collections
- **users** - Authentication and user profiles
- **work_orders** - Maintenance tasks and work orders
- **assets** - Equipment and asset management
- **inventory** - Parts and inventory management
- **ai_interactions** - AI chat history
- **notifications** - User alerts and notifications

### No SQLite Dependencies
- SQLite removed from production builds
- All data operations use Firestore
- Fallback to SQLite only for local development without Firebase

## 🧪 Testing & Validation

### Check Firebase Configuration
```bash
python3 check_firebase.py
```

### Initialize Firestore Collections
```bash
python3 init_firestore.py
```

### Production Setup Script
```bash
python3 setup_production.py
```

## 🔐 Security & Authentication

### Firebase Auth Integration
- Email/password authentication
- JWT token verification
- User role management
- Session handling

### GCP Security
- Application Default Credentials
- IAM service accounts
- Firestore security rules
- HTTPS enforced

## 📊 Monitoring & Health Checks

### Health Endpoints
- `/health` - Basic health check
- `/health/db` - Database connectivity check
- `/health/firebase` - Firebase service status

### Cloud Monitoring
- Cloud Run metrics
- Firestore usage
- Firebase Auth analytics

## 🛠️ Troubleshooting

### Firebase Connection Issues
```bash
# Check credentials
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test Firebase connection
python3 -c "from app.services.firebase_auth import firebase_auth_service; print(firebase_auth_service.is_available)"
```

### Local Development
```bash
# Run locally with Firebase
python3 main.py

# Run with SQLite fallback (development only)
DISABLE_FIREBASE=true python3 main.py
```

## 🔄 Data Migration

### From SQLite to Firestore
```bash
# Migration script (if needed)
python3 migrate_sqlite_to_firestore.py
```

## 📈 Scaling & Performance

### Cloud Run Configuration
- Memory: 2Gi
- CPU: 2 vCPU
- Max instances: 10
- Request timeout: 300s

### Firestore Optimization
- Compound indexes for queries
- Connection pooling
- Batch operations for bulk data

## 🎯 Production Checklist

- ✅ Firebase project configured
- ✅ Firestore collections initialized
- ✅ Service account permissions set
- ✅ Environment variables configured
- ✅ Health checks enabled
- ✅ HTTPS enforced
- ✅ SQLite dependencies removed
- ✅ Authentication flow tested

## 🚦 Next Steps

1. **Deploy**: Use any of the deployment options above
2. **Test**: Verify all functionality works
3. **Monitor**: Set up Cloud Monitoring alerts
4. **Scale**: Adjust Cloud Run settings as needed
5. **Backup**: Configure Firestore backups

Your ChatterFix CMMS is now ready for production deployment on GCP with Firebase! 🎉
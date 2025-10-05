# ChatterFix CMMS - Cloud Run CPU Quota Increase Request

## 📊 Current Status
- **Billing**: ✅ ENABLED (Account: 015848-2DBBC4-1F3F59)
- **Project**: fredfix
- **Current CPU Quota**: ~6-7 CPUs (us-central1)
- **Services Deployed**: 6/7 (missing AI Brain due to quota)
- **Needed**: Additional 10 CPUs for full deployment + headroom

## 🎯 Request Details

### Quota Increase Request
**Resource**: Cloud Run CPU (per region)
**Current Limit**: ~6-7 CPUs 
**Requested Limit**: 20 CPUs
**Region**: us-central1
**Justification**: Production CMMS deployment with AI services

### Business Justification
```
ChatterFix CMMS is a production-ready maintenance management system requiring:

1. Backend Services (Database, Work Orders, Assets, Parts): 3 CPUs
2. AI Services (AI Brain, Document Intelligence): 2 CPUs  
3. Frontend Gateway: 1 CPU
4. Development/Testing headroom: 4 CPUs
5. Auto-scaling capacity: 10 CPUs

Total Required: 20 CPUs

This enables full deployment of our consolidated microservices architecture
with AI-powered features including voice-to-work-order, predictive maintenance,
and computer vision analysis.
```

## 🔗 Request Instructions

### Method 1: Google Cloud Console (Recommended)
1. Go to: https://console.cloud.google.com/iam-admin/quotas
2. Filter by:
   - **Service**: Cloud Run API
   - **Location**: us-central1
   - **Metric**: CPU allocation (per region)
3. Select the CPU quota row
4. Click "EDIT QUOTAS"
5. Request increase to: **20 CPUs**
6. Provide business justification (copy from above)
7. Submit request

### Method 2: gcloud command
```bash
# Check current quotas
gcloud compute project-info describe --project=fredfix

# Request increase (use Console for better success rate)
# Note: Cloud Run quotas may need Console submission
```

## 📋 Expected Timeline
- **Automatic approval**: Instant (if within standard limits)
- **Manual review**: 1-3 business days
- **Complex requests**: 3-7 business days

## 🚀 Post-Approval Actions
Once quota is approved, run:
```bash
./deploy-consolidated-services.sh
```

This will deploy the 3 unified services:
1. **chatterfix-backend-unified** (Database + Work Orders + Assets + Parts)
2. **chatterfix-ai-unified** (AI Brain + Document Intelligence)
3. **chatterfix-cmms** (Frontend Gateway)

## 💰 Cost Impact
- **Current**: ~$30-50/month (6 services)
- **After consolidation**: ~$20-30/month (3 services)
- **Quota increase**: No additional cost (pay per usage)

## ✅ Benefits
- Full AI functionality deployment
- Voice-to-work-order conversion
- Predictive maintenance analytics
- Computer vision asset inspection
- 57% CPU reduction through consolidation
- PostgreSQL database preserved
- All PM scheduling enhancements maintained

---

**Status**: Billing ✅ | Quota Request ⏳ | Deployment Ready 🚀
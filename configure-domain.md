# ChatterFix Domain Configuration

## Step 1: Deploy to Cloud Run

Use the Google Cloud Console to deploy ChatterFix:

### Cloud Run Deployment
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select project: `chatterfix-cmms` (or create it)
3. Go to **Cloud Run** > **Create Service**
4. Choose **Deploy one revision from existing container image**
5. Use container image: `gcr.io/chatterfix-cmms/chatterfix-cmms:latest`

**OR build from source:**
1. Go to **Cloud Build** > **Triggers**
2. Create a trigger linked to your GitHub repo
3. Use the `cloudbuild-cloudrun.yaml` configuration

### Service Configuration
- **Service name**: `chatterfix-cmms`
- **Region**: `us-central1`
- **CPU allocation**: 1 CPU
- **Memory**: 2 GiB
- **Max instances**: 10
- **Min instances**: 1
- **Ingress**: Allow all traffic
- **Authentication**: Allow unauthenticated invocations

### Environment Variables
```
USE_FIRESTORE=true
GOOGLE_CLOUD_PROJECT=chatterfix-cmms
LOG_LEVEL=info
```

## Step 2: Map Custom Domain

### Through Google Cloud Console
1. Go to **Cloud Run** > **Manage Custom Domains**
2. Click **Add Mapping**
3. Select service: `chatterfix-cmms`
4. Enter domain: `chatterfix.com`
5. Click **Continue**

### DNS Records Required
The console will show you DNS records to add:

**CNAME Record:**
```
Name: @ (or chatterfix.com)
Type: CNAME
Value: ghs.googlehosted.com
TTL: 3600
```

**Verification TXT Record:**
```
Name: _acme-challenge.chatterfix.com
Type: TXT
Value: [Google will provide this value]
TTL: 3600
```

## Step 3: Configure DNS

### If using Cloudflare:
1. Go to **DNS** tab in Cloudflare dashboard
2. Add **CNAME** record: `@` → `ghs.googlehosted.com`
3. Add **TXT** record: `_acme-challenge` → `[value from Google]`
4. Set proxy status to **DNS only** (gray cloud)

### If using GoDaddy:
1. Go to **DNS Management**
2. Add **CNAME** record: `@` → `ghs.googlehosted.com`
3. Add **TXT** record: `_acme-challenge` → `[value from Google]`

### If using Namecheap:
1. Go to **Advanced DNS**
2. Add **CNAME** record: `@` → `ghs.googlehosted.com`  
3. Add **TXT** record: `_acme-challenge` → `[value from Google]`

## Step 4: Enable Firebase

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project: `chatterfix-cmms`
3. Go to **Authentication** > **Sign-in method**
4. Enable **Email/Password**
5. Go to **Project Settings** > **Authorized domains**
6. Add `chatterfix.com`

## Step 5: Firestore Setup

1. Go to **Firestore Database**
2. Create database in **Native mode**
3. Choose location: `us-central1`
4. Set security rules to allow authenticated users:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

## Step 6: Test Deployment

Once DNS propagates (15-60 minutes):

1. Visit: `https://chatterfix.com/health`
2. Should return: `{"status": "healthy", "service": "ChatterFix CMMS"}`
3. Visit: `https://chatterfix.com`
4. Should show ChatterFix login page

## Monitoring

- **Service URL**: Check Cloud Run console for the service URL
- **Domain Status**: Monitor domain mapping status in Cloud Run
- **SSL Certificate**: Auto-provisioned by Google Cloud
- **Logs**: Available in Cloud Run > chatterfix-cmms > Logs

## Quick Commands (if gcloud is working)

```bash
# Check service status
gcloud run services list --region=us-central1

# Check domain mapping
gcloud run domain-mappings list --region=us-central1

# View logs
gcloud run logs read --service=chatterfix-cmms --region=us-central1
```

---

**🎉 Result**: ChatterFix CMMS will be available at `https://chatterfix.com` with Firebase Authentication and Firestore database!
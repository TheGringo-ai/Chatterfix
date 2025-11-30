# GitHub Secrets Setup for ChatterFix Deployment

## 🔑 Required Secrets for Deployment

To deploy ChatterFix to GCP, you need to configure these GitHub repository secrets:

### 1. **GCP_SA_KEY** (Required for Cloud Run deployment)

#### Step-by-step setup:

1. **Go to Google Cloud Console**:
   ```
   https://console.cloud.google.com/iam-admin/serviceaccounts?project=fredfix
   ```

2. **Create or use existing service account**:
   - Click "Create Service Account"
   - Name: `chatterfix-deploy`
   - Description: `Service account for ChatterFix deployment`

3. **Grant required roles**:
   - Cloud Run Admin
   - Cloud Build Service Account
   - Storage Admin
   - Artifact Registry Administrator
   - Service Account User

4. **Create JSON key**:
   - Click on the service account
   - Go to "Keys" tab
   - "Add Key" → "Create new key" → JSON
   - Download the JSON file

5. **Add to GitHub Secrets**:
   - Go to your GitHub repository
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `GCP_SA_KEY`
   - Value: Copy and paste the **entire contents** of the downloaded JSON file

### 2. **FIREBASE_SERVICE_ACCOUNT_KEY** (Alternative/Fallback)

If you already have Firebase credentials:
- Use the same JSON key from Firebase Console
- Project Settings → Service accounts → Generate new private key
- Add as GitHub secret with this name

### 3. **API Keys** (Optional but recommended)

```bash
# AI API Keys
GEMINI_API_KEY=AIzaSyDxQ45QqBacpEIISrS52E1QjeSy1nNuy48
OPENAI_API_KEY=sk-your-openai-key-here  
GROK_API_KEY=grok-your-key-here
```

## 🧪 Test Your Setup

After adding the secrets, you can test the deployment by:

1. **Manual deployment trigger**:
   - Go to Actions tab in your repository
   - Click "Deploy to Production" 
   - "Run workflow" → "Run workflow"

2. **Check deployment status**:
   - Monitor the workflow run
   - Check Cloud Run service at: https://console.cloud.google.com/run?project=fredfix

## 🛠️ Troubleshooting

### "Credentials_json" Error
- Ensure the entire JSON file content is copied to GitHub secret
- Check that the service account has the required roles
- Verify the project ID is correct (`fredfix`)

### "Permission Denied" Error  
- Add Cloud Run Admin role to service account
- Add Cloud Build Service Account role
- Ensure project billing is enabled

### "Service Not Found" Error
- The service will be created automatically on first deployment
- Ensure region is set to `us-central1`

## 🚀 Manual GCP Deployment (Alternative)

If GitHub Actions fail, you can deploy manually:

```bash
# Set up gcloud CLI locally
gcloud auth login
gcloud config set project fredfix

# Deploy directly
gcloud run deploy chatterfix \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2
```

## 📋 Security Best Practices

✅ **Do**:
- Use service accounts with minimal required permissions
- Regularly rotate service account keys
- Monitor Cloud Audit logs for unusual activity

❌ **Don't**:
- Share service account JSON files
- Commit service account keys to repository  
- Use overly broad permissions (like Project Editor)

Your ChatterFix deployment should work perfectly once the `GCP_SA_KEY` secret is configured! 🎉
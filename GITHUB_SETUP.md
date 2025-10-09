# 🚀 GitHub Actions Setup for ChatterFix CMMS

## Quick Setup (2 minutes)

### 1. Add GitHub Secrets

Go to your GitHub repository settings and add these secrets:

**Repository → Settings → Secrets and variables → Actions → New repository secret**

#### Required Secret:
- **Name:** `GCP_SERVICE_ACCOUNT_KEY`
- **Value:** The service account key JSON you created earlier (stored in GitHub Secrets only - never commit to repository)

#### Optional Secrets (for notifications):
- **Name:** `SLACK_WEBHOOK` (optional)
- **Value:** Your Slack webhook URL for deployment notifications

### 2. Test Deployment

Once the secret is added, you can trigger a deployment:

1. **Automatic:** Push to `main` or `main-clean` branch
2. **Manual:** Go to Actions → "🚀 Deploy ChatterFix CMMS to GCP" → "Run workflow"

### 3. Available Workflows

#### 🚀 Full Deployment
- **File:** `.github/workflows/deploy-to-gcp.yml`
- **Trigger:** Push to main/main-clean or manual
- **Action:** Complete clean deployment (3-5 minutes)

#### ⚡ Quick Update
- **File:** `.github/workflows/quick-update.yml`
- **Trigger:** Changes to `core/cmms/app.py` or templates
- **Action:** Fast app-only update (30 seconds)

## Current Status

✅ **Clean VM Deployed:** http://35.237.149.25  
✅ **GitHub Actions Ready:** Workflows configured  
✅ **Service Account:** github-actions-deploy@fredfix.iam.gserviceaccount.com  
✅ **Ollama Preserved:** Available for deployment assistance  

## Instant Deployment Commands

```bash
# Test current deployment
curl http://35.237.149.25:8000/health

# Trigger manual deployment (after GitHub secret setup)
# Go to GitHub Actions and click "Run workflow"

# Check logs
# GitHub Actions → Latest workflow run
```

## Cost Estimate

**Current Setup:**
- GCP e2-standard-4: ~$85/month (4 vCPUs, 16GB RAM)
- **Running now:** Your VM is active
- **Stopped cost:** $0 (when stopped)

## Security Notes

🔒 **Service Account Permissions:**
- compute.admin: Full compute instance control
- compute.instanceAdmin: Instance management
- Scoped to your project only

🔑 **Key Management:**
- Store service account key in GitHub Secrets only
- Delete local `github-actions-key.json` after setup
- Rotate keys every 90 days for security

## Next Steps

1. ✅ Add GitHub secret (copy JSON above)
2. ✅ Push any change to trigger first deployment  
3. ✅ Monitor GitHub Actions for success
4. ✅ Access your app at http://35.237.149.25

## Troubleshooting

**If deployment fails:**
1. Check GitHub Actions logs
2. Verify service account key is correct
3. Ensure GCP project permissions are set
4. VM should be running in us-east1-b zone

**Manual rollback:**
```bash
gcloud compute instances reset chatterfix-cmms-production --zone=us-east1-b
```
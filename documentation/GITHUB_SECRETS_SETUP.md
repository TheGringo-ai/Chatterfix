# GitHub Secrets Configuration for Fix It Fred Git Integration

## 🔐 Secure Deployment with GitHub Secrets & Git Integration

The GitHub token stays securely in GitHub Secrets where it belongs! Fix It Fred now has comprehensive Git integration with real-time monitoring, AI-powered commits, and automated deployment workflows.

## 📋 Required GitHub Secrets

Go to your repository: **Settings → Secrets and variables → Actions → New repository secret**

### 1. `GCP_SA_KEY` (Required for VM Deployment)
**Purpose**: Allows GitHub Actions to deploy to your GCP VM and manage Git integration services

**How to get it**:
```bash
# Create service account (if not already done)
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Deployer"

# Grant comprehensive permissions for Git integration
gcloud projects add-iam-policy-binding fredfix \
  --member="serviceAccount:github-actions@fredfix.iam.gserviceaccount.com" \
  --role="roles/compute.instanceAdmin.v1"

gcloud projects add-iam-policy-binding fredfix \
  --member="serviceAccount:github-actions@fredfix.iam.gserviceaccount.com" \
  --role="roles/compute.osLogin"

# Create key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@fredfix.iam.gserviceaccount.com

# Copy the contents of github-actions-key.json
cat github-actions-key.json
```

**Add to GitHub Secrets**:
- Name: `GCP_SA_KEY`
- Value: [Entire JSON contents]

### 2. `DEPLOYMENT_API_KEY` (Optional)
**Purpose**: Secure the deployment API endpoints

```bash
# Generate a secure API key
openssl rand -hex 32
```

**Add to GitHub Secrets**:
- Name: `DEPLOYMENT_API_KEY`
- Value: [Generated key]

Also add to VM:
```bash
echo "DEPLOYMENT_API_KEY=your-key-here" >> ~/chatterfix-docker/app/.env
```

### 3. `SLACK_WEBHOOK` (Optional)
**Purpose**: Get notifications when deployments complete

**Add to GitHub Secrets**:
- Name: `SLACK_WEBHOOK`
- Value: `https://hooks.slack.com/services/YOUR/WEBHOOK/URL`

## 🚀 How Fix It Fred Triggers Deployments

### Method 1: Git Push (Recommended)
When Fred commits and pushes changes, GitHub Actions automatically detects the push and deploys.

```python
# Fred does this:
# 1. Commits changes
# 2. Pushes to GitHub
# 3. GitHub Actions sees the push
# 4. Workflow runs automatically
# ✅ No GitHub token needed on VM!
```

### Method 2: Manual Workflow Trigger
You can manually trigger deployments from GitHub Actions UI:
1. Go to **Actions** tab
2. Select "🤖 Fix It Fred Command Deployment"
3. Click "Run workflow"
4. Enter command: "deploy to production"

## 📝 VM Configuration (No Tokens Required!)

Your VM only needs these environment variables:

```bash
# ~/chatterfix-docker/app/.env

# Repository path (for git operations)
REPO_PATH=/home/yoyofred_gringosgambit_com/chatterfix-docker/app

# Your GitHub repository
GITHUB_REPO=fredfix/ai-tools

# API security (optional)
DEPLOYMENT_API_KEY=your-secure-key-here

# Ollama configuration (already set)
OLLAMA_HOST=http://localhost:11434
```

**Notice**: No `GITHUB_TOKEN` required! 🎉

## 🎯 Git Integration Workflow: How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Fix It Fred on VM                       │
├─────────────────────────────────────────────────────────────┤
│  🤖 AI Service (Port 9000)                                 │
│  🔍 Git Integration Service (Port 9002)                    │
│  📊 Real-time File Monitor                                 │
└────────┬────────────────────────────────────────────────────┘
         │
         │ 1. File changes detected
         │ 2. AI analysis performed
         │ 3. Intelligent commit created
         │ 4. Push to GitHub
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions                          │
├─────────────────────────────────────────────────────────────┤
│  Workflow 1: deploy-fix-it-fred-git-integration.yml        │
│  - Deploys Git Integration Service                         │
│  - Configures systemd service                             │
│  - Sets up monitoring                                      │
│                                                            │
│  Workflow 2: deploy.yml                                   │
│  - Main application deployment                             │
│  - Includes Git integration health checks                 │
│                                                            │
│  Uses Secrets: GCP_SA_KEY                                │
└────────┬────────────────────────────────────────────────────┘
         │
         │ 3. Deploy to GCP VM
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Production VM                           │
├─────────────────────────────────────────────────────────────┤
│  ✅ ChatterFix CMMS Updated                               │
│  ✅ Git Integration Active                                │
│  ✅ Real-time Monitoring                                 │
│  ✅ AI-Powered Commits                                   │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Testing the Setup

### Test 1: Git Operations (No Token)
```bash
curl -X POST http://35.237.149.25:8080/api/github/status
# ✅ Should work without GITHUB_TOKEN
```

### Test 2: Commit Changes
```bash
curl -X POST http://35.237.149.25:8080/api/github/commit \
  -H "Content-Type: application/json" \
  -d '{"message": "Test commit from Fred"}'
# ✅ Works with just git config
```

### Test 3: Trigger Deployment (via push)
```bash
curl -X POST http://35.237.149.25:8080/api/fix-it-fred/deploy \
  -H "Content-Type: application/json" \
  -d '{"command": "ship it"}'
# ✅ Commits, pushes → GitHub Actions deploys automatically
```

## 🎨 Supported Commands

All these work **without** requiring a GitHub token on the VM:

| Command | What Fred Does |
|---------|---------------|
| `"check git status"` | Shows changes | ✅ No token |
| `"commit changes"` | Commits with AI message | ✅ No token |
| `"push to github"` | Pushes committed changes | ✅ No token |
| `"deploy to production"` | Commit + Push → GitHub Actions deploys | ✅ No token |
| `"ship it"` | Full deployment flow | ✅ No token |

## ⚙️ GitHub Actions Workflows

### Workflow 1: deploy-to-gcp.yml
**Trigger**: Push to `main` or `main-clean` branches

**What it does**:
1. Checks out code
2. Authenticates with GCP using `GCP_SERVICE_ACCOUNT_KEY` secret
3. Deploys to VM
4. Runs health checks
5. Posts to Slack (if configured)

### Workflow 2: deploy-on-command.yml (New!)
**Trigger**:
- Repository dispatch events
- Manual workflow trigger with natural language command

**What it does**:
1. Parses natural language command
2. Determines action (deploy, create PR, status check)
3. Executes appropriate workflow
4. Reports status back

## 🔄 Auto-Deployment Flow

```bash
# On your VM, Fred can do this:
curl -X POST http://35.237.149.25:8080/api/fix-it-fred/deploy \
  -H "Content-Type: application/json" \
  -d '{
    "command": "deploy new features to production"
  }'

# Fred will:
# 1. ✅ Check git status (no token needed)
# 2. ✅ Generate AI commit message (uses Ollama)
# 3. ✅ Commit changes (no token needed)
# 4. ✅ Push to GitHub (uses git credentials)
# 5. ✅ GitHub Actions sees push
# 6. ✅ Workflow runs with GCP_SERVICE_ACCOUNT_KEY
# 7. ✅ Deploys to VM
# 8. ✅ Runs health checks
# 9. ✅ Notifies Slack (optional)
```

## 🚨 Troubleshooting

### Issue: "Push failed - authentication required"
**Solution**: Configure git credentials on VM
```bash
git config --global credential.helper store
git push  # Enter credentials once, then stored
```

### Issue: "GitHub Actions workflow not triggering"
**Solution**: Check workflow file is on the branch you're pushing to
```bash
git checkout main-clean
ls .github/workflows/
```

### Issue: "GCP deployment fails"
**Solution**: Verify `GCP_SERVICE_ACCOUNT_KEY` secret is correct
1. Go to GitHub repository → Settings → Secrets
2. Ensure key is valid JSON
3. Check service account has `compute.instanceAdmin.v1` role

## ✅ Security Benefits

1. **No GitHub Token on VM**: Token never leaves GitHub
2. **Secret Management**: All secrets in GitHub Secrets
3. **Least Privilege**: VM only needs git push permission
4. **Audit Trail**: All deployments logged in GitHub Actions
5. **Rollback**: Easy to revert via git
6. **API Key Optional**: Can work without API key for read operations

## 🎉 Summary

- ✅ GitHub token stays in GitHub Secrets (secure!)
- ✅ VM only needs git credentials (low risk)
- ✅ Fred triggers deployments via git push
- ✅ GitHub Actions handles actual deployment
- ✅ All secrets managed centrally
- ✅ Natural language interface works perfectly

**Just ask Fred: "ship it" and let GitHub Actions handle the rest!** 🚀

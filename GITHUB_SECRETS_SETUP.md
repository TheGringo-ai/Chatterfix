# 🔐 GitHub Secrets Setup Guide

## Required Secrets for Deployment

Your ChatterFix deployment needs these GitHub repository secrets configured:

### 🔥 **Firebase Configuration**
- **`FIREBASE_API_KEY`**: `AIzaSyAaXlvuopHtTZglfghnlc_hBqGr1YzPrBk`
  - Current value from your `.env` file
  - Used for Firebase web app authentication

### 🤖 **AI Service Keys**
- **`GEMINI_API_KEY`**: `AIzaSyDxQ45QqBacpEIISrS52E1QjeSy1nNuy48`
  - Current working key from your `.env` file
- **`OPENAI_API_KEY`**: `sk-your-openai-key-here`
  - ⚠️ **Update needed**: Replace with real OpenAI API key
- **`GROK_API_KEY`**: `grok-your-grok-key-here`
  - ⚠️ **Update needed**: Replace with real Grok API key

### ☁️ **Google Cloud Configuration**
- **`GCP_SA_KEY`**: Google Cloud Service Account JSON
  - Download from Google Cloud Console → IAM & Admin → Service Accounts
  - Should have Cloud Run deployment permissions

## 📋 Setup Instructions

### Step 1: Access GitHub Secrets
1. Go to your GitHub repository: `https://github.com/[username]/ChatterFix`
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **"New repository secret"**

### Step 2: Add Each Secret
For each secret above:
1. **Name**: Enter the exact secret name (e.g., `FIREBASE_API_KEY`)
2. **Secret**: Paste the corresponding value
3. Click **"Add secret"**

### Step 3: Verify Setup
After adding all secrets, the deployment workflow will:
- ✅ Validate all required secrets exist
- ✅ Deploy with secure environment variables
- ❌ Fail early if any secrets are missing

## 🚨 Security Notes

- **Never commit API keys** to your repository
- The `.env` file should remain in `.gitignore`
- GitHub secrets are encrypted and only accessible during workflows
- Update API keys regularly for security

## 🔍 Testing

After setup, push to main branch to trigger deployment:
```bash
git add .
git commit -m "Configure GitHub secrets for deployment"
git push origin main
```

The workflow will validate all secrets before proceeding with deployment.

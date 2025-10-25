#!/bin/bash

# Clear GitHub token environment
unset GITHUB_TOKEN
unset GITHUB_PAT

echo "🔐 Adding GCP_SA_KEY secret to GitHub repository..."

# The service account JSON (from previous output)
GCP_SA_KEY='{
  REDACTED_SERVICE_ACCOUNT'

# Add the secret using GitHub CLI
echo "$GCP_SA_KEY" | gh secret set GCP_SA_KEY --repo TheGringo-ai/Chatterfix

if [ $? -eq 0 ]; then
    echo "✅ Successfully added GCP_SA_KEY secret to GitHub repository!"
    echo ""
    echo "🚀 Now you can test your GitHub Actions workflows:"
    echo "   Go to: https://github.com/TheGringo-ai/Chatterfix/actions"
    echo "   Run: '🤖 Deploy Fix It Fred Git Integration'"
    echo ""
else
    echo "❌ Failed to add secret. Please add manually:"
    echo "   1. Go to: https://github.com/TheGringo-ai/Chatterfix/settings/secrets/actions"
    echo "   2. Click 'New repository secret'"
    echo "   3. Name: GCP_SA_KEY"
    echo "   4. Value: [paste the JSON above]"
fi
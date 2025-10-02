#!/bin/bash

# ChatterFix PR Creation Helper Script
# This script helps create the PR from main-clean to main

set -e

echo "🚀 ChatterFix PR Creation Helper"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "Please run this script from the root of the Chatterfix repository"
    exit 1
fi

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "⚠️  GitHub CLI (gh) is not installed"
    echo ""
    echo "You have two options:"
    echo ""
    echo "1. Install GitHub CLI:"
    echo "   - macOS: brew install gh"
    echo "   - Linux: See https://github.com/cli/cli/blob/trunk/docs/install_linux.md"
    echo "   - Windows: See https://github.com/cli/cli/releases"
    echo ""
    echo "2. Use the web interface:"
    echo "   Visit: https://github.com/TheGringo-ai/Chatterfix/compare/main...main-clean"
    echo ""
    echo "For detailed instructions, see QUICK_PR_GUIDE.md or PULL_REQUEST_GUIDE.md"
    exit 0
fi

# Check if authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo "🔐 You need to authenticate with GitHub first"
    echo ""
    echo "Run: gh auth login"
    echo ""
    read -p "Would you like to authenticate now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh auth login
    else
        echo "Please authenticate later and run this script again"
        exit 0
    fi
fi

echo "✅ GitHub CLI is installed and authenticated"
echo ""

# Show the PR that will be created
echo "📋 PR Details:"
echo "  From: main-clean"
echo "  To:   main"
echo "  Title: 🎉 Complete ChatterFix CMMS - Clean Microservices Implementation"
echo ""

# Ask for confirmation
read -p "Create this pull request? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "🔨 Creating pull request..."
echo ""

# Create the PR using the template
gh pr create \
  --base main \
  --head main-clean \
  --title "🎉 Complete ChatterFix CMMS - Clean Microservices Implementation" \
  --body-file .github/PULL_REQUEST_TEMPLATE.md

echo ""
echo "✅ Pull request created successfully!"
echo ""
echo "To view the PR:"
gh pr view --web

echo ""
echo "🎉 Done!"

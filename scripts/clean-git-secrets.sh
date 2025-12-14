#!/bin/bash
# ============================================
# Git History Secret Cleaner for ChatterFix
# ============================================
#
# This script removes secrets from git history using git-filter-repo
#
# WARNING: This is a DESTRUCTIVE operation that:
# - Rewrites git history
# - Requires force push to remote
# - Will affect all collaborators (they need to re-clone)
#
# BEFORE RUNNING:
# 1. Ensure all team members have pushed their changes
# 2. Backup the repository
# 3. Coordinate with team about the force push
#
# AFTER RUNNING:
# 1. Force push: git push --force --all
# 2. All collaborators must re-clone or reset their local repos
#
# Usage: ./scripts/clean-git-secrets.sh
# ============================================

set -e

echo "=================================================="
echo "🔐 ChatterFix Git History Secret Cleaner"
echo "=================================================="
echo ""
echo "⚠️  WARNING: This will rewrite git history!"
echo "    - All team members will need to re-clone"
echo "    - This operation cannot be undone"
echo ""

read -p "Are you sure you want to continue? (type 'YES' to confirm): " confirm
if [ "$confirm" != "YES" ]; then
    echo "Aborted."
    exit 0
fi

# Check if git-filter-repo is installed
if ! command -v git-filter-repo &> /dev/null; then
    echo ""
    echo "git-filter-repo is not installed."
    echo "Install with: brew install git-filter-repo"
    echo ""
    echo "Alternative: Using BFG Repo Cleaner"
    echo "Download from: https://rtyley.github.io/bfg-repo-cleaner/"
    exit 1
fi

echo ""
echo "Creating backup..."
BACKUP_DIR="../chatterfix-backup-$(date +%Y%m%d_%H%M%S)"
cp -r . "$BACKUP_DIR"
echo "✅ Backup created at: $BACKUP_DIR"

echo ""
echo "Creating patterns file for secrets to remove..."

# Create a patterns file with regex patterns for secrets
cat > /tmp/secret_patterns.txt << 'EOF'
# Google/Firebase API keys
AIza[0-9A-Za-z_-]{35}

# OpenAI API keys
sk-proj-[a-zA-Z0-9_-]{20,}
sk-[a-zA-Z0-9]{20,}

# xAI API keys
xai-[a-zA-Z0-9]{20,}

# Generic API patterns that might be real keys
[a-zA-Z0-9]{32,}(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])
EOF

echo ""
echo "Removing secrets from git history..."
echo "This may take several minutes for large repositories..."
echo ""

# Method 1: Use git-filter-repo to remove the security audit file entirely from history
# (Safest approach - removes the file that contained secrets)
git filter-repo --force --path docs/FIREBASE_SECURITY_AUDIT.md --invert-paths

echo ""
echo "=================================================="
echo "✅ Git history has been cleaned!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "1. Review the changes: git log --oneline -20"
echo "2. Force push to remote: git push --force --all"
echo "3. Notify all team members to re-clone the repository"
echo ""
echo "The security audit document has been removed from history."
echo "You may want to recreate it with redacted content."
echo ""

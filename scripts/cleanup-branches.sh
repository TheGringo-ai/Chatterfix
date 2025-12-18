#!/bin/bash

# ChatterFix Branch Cleanup Script
# Safely removes merged branches to keep repository clean

set -e

echo "🧹 ChatterFix Branch Cleanup"
echo "============================="
echo ""

# Check if on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Please switch to main branch first: git checkout main"
    exit 1
fi

# Update main branch
echo "📥 Updating main branch..."
git fetch origin
git pull origin main

echo ""
echo "🔍 Analyzing branches..."

# List local branches that have been merged into main
MERGED_LOCAL=$(git branch --merged main | grep -v "main" | grep -v "\*" | tr -d ' ' || true)

# List remote branches (excluding main and current development)
REMOTE_BRANCHES=$(git branch -r | grep -v "origin/main" | grep -v "origin/HEAD" | tr -d ' ' | sed 's/origin\///' || true)

echo ""
echo "📋 Branches Analysis:"
echo "  Current: $CURRENT_BRANCH"
echo "  Local merged branches: $(echo $MERGED_LOCAL | wc -w | tr -d ' ') found"
echo "  Remote branches: $(echo $REMOTE_BRANCHES | wc -w | tr -d ' ') found"

echo ""
echo "🗑️  Branches to delete:"

# Show what will be deleted
if [ -n "$MERGED_LOCAL" ]; then
    echo "  Local merged branches:"
    for branch in $MERGED_LOCAL; do
        echo "    - $branch"
    done
fi

# Show remote branches that might be old
echo "  Remote branches to review:"
for branch in $REMOTE_BRANCHES; do
    # Skip if it contains current important keywords
    if [[ "$branch" =~ (main|prod|staging|dev-safe|clean) ]]; then
        echo "    - $branch (keeping - important)"
    else
        echo "    - $branch (candidate for deletion)"
    fi
done

echo ""
read -p "🤔 Do you want to proceed with cleanup? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Starting cleanup..."
    
    # Delete local merged branches
    if [ -n "$MERGED_LOCAL" ]; then
        echo "  Deleting local merged branches..."
        for branch in $MERGED_LOCAL; do
            git branch -d "$branch"
            echo "    ✅ Deleted local: $branch"
        done
    fi
    
    # Delete remote copilot branches (auto-generated)
    echo "  Deleting copilot auto-branches..."
    for branch in $REMOTE_BRANCHES; do
        if [[ "$branch" =~ ^copilot/ ]]; then
            git push origin --delete "$branch" 2>/dev/null || echo "    ⚠️  Could not delete: $branch"
            echo "    ✅ Deleted remote: $branch"
        fi
    done
    
    echo ""
    echo "🎉 Cleanup complete!"
    echo "📊 Final branch count:"
    git branch -a | wc -l | xargs echo "  Total branches:"
    
else
    echo "❌ Cleanup cancelled"
fi

echo ""
echo "💡 To manually review branches:"
echo "  git branch -a                    # List all branches"
echo "  git branch --merged main         # List merged branches"
echo "  git push origin --delete <name>  # Delete remote branch"
#!/bin/bash
# ChatterFix GitHub CLI Aliases
# Run: source scripts/gh-aliases.sh
# Or add to ~/.zshrc: source ~/ChatterFix/scripts/gh-aliases.sh

# Quick deployment status
alias ghstatus='gh run list --limit 5 --json status,conclusion,name,createdAt | jq -r ".[] | \"\\(.name): \\(.conclusion // .status)\""'

# Watch current deployment
alias ghwatch='gh run watch'

# Quick PR creation
alias ghpr='gh pr create --fill'

# View latest deployment logs
alias ghlogs='gh run view --log | tail -100'

# Check production health
alias ghhealth='curl -s https://chatterfix.com/health | jq'

# Quick deploy (push to main triggers deploy)
alias ghdeploy='git push origin main && echo "🚀 Deployment triggered! Run ghwatch to monitor"'

# List open PRs
alias ghprs='gh pr list'

# Review PR
alias ghreview='gh pr review --approve'

# Merge PR with squash
alias ghmerge='gh pr merge --squash --delete-branch'

# Create bug issue
alias ghbug='gh issue create --template bug_report.yml'

# Create feature issue
alias ghfeat='gh issue create --template feature_request.yml'

# View workflow runs
alias ghruns='gh run list --limit 10'

# Trigger workflow manually
alias ghtrigger='gh workflow run'

# Check Dependabot alerts
alias ghsecurity='gh api repos/TheGringo-ai/Chatterfix/dependabot/alerts --jq ".[].security_advisory.summary" | head -10'

echo "✅ ChatterFix GitHub aliases loaded!"
echo ""
echo "Available commands:"
echo "  ghstatus   - Quick workflow status"
echo "  ghwatch    - Watch current deployment"
echo "  ghpr       - Create PR with auto-filled details"
echo "  ghdeploy   - Push to main (triggers deploy)"
echo "  ghhealth   - Check production health"
echo "  ghprs      - List open PRs"
echo "  ghreview   - Approve current PR"
echo "  ghmerge    - Merge with squash"
echo "  ghbug      - Create bug issue"
echo "  ghfeat     - Create feature issue"
echo "  ghruns     - View recent workflow runs"
echo "  ghsecurity - Check security alerts"

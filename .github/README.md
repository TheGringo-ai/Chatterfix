# GitHub Templates

This directory contains templates used by GitHub for various workflows.

## Files

### PULL_REQUEST_TEMPLATE.md

**Purpose:** Default pull request description template

**Usage:** When creating a pull request via the GitHub web interface, this template will automatically populate the PR description field.

**Content:** 
- Summary of the ChatterFix CMMS clean microservices implementation
- Major changes overview
- Security features
- Architecture details
- Testing verification
- Live deployment information

**When it's used:**
- Automatically loaded when creating PRs through GitHub web UI
- Can be referenced with `--body-file .github/PULL_REQUEST_TEMPLATE.md` in GitHub CLI
- Used by the `create-pr.sh` helper script

**Related Documentation:**
- [Quick PR Guide](../QUICK_PR_GUIDE.md)
- [Complete PR Guide](../PULL_REQUEST_GUIDE.md)
- [PR Creation Flowchart](../PR_CREATION_FLOWCHART.md)

## Other Templates

### ISSUE_TEMPLATE/

Contains issue templates for:
- Bug reports
- Feature requests

### workflows/

Contains GitHub Actions workflows for:
- CI/CD pipeline
- Deployment automation
- Testing

---

**Last Updated:** October 2024

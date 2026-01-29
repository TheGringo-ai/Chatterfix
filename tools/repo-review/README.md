# Repo Maintenance Review

A read-only tool that analyzes public GitHub repositories and generates maintenance reports.

## What This Tool Does

- Clones public repos (read-only, no authentication required)
- Detects stack (Python, Node, etc.)
- Runs dependency and security scans
- Uses AI to identify maintenance issues
- Generates a Markdown report

## What This Tool Does NOT Do

- Execute any code from analyzed repos
- Push changes or open PRs
- Modify any files
- Store or transmit repository contents
- Run without human approval

## Usage

```bash
# Analyze a public repo
python review.py https://github.com/owner/repo

# Analyze with verbose output
python review.py https://github.com/owner/repo --verbose

# Output to specific file
python review.py https://github.com/owner/repo --output report.md
```

## Output

Generates a Markdown report with:
- Summary of findings
- Safe suggestions (low-risk fixes)
- Deferred items (breaking changes)
- Risk classification

## Requirements

- Python 3.11+
- git (for cloning)
- Optional: pip-audit, npm audit (for deeper scans)

## Ethics

This tool is designed for:
- Reviewing your own repositories
- Reviewing repos with owner permission
- Learning and demonstration purposes

Do not use this tool to:
- Spam maintainers with unsolicited advice
- Publicly shame projects
- Claim expertise you don't have

## License

Part of ChatterFix. See main LICENSE file.

# ChatterFix Deployment Workflow

Execute the complete deployment workflow with all quality gates from CLAUDE.md.

## Pre-Deployment Checklist

1. **Git Status Check**: Verify no uncommitted changes
2. **Local Testing**: Run tests to ensure all pass
3. **API Testing**: Validate all endpoints return proper JSON
4. **Security Scan**: Check for vulnerabilities
5. **Build Verification**: Ensure Docker builds successfully

## Execution Steps

1. First, check git status for uncommitted changes:
   ```bash
   git status
   ```

2. Run the test suite:
   ```bash
   python -m pytest tests/ -v --tb=short
   ```

3. Build and verify Docker image:
   ```bash
   docker build -t chatterfix:latest .
   ```

4. If all checks pass, deploy to Cloud Run:
   ```bash
   ./scripts/deploy.sh
   ```

5. Post-deployment verification:
   - Test production URL: https://chatterfix.com
   - Verify dark/light mode toggle works
   - Test key API endpoints
   - Check mobile responsiveness

## Quality Gates (NEVER skip these)

- Git status must be clean
- All tests must pass
- Docker build must succeed
- Production verification required after deploy

## Rollback Procedure

If issues are found post-deployment:
```bash
gcloud run services update-traffic chatterfix --to-revisions=PREVIOUS_REVISION=100
```

Remember: NEVER deploy with uncommitted changes. Always test production immediately after deployment.

# Deployment Safety Guide

This guide ensures smooth, safe deployments with zero downtime and easy rollback capabilities.

## 🛡️ Safety Features

### Pre-Deployment Validation

- ✅ Syntax validation (Python, YAML, JSON)
- ✅ Security scanning (secrets detection, vulnerability check)
- ✅ Dependency verification
- ✅ Database migration safety
- ✅ Environment variable validation
- ✅ Docker build test
- ✅ Unit test execution

### Post-Deployment Verification

- ✅ Automated smoke tests
- ✅ Health endpoint checks
- ✅ Response time monitoring
- ✅ Database connectivity verification
- ✅ Critical API endpoint validation

### Automatic Rollback

- 🔄 Triggers on smoke test failures
- 🔄 One-command manual rollback
- 🔄 Rollback history tracking
- 🔄 Fast rollback (< 30 seconds)

## 📋 Pre-Deployment Checklist

Before deploying to production, ensure:

- [ ] All tests pass locally
- [ ] Code has been reviewed
- [ ] No secrets in code
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Pre-deployment checks pass

## 🚀 Deployment Process

### 1. Run Pre-Deployment Checks

```bash
# Run all validation checks
./deployment/pre-deploy-check.sh

# Skip tests (faster)
./deployment/pre-deploy-check.sh --skip-tests

# Force deployment (override failures)
./deployment/pre-deploy-check.sh --force
```

### 2. Deploy to Production

#### Via GitHub Actions (Recommended)

```bash
# Push to main branch
git push origin main

# Or trigger manual deployment
gh workflow run deploy.yml
```

#### Via Command Line

```bash
# Deploy with safety checks
gcloud run deploy chatterfix \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### 3. Verify Deployment

```bash
# Run smoke tests
./deployment/smoke-tests.sh https://chatterfix.com

# Monitor health continuously
python3 deployment/health-monitor.py --url https://chatterfix.com --duration 10
```

## 🔄 Rollback Procedures

### Automatic Rollback

Rollback is triggered automatically when:

- Smoke tests fail after deployment
- Health checks fail 3 consecutive times
- Critical endpoints return errors

### Manual Rollback

```bash
# Rollback to previous version
./deployment/rollback.sh

# Dry run (see what would happen)
./deployment/rollback.sh --dry-run

# Rollback with reason
./deployment/rollback.sh --reason "Bug in payment processing"
```

### Verify Rollback

```bash
# Check current revision
gcloud run services describe chatterfix \
  --region us-central1 \
  --format='value(status.latestReadyRevisionName)'

# Run smoke tests on rolled-back version
./deployment/smoke-tests.sh https://chatterfix.com
```

## 🚨 Emergency Procedures

### Service is Down

1. **Check service status**

   ```bash
   gcloud run services describe chatterfix --region us-central1
   ```

2. **Check logs**

   ```bash
   gcloud logging read "resource.type=cloud_run_revision resource.labels.service_name=chatterfix" --limit=50
   ```

3. **Rollback immediately**
   ```bash
   ./deployment/rollback.sh --reason "Emergency: service down"
   ```

### Slow Response Times

1. **Check current metrics**

   ```bash
   python3 deployment/health-monitor.py --url https://chatterfix.com --duration 5
   ```

2. **Scale up resources**

   ```bash
   gcloud run services update chatterfix \
     --region us-central1 \
     --min-instances=3 \
     --max-instances=20
   ```

3. **Monitor improvement**
   ```bash
   ./deployment/smoke-tests.sh https://chatterfix.com
   ```

### Database Issues

1. **Check database connectivity**

   ```bash
   curl https://chatterfix.com/assets/
   ```

2. **Verify Firestore status**

   ```bash
   gcloud firestore databases list
   ```

3. **Check environment variables**
   ```bash
   gcloud run services describe chatterfix \
     --region us-central1 \
     --format='value(spec.template.spec.containers[0].env)'
   ```

## 📊 Monitoring

### Continuous Health Monitoring

```bash
# Monitor for 30 minutes
python3 deployment/health-monitor.py \
  --url https://chatterfix.com \
  --duration 30

# Custom check interval (every 60 seconds)
python3 deployment/health-monitor.py \
  --url https://chatterfix.com \
  --interval 60

# Custom failure threshold (5 failures before rollback)
python3 deployment/health-monitor.py \
  --url https://chatterfix.com \
  --threshold 5
```

### View Deployment History

```bash
# List recent revisions
gcloud run revisions list \
  --service=chatterfix \
  --region=us-central1 \
  --limit=10

# View rollback history
cat deployment/rollback-history.log
```

## 🔧 Troubleshooting

### Pre-Deployment Checks Failing

**Secret Detection Error**

```bash
# Remove secrets from code
# Use environment variables instead
export OPENAI_API_KEY="your-key-here"
```

**Docker Build Failing**

```bash
# Test build locally
docker build -t chatterfix-test .

# Check build logs
cat /tmp/docker-build.log
```

**Tests Failing**

```bash
# Run tests locally
pytest tests/ -v

# Skip tests if needed (not recommended)
./deployment/pre-deploy-check.sh --skip-tests
```

### Smoke Tests Failing

**Endpoint Not Found (404)**

```bash
# Verify routes are configured
grep -r "@router" app/routers/

# Check main.py includes all routers
cat main.py | grep "include_router"
```

**Timeout Errors**

```bash
# Increase timeout in smoke-tests.sh
# Edit TIMEOUT variable at top of file
```

**Database Connection Errors**

```bash
# Verify Firestore is enabled
gcloud services list | grep firestore

# Check environment variables
gcloud run services describe chatterfix --region us-central1
```

## 🎯 Best Practices

### Before Every Deployment

1. ✅ Run pre-deployment checks locally
2. ✅ Test in staging environment (if available)
3. ✅ Review recent changes
4. ✅ Ensure team is aware of deployment
5. ✅ Have rollback plan ready

### During Deployment

1. ✅ Monitor deployment progress
2. ✅ Watch for errors in logs
3. ✅ Verify smoke tests pass
4. ✅ Check response times
5. ✅ Monitor error rates

### After Deployment

1. ✅ Run comprehensive smoke tests
2. ✅ Monitor for 10-15 minutes
3. ✅ Check user-facing features
4. ✅ Verify database operations
5. ✅ Document any issues

### Deployment Timing

- ✅ Deploy during low-traffic periods
- ✅ Avoid Friday deployments
- ✅ Have team available for monitoring
- ✅ Plan for potential rollback
- ✅ Communicate with stakeholders

## 📞 Support

### Deployment Issues

- Check logs: `gcloud logging read`
- Review rollback history: `cat deployment/rollback-history.log`
- Run diagnostics: `./deployment/smoke-tests.sh`

### Emergency Contact

- Immediate rollback: `./deployment/rollback.sh`
- Check service status: `gcloud run services describe chatterfix`
- View recent deployments: `gcloud run revisions list`

## 🔗 Related Documentation

- [Deployment Guide](DEPLOYMENT.md)
- [GitHub Actions Workflows](.github/workflows/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)

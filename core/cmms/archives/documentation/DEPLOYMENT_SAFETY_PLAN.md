# ChatterFix CMMS Deployment Safety Plan

## 🚨 CRITICAL DEPLOYMENT REGRESSION RESOLVED

**Date:** October 3, 2025
**Issue:** Older version deployed instead of professional landing page
**Status:** ✅ RESOLVED
**Current Live Site:** https://chatterfix.com (Professional Landing Page)

---

## Root Cause Analysis

### What Happened
1. **Multiple Deployment Scripts**: Found 16+ deployment scripts in the repository
2. **Resource Conflicts**: CPU quota exceeded due to too many running services
3. **Version Confusion**: Old app version was serving from Cloud Run instead of new professional landing page
4. **Email Error**: Wrong email address (yoyofred@chatterfix.com) instead of correct (yoyofred@gringosgambit.com)

### What Was Fixed
1. ✅ Cleaned up unused Cloud Run services (freed resources)
2. ✅ Fixed email addresses in app.py
3. ✅ Successfully deployed professional landing page
4. ✅ Verified live site shows correct content

---

## Deployment Safety Protocols

### 1. Pre-Deployment Checklist
- [ ] **Version Control**: Ensure git status is clean
- [ ] **File Verification**: Confirm app.py contains professional landing page (not old dashboard)
- [ ] **Email Check**: Verify all email references use yoyofred@gringosgambit.com
- [ ] **Resource Check**: Ensure sufficient Cloud Run CPU quota
- [ ] **Service Cleanup**: Remove unused services before deployment

### 2. Deployment Process
```bash
# 1. Pre-deployment verification
curl -s https://chatterfix.com | head -5  # Check current version
gcloud run services list --region=us-central1  # Check resources

# 2. Deploy with safe settings
gcloud run deploy chatterfix-cmms \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 2 \
    --min-instances 0

# 3. Post-deployment verification
curl -s https://chatterfix.com | grep "Revolutionary AI-Powered"
curl -s https://chatterfix.com | grep "yoyofred@gringosgambit.com"
```

### 3. Verification Steps
1. **Title Check**: Must show "ChatterFix CMMS - Revolutionary AI-Powered Maintenance Management"
2. **Email Check**: All email references must use yoyofred@gringosgambit.com
3. **Landing Page**: Must show professional design with email signup form
4. **Health Check**: Verify /health endpoint responds correctly

### 4. Rollback Procedure
If deployment fails or regression occurs:
```bash
# 1. Check current revisions
gcloud run revisions list --service=chatterfix-cmms --region=us-central1

# 2. Rollback to previous working revision
gcloud run services update-traffic chatterfix-cmms \
    --to-revisions=PREVIOUS_REVISION=100 \
    --region=us-central1

# 3. Verify rollback worked
curl -s https://chatterfix.com | head -5
```

---

## Resource Management

### Cloud Run Services Inventory
**Currently Running (Essential):**
- chatterfix-cmms (Main UI Gateway) - **PRODUCTION**
- chatterfix-ai-brain (AI Services)
- chatterfix-assets (Asset Management)
- chatterfix-parts (Parts Inventory)
- chatterfix-work-orders (Work Order Management)
- chatterfix-database (Database Service)
- chatterfix-document-intelligence (Document Processing)
- chatterfix-storage-api (Storage API)

**Removed (To Free Resources):**
- ~~chatterfix-ui-gateway~~ (Duplicate, removed)
- ~~line-smart~~ (Unused, removed)
- ~~linesmart-platform~~ (Unused, removed)
- ~~fredfix-training-platform~~ (Unused, removed)
- ~~chatterfix-llama-api~~ (Unused, removed)

### CPU Quota Management
- **Monitor Usage**: Regularly check quota usage
- **Service Cleanup**: Remove unused services immediately
- **Resource Limits**: Use minimal but sufficient resources (512Mi RAM, 1 CPU)
- **Scaling Policy**: min-instances=0, max-instances=2 for cost efficiency

---

## File Structure & Version Control

### Critical Files
- **app.py**: Main application file (MUST contain professional landing page)
- **deploy-chatterfix.sh**: Primary deployment script
- **Dockerfile**: Container configuration

### Backup Strategy
```bash
# Before any major changes, create backup
cp app.py app.py.backup.$(date +%Y%m%d_%H%M%S)
git add . && git commit -m "Backup before deployment"
```

### Deployment Scripts Audit
**Primary Scripts (Keep):**
- deploy-chatterfix.sh (Main deployment)
- deploy-main-ui-gateway.sh (Alternative deployment)

**Secondary Scripts (Review/Consolidate):**
- 14+ other deployment scripts need review and possible consolidation

---

## Monitoring & Alerts

### Health Checks
- **Automated**: Monitor /health endpoint every 5 minutes
- **Manual**: Verify landing page content after each deployment
- **Email Test**: Ensure email signup form works correctly

### Performance Monitoring
- **Response Time**: < 2 seconds for landing page
- **Uptime**: 99.9% availability target
- **Error Rate**: < 1% error rate

### Alert Conditions
1. **Service Down**: Immediate alert if chatterfix.com is unreachable
2. **Wrong Content**: Alert if old dashboard content is detected
3. **Email Error**: Alert if wrong email domain is found
4. **Resource Quota**: Alert when approaching CPU limits

---

## Emergency Contacts

**Primary**: yoyofred@gringosgambit.com
**Deployment Issues**: Check this document first
**Resource Limits**: Clean up unused services

---

## Testing Protocol

### Before Each Deployment
1. **Local Testing**: Verify app.py runs locally on port 8080
2. **Content Check**: Confirm professional landing page loads
3. **Email Verification**: Check all email links point to @gringosgambit.com
4. **Resource Check**: Ensure sufficient Cloud Run quota

### After Each Deployment
1. **Immediate Check**: curl https://chatterfix.com within 30 seconds
2. **Content Verification**: Confirm title shows "Revolutionary AI-Powered"
3. **Email Test**: Submit test email through signup form
4. **Performance Test**: Check page load time < 2 seconds

---

## Lessons Learned

1. **Resource Management**: Keep only essential services running
2. **Single Source of Truth**: Use one primary deployment script
3. **Pre-deployment Checks**: Always verify current state before deploying
4. **Post-deployment Verification**: Immediate content verification is critical
5. **Documentation**: Keep deployment process well-documented

---

## Future Improvements

1. **Automated Testing**: Implement CI/CD pipeline with automated tests
2. **Staging Environment**: Create staging environment for testing
3. **Infrastructure as Code**: Move to Terraform for resource management
4. **Monitoring Dashboard**: Create real-time monitoring dashboard
5. **Automated Rollback**: Implement automatic rollback on deployment failure

---

**Last Updated:** October 3, 2025
**Next Review:** October 10, 2025
**Status:** ✅ All systems operational - Professional landing page live at https://chatterfix.com
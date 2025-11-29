# ChatterFix Custom Domain Setup (chatterfix.com)

Deploy your ChatterFix CMMS to your custom domain with SSL certificate.

## 🚀 Quick Setup

```bash
# Deploy to custom domain
./deploy-custom-domain.sh

# Monitor deployment progress
./check-domain-status.sh
```

## 📋 Prerequisites

1. **Domain Ownership**: You must own `chatterfix.com`
2. **Domain Verification**: Verify ownership in Google Search Console
3. **DNS Access**: Ability to modify DNS records for your domain
4. **GCP Project**: ChatterFix already deployed to Cloud Run

## 🔧 Step-by-Step Process

### 1. Verify Domain Ownership

**Before running the script:**

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Click "Add Property" 
3. Enter `chatterfix.com`
4. Follow verification steps (HTML file upload or DNS TXT record)
5. Confirm verification is successful

### 2. Deploy Custom Domain

```bash
./deploy-custom-domain.sh
```

This script will:
- ✅ Deploy ChatterFix to Cloud Run (if not already deployed)
- ✅ Create domain mapping for chatterfix.com
- ✅ Generate required DNS records
- ✅ Set up automatic SSL certificate provisioning

### 3. Configure DNS Records

The script will output DNS records like these:

**CNAME Record:**
```
Name: chatterfix.com (or @)
Value: ghs.googlehosted.com
TTL: 300
```

**TXT Record (for verification):**
```
Name: _acme-challenge.chatterfix.com
Value: [generated-value]
TTL: 300
```

### 4. Add DNS Records

**For most DNS providers:**

1. Log into your domain registrar/DNS provider
2. Go to DNS management
3. Add the CNAME record:
   - **Type**: CNAME
   - **Name**: @ (or chatterfix.com)
   - **Value**: ghs.googlehosted.com
   - **TTL**: 300

4. Add the TXT record:
   - **Type**: TXT
   - **Name**: _acme-challenge
   - **Value**: [from script output]
   - **TTL**: 300

### 5. Wait for Propagation

- **DNS Propagation**: 5-60 minutes
- **SSL Certificate**: 15-60 minutes after DNS is active

**Monitor progress:**
```bash
./check-domain-status.sh
```

## 🌐 Popular DNS Providers

### Cloudflare
1. Go to DNS tab
2. Add CNAME record: `@` → `ghs.googlehosted.com`
3. Add TXT record: `_acme-challenge` → `[value]`
4. Set Proxy status to "DNS only" (gray cloud)

### GoDaddy
1. Go to DNS Management
2. Add CNAME record: `@` → `ghs.googlehosted.com`
3. Add TXT record: `_acme-challenge` → `[value]`

### Namecheap
1. Go to Advanced DNS
2. Add CNAME record: `@` → `ghs.googlehosted.com`
3. Add TXT record: `_acme-challenge` → `[value]`

### Google Domains
1. Go to DNS settings
2. Add CNAME record: `@` → `ghs.googlehosted.com`
3. Add TXT record: `_acme-challenge` → `[value]`

## 🔍 Troubleshooting

### Domain Not Verified
```bash
# Check verification status
gcloud domains list-user-verified
```
**Solution**: Complete domain verification in Google Search Console

### DNS Not Propagating
```bash
# Check DNS propagation
nslookup chatterfix.com
dig chatterfix.com CNAME
```
**Solution**: Wait longer or contact DNS provider

### SSL Certificate Issues
```bash
# Check certificate status
gcloud run domain-mappings describe chatterfix.com --region=us-central1
```
**Solutions**:
- Ensure DNS records are correct
- Wait for propagation
- Check domain verification

### Service Not Found
```bash
# Deploy service first
./deploy-gcp.sh
```

## 🔧 Advanced Configuration

### Custom Subdomain
To deploy to `app.chatterfix.com` instead:
```bash
# Edit the deploy script
DOMAIN="app.chatterfix.com"
```

### Multiple Domains
```bash
# Map additional domains
gcloud run domain-mappings create \
  --service=chatterfix-cmms \
  --domain=www.chatterfix.com \
  --region=us-central1
```

### Force HTTPS Redirect
Cloud Run automatically redirects HTTP to HTTPS.

## 📊 Monitoring

### Health Checks
```bash
# Test health endpoint
curl https://chatterfix.com/health

# Test with verbose output
curl -v https://chatterfix.com/health
```

### View Logs
```bash
# Service logs
gcloud run logs read --service=chatterfix-cmms --region=us-central1

# Follow logs live
gcloud run logs tail --service=chatterfix-cmms --region=us-central1
```

### Domain Status
```bash
# Check domain mapping
gcloud run domain-mappings list --region=us-central1

# Detailed status
gcloud run domain-mappings describe chatterfix.com --region=us-central1
```

## 🎯 Final Steps

Once DNS propagates and SSL is ready:

1. **✅ Test**: `https://chatterfix.com/health`
2. **✅ Login**: `https://chatterfix.com`
3. **✅ Configure**: Set up Firebase Auth domains
4. **✅ Monitor**: Set up alerts and monitoring

## 🔄 Updating Deployment

To update the application:
```bash
# Rebuild and deploy
./deploy-gcp.sh

# No DNS changes needed - domain mapping persists
```

---

**🎉 Success!** ChatterFix will be available at `https://chatterfix.com` with automatic SSL certificate!

## 📞 Support

**Common Issues:**
- Domain verification → Check Google Search Console
- DNS propagation → Wait 15-60 minutes
- SSL certificate → Ensure DNS is correct
- 404 errors → Check service deployment

**Debug Commands:**
```bash
./check-domain-status.sh
gcloud run domain-mappings describe chatterfix.com --region=us-central1
curl -v https://chatterfix.com/health
```
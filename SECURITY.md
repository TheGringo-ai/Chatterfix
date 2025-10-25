# 🔐 ChatterFix CMMS - Security & Environment Management

## 🎯 **Overview**
This document outlines the secure environment variable management system for ChatterFix CMMS.

## 📁 **File Structure**
```
.
├── .env.local                  # Local development (git-ignored)
├── .env.template              # Template for new developers
├── .gitignore                 # Security protection
├── config/
│   ├── env_loader.py          # Environment variable loader
│   └── __init__.py
├── deploy-with-env.sh         # Secure deployment script
└── SECURITY.md               # This file
```

## 🔑 **API Keys & Credentials**

### Current Configuration:
- **OpenAI API Key**: `REDACTED_OPENAI_KEY`
- **Database**: PostgreSQL on Google Cloud SQL
- **Project**: fredfix (Google Cloud)

### ⚠️ **IMPORTANT SECURITY NOTES**:
1. **NEVER commit .env files** to git
2. **Revoke and regenerate** API keys if exposed
3. **Use environment variables** in production
4. **Rotate credentials** regularly

## 🚀 **Deployment**

### Secure Production Deployment:
```bash
# Deploy with environment variables
./deploy-with-env.sh
```

### Manual Cloud Run Deployment:
```bash
gcloud run deploy chatterfix-unified-gateway \
  --source frontend/ \
  --region us-central1 \
  --set-env-vars="OPENAI_API_KEY=your-key" \
  --set-env-vars="DATABASE_URL=your-db-url"
```

## 💻 **Local Development**

### Setup:
1. Copy environment template:
   ```bash
   cp .env.template .env.local
   ```

2. Fill in your actual values in `.env.local`

3. Use the environment loader:
   ```python
   from config.env_loader import get_env, get_openai_config
   
   api_key = get_env('OPENAI_API_KEY')
   config = get_openai_config()
   ```

## 🛡️ **Security Features**

### ✅ **Implemented**:
- Environment variable templates
- Comprehensive .gitignore
- Secure deployment scripts
- Environment loader utility
- Production/development separation

### 🔄 **Environment Loading Priority**:
1. System environment variables (Cloud Run)
2. `.env.local` (local development)
3. `.env.production` (production backup)
4. `.env` (fallback)
5. `.env.template` (template only)

## 🔧 **Usage Examples**

### Python Services:
```python
from config.env_loader import get_database_config, get_openai_config

# Database connection
db_config = get_database_config()
connection_string = db_config['url']

# OpenAI configuration
openai_config = get_openai_config()
client = OpenAI(api_key=openai_config['api_key'])
```

### Environment Detection:
```python
from config.env_loader import is_production, is_debug

if is_production():
    # Production-specific code
    log_level = 'INFO'
else:
    # Development-specific code
    log_level = 'DEBUG'
```

## 🎯 **Service URLs**

### Production:
- **Main App**: https://chatterfix.com
- **Gateway**: https://chatterfix-unified-gateway-650169261019.us-central1.run.app
- **Work Orders**: https://chatterfix-work-orders-650169261019.us-central1.run.app
- **Assets**: https://chatterfix-assets-650169261019.us-central1.run.app
- **Parts**: https://chatterfix-parts-650169261019.us-central1.run.app

### Development:
- **Local**: http://localhost:8080
- **Services**: http://localhost:800[1-6]

## 📝 **Best Practices**

1. **Never hardcode credentials** in source code
2. **Use environment variables** for all configuration
3. **Separate development and production** environments
4. **Rotate API keys** regularly
5. **Monitor access logs** for suspicious activity
6. **Use least privilege** principle for service accounts

## 🚨 **Emergency Procedures**

### If API Key is Compromised:
1. **Immediately revoke** the key in OpenAI dashboard
2. **Generate new key**
3. **Update Cloud Run environment variables**
4. **Redeploy services**
5. **Monitor usage** for unauthorized activity

### If Database is Compromised:
1. **Change database passwords**
2. **Update connection strings**
3. **Review access logs**
4. **Redeploy all services**

---

**Last Updated**: 2025-10-24
**Security Level**: Production Ready ✅
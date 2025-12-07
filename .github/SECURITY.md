# Security Policy

## Supported Versions

We actively support the following versions of ChatterFix CMMS:

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### 🔒 Private Disclosure

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please:

1. **Email**: Send details to security@chatterfix.com
2. **Include**: 
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

### 📋 What to Include

- **Environment**: Version, deployment type (Cloud Run, local, etc.)
- **Vulnerability Type**: Authentication, authorization, injection, etc.
- **Severity**: Critical, High, Medium, Low
- **Affected Components**: API endpoints, database, authentication, etc.

### ⏱️ Response Timeline

- **24 hours**: Initial acknowledgment
- **72 hours**: Initial assessment and severity classification
- **1 week**: Status update and timeline for fix
- **2 weeks**: Target resolution for critical vulnerabilities

### 🛡️ Security Best Practices

When deploying ChatterFix:

1. **Environment Variables**: Never commit secrets to version control
2. **Database Security**: Use Firebase security rules and IAM
3. **API Security**: Enable authentication for production deployments
4. **HTTPS**: Always use HTTPS in production
5. **Updates**: Keep dependencies updated (Dependabot helps!)

### 🔄 Dependency Security

- Dependabot automatically monitors for vulnerable dependencies
- Security updates are prioritized and released ASAP
- Check the security tab on GitHub for vulnerability alerts

## Security Features

ChatterFix includes several built-in security features:

- **Rate Limiting**: API request throttling
- **CORS Protection**: Configurable cross-origin policies  
- **Input Validation**: Pydantic model validation
- **Authentication**: Firebase Auth integration
- **Audit Logging**: Comprehensive activity logging

## Third-Party Dependencies

We regularly audit our dependencies for security vulnerabilities:

- **Python packages**: Monitored via pip-audit and Dependabot
- **GitHub Actions**: Monitored via Dependabot
- **Docker images**: Base images updated regularly

---

Thank you for helping keep ChatterFix secure! 🔐
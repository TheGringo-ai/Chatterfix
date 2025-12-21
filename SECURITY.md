# Security Policy

**ChatterFix CMMS Platform**

---

## Our Commitment

Security is a top priority at ChatterFix. We are committed to protecting our users' data and maintaining the integrity of our platform. This document outlines our security practices and how to report vulnerabilities.

---

## Reporting a Vulnerability

### How to Report

If you discover a security vulnerability, please report it responsibly:

**Email:** security@chatterfix.com

**Include in your report:**
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any supporting materials (screenshots, logs)

### What to Expect

| Timeline | Action |
|----------|--------|
| 24 hours | Acknowledgment of your report |
| 72 hours | Initial assessment and severity rating |
| 7 days | Status update on remediation |
| 90 days | Public disclosure (coordinated with you) |

### Safe Harbor

We will not pursue legal action against security researchers who:
- Report vulnerabilities in good faith
- Do not access or modify user data
- Do not disrupt service availability
- Follow responsible disclosure practices

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest (main branch) | Yes |
| Previous releases | 90 days after new release |
| Development branches | No security support |

---

## Security Architecture

### Infrastructure

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│   │   WAF       │    │  Cloud      │    │  DDoS       │     │
│   │   Firewall  │────│  Armor      │────│  Protection │     │
│   └─────────────┘    └─────────────┘    └─────────────┘     │
│          │                  │                  │             │
│   ┌──────▼──────────────────▼──────────────────▼──────┐     │
│   │              Google Cloud Run                      │     │
│   │         (Container Isolation, Auto-scaling)        │     │
│   └────────────────────────┬───────────────────────────┘     │
│                            │                                 │
│   ┌────────────────────────▼───────────────────────────┐     │
│   │              Application Layer                      │     │
│   │    FastAPI + Authentication + Authorization         │     │
│   └────────────────────────┬───────────────────────────┘     │
│                            │                                 │
│   ┌────────────────────────▼───────────────────────────┐     │
│   │              Firebase/Firestore                     │     │
│   │         (Encrypted at Rest, IAM Policies)          │     │
│   └────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Encryption

| Data State | Encryption |
|------------|------------|
| In Transit | TLS 1.3 |
| At Rest | AES-256 |
| Backups | AES-256 |
| Secrets | Google Secret Manager |

### Authentication

- **Firebase Authentication** for user management
- **Session tokens** with secure cookie settings
- **Multi-factor authentication** (Enterprise)
- **OAuth 2.0** for API access
- **Role-based access control** (RBAC)

### Session Security

```python
# Session cookie security settings
set_cookie(
    key="session_token",
    value=token,
    httponly=True,      # Prevents XSS access
    secure=True,        # HTTPS only
    samesite="lax",     # CSRF protection
    max_age=86400       # 24-hour expiry
)
```

---

## Security Practices

### Code Security

- **Dependency Scanning:** Automated Dependabot alerts
- **Static Analysis:** Bandit security linting
- **Code Review:** All changes require review
- **Secret Detection:** Pre-commit hooks prevent secret commits
- **Input Validation:** Pydantic models for all inputs

### Infrastructure Security

- **Container Isolation:** Each request runs in isolated container
- **Least Privilege:** Minimal IAM permissions
- **Network Segmentation:** VPC with private subnets
- **Secrets Management:** Google Secret Manager, no hardcoded secrets
- **Logging & Monitoring:** Cloud Logging with alerting

### Development Security

- **Pre-commit Hooks:** Security checks before commit
- **CI/CD Security:** Automated security scans in pipeline
- **Dependency Updates:** Weekly automated updates
- **Security Training:** Regular developer security training

---

## Compliance

### Standards We Follow

| Standard | Status |
|----------|--------|
| OWASP Top 10 | Actively mitigated |
| SOC 2 Type II | Via Google Cloud |
| GDPR | Compliant |
| CCPA | Compliant |
| HIPAA | Available for Enterprise |

### Data Protection

- **Data Residency:** US-based by default, EU available for Enterprise
- **Data Retention:** Configurable retention policies
- **Right to Delete:** GDPR/CCPA compliant deletion
- **Data Portability:** Export your data anytime

---

## Security Features

### For All Users

- Encrypted communications (HTTPS only)
- Secure authentication
- Session timeout
- Audit logging
- Input sanitization

### Enterprise Security Add-ons

- Single Sign-On (SSO) integration
- Multi-factor authentication
- IP allowlisting
- Custom session policies
- Advanced audit logs
- SOC 2 compliance reports
- Dedicated security reviews

---

## Incident Response

### Our Process

1. **Detection:** 24/7 automated monitoring
2. **Containment:** Immediate isolation of affected systems
3. **Investigation:** Root cause analysis
4. **Remediation:** Patch and restore
5. **Notification:** Affected users notified within 72 hours
6. **Review:** Post-incident review and improvements

### Your Role

If you suspect a security incident:
1. Change your password immediately
2. Review recent account activity
3. Report to security@chatterfix.com
4. Preserve any evidence

---

## Security Updates

### Staying Informed

- **Security Advisories:** Published on GitHub
- **Email Notifications:** Critical issues emailed to admins
- **Changelog:** Security fixes noted in releases

### Applying Updates

For self-hosted deployments:
```bash
# Pull latest security updates
git pull origin main

# Rebuild container
docker build -t chatterfix .

# Deploy
./deploy.sh
```

---

## Bug Bounty Program

We appreciate security researchers who help keep ChatterFix safe.

### In Scope

- chatterfix.com and subdomains
- ChatterFix API endpoints
- Authentication and authorization
- Data exposure vulnerabilities
- Injection attacks

### Out of Scope

- Social engineering attacks
- Physical security
- Denial of service attacks
- Third-party services
- Recently disclosed vulnerabilities (< 90 days)

### Rewards

| Severity | Reward |
|----------|--------|
| Critical | $500 - $2,000 |
| High | $200 - $500 |
| Medium | $50 - $200 |
| Low | Recognition |

*Rewards subject to report quality and impact.*

---

## Contact

**Security Team:** security@chatterfix.com

**PGP Key:** Available upon request for encrypted communications

**Response Time:** 24 hours for initial acknowledgment

---

**Thank you for helping keep ChatterFix secure.**

---

*© 2024 Fred Taylor. All Rights Reserved.*

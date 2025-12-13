# Security Scanning Workflow

Comprehensive security analysis for ChatterFix codebase.

## Security Checks

### 1. Dependency Vulnerabilities
```bash
# Check Python dependencies for known vulnerabilities
pip-audit

# Alternative using safety
safety check -r requirements.txt
```

### 2. Static Code Analysis
```bash
# Run bandit for Python security issues
bandit -r app/ -f json

# Run semgrep for pattern-based detection
semgrep --config=auto app/
```

### 3. Secret Detection
```bash
# Check for hardcoded secrets
git secrets --scan

# Alternative using trufflehog
trufflehog filesystem . --only-verified
```

### 4. Docker Security
```bash
# Scan Docker image for vulnerabilities
trivy image chatterfix:latest
```

## OWASP Top 10 Checklist

Manually verify protection against:

1. **Injection**: SQL, command, LDAP injection
2. **Broken Authentication**: Session management, credential storage
3. **Sensitive Data Exposure**: Encryption, data masking
4. **XML External Entities**: XXE attack prevention
5. **Broken Access Control**: Authorization checks
6. **Security Misconfiguration**: Headers, error handling
7. **XSS**: Input sanitization, output encoding
8. **Insecure Deserialization**: Safe deserialization
9. **Vulnerable Components**: Dependency updates
10. **Insufficient Logging**: Audit trails, monitoring

## ChatterFix-Specific Security

Check these critical areas:
- Firebase/Firestore security rules
- API authentication tokens
- Voice command input sanitization
- File upload validation (OCR documents)
- User permission boundaries
- Environment variable handling (.env files)

## Action Items

If vulnerabilities found:
1. **Critical/High**: Fix immediately before any deployment
2. **Medium**: Create issue, fix within 7 days
3. **Low**: Document and plan for next sprint

## Never Commit

- .env files with real credentials
- API keys or tokens
- Database connection strings
- Private keys or certificates

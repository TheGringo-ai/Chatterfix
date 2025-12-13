#!/bin/bash

# ChatterFix CMMS - Security Hardening Script
# Comprehensive security checks for development and production

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SECURITY_SCORE=0
MAX_SCORE=100

log() {
    echo -e "${BLUE}[SECURITY]${NC} $1"
}

error() {
    echo -e "${RED}[CRITICAL]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SECURE]${NC} $1"
    SECURITY_SCORE=$((SECURITY_SCORE + 10))
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    SECURITY_SCORE=$((SECURITY_SCORE + 5))
}

# Check for sensitive files in git
check_git_security() {
    log "Checking git repository security..."
    
    # Check for accidentally committed secrets
    if git log --all --grep="password\|secret\|key\|token" --oneline | head -5; then
        error "Found potential secrets in git history!"
    else
        success "No obvious secrets found in git history"
    fi
    
    # Check for large files that might contain secrets
    if find . -name "*.json" -size +1M -not -path "./node_modules/*" | head -3; then
        warn "Found large JSON files that might contain secrets"
    else
        success "No suspicious large JSON files found"
    fi
    
    # Check .env file protection
    if [ -f ".env" ] && ! grep -q "^.env$" .gitignore; then
        error ".env file exists but not in .gitignore!"
    else
        success ".env file properly protected"
    fi
}

# Docker security checks
check_docker_security() {
    log "Checking Docker security configuration..."
    
    # Check Dockerfile for security best practices
    if [ -f "Dockerfile" ]; then
        # Check for non-root user
        if grep -q "USER.*[^root]" Dockerfile; then
            success "Dockerfile uses non-root user"
        else
            error "Dockerfile runs as root - security risk!"
        fi
        
        # Check for latest tag usage
        if grep -q "FROM.*:latest" Dockerfile; then
            warn "Dockerfile uses 'latest' tag - not reproducible"
        else
            success "Dockerfile uses pinned image versions"
        fi
        
        # Check for secrets in Dockerfile
        if grep -iE "(password|secret|key|token)" Dockerfile; then
            error "Found potential secrets in Dockerfile!"
        else
            success "No secrets detected in Dockerfile"
        fi
    fi
    
    # Check docker-compose security
    if [ -f "docker-compose.yml" ]; then
        # Check for exposed ports
        if grep -q "0.0.0.0:" docker-compose.yml; then
            warn "Docker services expose ports to all interfaces"
        else
            success "Docker ports properly configured"
        fi
    fi
}

# Python dependency security
check_python_security() {
    log "Checking Python dependency security..."
    
    # Check if safety is installed
    if command -v safety &> /dev/null; then
        # Run safety check on requirements
        if safety check -r requirements-full.txt --json > safety_report.json 2>/dev/null; then
            if [ -s safety_report.json ] && [ "$(cat safety_report.json)" != "[]" ]; then
                error "Found security vulnerabilities in dependencies!"
                cat safety_report.json | jq '.[].vulnerability'
            else
                success "No known vulnerabilities in dependencies"
            fi
        else
            warn "Could not run safety check"
        fi
        rm -f safety_report.json
    else
        warn "Safety tool not installed - install with: pip install safety"
    fi
    
    # Check for pinned dependencies
    if grep -q "==" requirements-full.txt; then
        success "Dependencies are pinned to specific versions"
    else
        warn "Dependencies not pinned - potential security risk"
    fi
}

# Environment and secrets security
check_env_security() {
    log "Checking environment and secrets security..."
    
    # Check for .env template
    if [ -f ".env.template" ]; then
        success "Environment template exists for secure configuration"
    else
        warn "No .env.template found - create one for team consistency"
    fi
    
    # Check current environment for insecure defaults
    if [ -f ".env" ]; then
        # Check for default/weak values
        if grep -q "your-secret-key\|password123\|admin\|test" .env; then
            error "Found default/weak secrets in .env file!"
        else
            success "No obvious weak secrets in .env"
        fi
        
        # Check for proper key lengths
        if grep -E "SECRET_KEY=.{32,}" .env >/dev/null; then
            success "Secret keys appear to be properly sized"
        else
            warn "Secret keys may be too short"
        fi
    fi
}

# Cloud security configuration
check_cloud_security() {
    log "Checking cloud deployment security..."
    
    # Check for cloud configuration files
    if [ -d "k8s" ]; then
        # Check Kubernetes configurations
        for file in k8s/*.yaml k8s/*.yml; do
            if [ -f "$file" ]; then
                # Check for hardcoded secrets
                if grep -iE "(password|secret|key):" "$file"; then
                    error "Found potential hardcoded secrets in $file"
                else
                    success "No hardcoded secrets in Kubernetes configs"
                fi
            fi
        done
    fi
    
    # Check deployment scripts
    if [ -f "scripts/deploy.sh" ]; then
        if grep -q "set -euo pipefail" scripts/deploy.sh; then
            success "Deployment script uses secure shell options"
        else
            warn "Deployment script should use 'set -euo pipefail'"
        fi
    fi
}

# Network and API security
check_api_security() {
    log "Checking API and network security..."
    
    # Check for CORS configuration
    if grep -r "CORS\|cors" . --include="*.py" >/dev/null; then
        success "CORS configuration found"
    else
        warn "No CORS configuration detected"
    fi
    
    # Check for rate limiting
    if grep -r "rate.limit\|slowapi" . --include="*.py" >/dev/null; then
        success "Rate limiting implementation found"
    else
        warn "No rate limiting detected - add for production"
    fi
    
    # Check for input validation
    if grep -r "pydantic\|validation" . --include="*.py" >/dev/null; then
        success "Input validation framework detected"
    else
        warn "No input validation framework found"
    fi
}

# File permissions security
check_file_permissions() {
    log "Checking file permissions..."
    
    # Check for overly permissive files
    if find . -name "*.sh" -perm 777 | head -3; then
        warn "Found scripts with 777 permissions"
    else
        success "Script permissions appear secure"
    fi
    
    # Check for secret files with wrong permissions
    if find . -name "*.key" -o -name "*.pem" | xargs ls -la 2>/dev/null | grep -v "^-r--------"; then
        error "Found secret files with insecure permissions!"
    else
        success "Secret file permissions appear secure"
    fi
}

# Generate security report
generate_security_report() {
    log "Generating security assessment report..."
    
    echo "
# ChatterFix CMMS Security Assessment Report
Generated: $(date)

## Security Score: ${SECURITY_SCORE}/${MAX_SCORE}

## Recommendations:
1. Regularly update dependencies with: pip install -U -r requirements-full.txt
2. Run security scans before each deployment
3. Rotate API keys and secrets monthly
4. Monitor security logs and alerts
5. Use multi-factor authentication for all accounts
6. Implement intrusion detection systems
7. Regular security audits and penetration testing

## Technician-Specific Security:
- Voice command data encryption in transit
- OCR document data privacy protection
- Mobile device security for field technicians
- Secure authentication for equipment access
- Audit trails for maintenance actions

## Next Steps:
- Set up automated security scanning in CI/CD
- Implement security monitoring and alerting
- Create incident response procedures
- Train team on security best practices
" > security_report.md
    
    success "Security report generated: security_report.md"
}

# Main security check function
main() {
    log "Starting ChatterFix CMMS security assessment..."
    
    check_git_security
    check_docker_security
    check_python_security
    check_env_security
    check_cloud_security
    check_api_security
    check_file_permissions
    generate_security_report
    
    echo ""
    if [ $SECURITY_SCORE -ge 80 ]; then
        success "Security assessment PASSED: ${SECURITY_SCORE}/${MAX_SCORE}"
    elif [ $SECURITY_SCORE -ge 60 ]; then
        warn "Security assessment MODERATE: ${SECURITY_SCORE}/${MAX_SCORE}"
    else
        error "Security assessment FAILED: ${SECURITY_SCORE}/${MAX_SCORE}"
        echo "Please address critical security issues before deployment!"
        exit 1
    fi
    
    log "🛡️  ChatterFix CMMS security check complete"
}

# Run main function
main "$@"
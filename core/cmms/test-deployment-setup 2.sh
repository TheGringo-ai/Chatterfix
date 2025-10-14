#!/bin/bash

# Test script for deployment setup validation
# This checks if all required files and configurations are in place

echo "🧪 Testing ChatterFix SaaS Deployment Setup"
echo "==========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Test 1: Check deployment script exists and is executable
test_deployment_script() {
    print_status "Testing deployment script..."
    
    if [[ -f "deploy-saas-platform.sh" ]]; then
        print_success "Deployment script exists"
    else
        print_error "Deployment script not found"
        return 1
    fi
    
    if [[ -x "deploy-saas-platform.sh" ]]; then
        print_success "Deployment script is executable"
    else
        print_error "Deployment script is not executable"
        return 1
    fi
}

# Test 2: Check GitHub workflow exists
test_github_workflow() {
    print_status "Testing GitHub workflow..."
    
    if [[ -f ".github/workflows/deploy.yml" ]]; then
        print_success "GitHub workflow exists"
    else
        print_error "GitHub workflow not found"
        return 1
    fi
    
    # Check if workflow contains required elements
    if grep -q "chatterfix-saas-platform" .github/workflows/deploy.yml; then
        print_success "Workflow contains SaaS platform deployment"
    else
        print_error "Workflow missing SaaS platform configuration"
        return 1
    fi
}

# Test 3: Check required tools
test_prerequisites() {
    print_status "Testing prerequisites..."
    
    # Check if gcloud is available
    if command -v gcloud &> /dev/null; then
        print_success "gcloud CLI available"
    else
        print_warning "gcloud CLI not found (needed for deployment)"
    fi
    
    # Check if docker is available
    if command -v docker &> /dev/null; then
        print_success "Docker available"
    else
        print_warning "Docker not found (needed for deployment)"
    fi
    
    # Check git
    if command -v git &> /dev/null; then
        print_success "Git available"
    else
        print_error "Git not found"
        return 1
    fi
}

# Test 4: Check Python dependencies
test_python_setup() {
    print_status "Testing Python setup..."
    
    if [[ -f "requirements.txt" ]]; then
        print_success "Requirements file exists"
    else
        print_error "requirements.txt not found"
        return 1
    fi
    
    if [[ -f "saas_management_service.py" ]]; then
        print_success "SaaS management service exists"
    else
        print_error "SaaS management service not found"
        return 1
    fi
}

# Test 5: Check Dockerfile
test_docker_setup() {
    print_status "Testing Docker setup..."
    
    if [[ -f "Dockerfile" ]]; then
        print_success "Main Dockerfile exists"
    else
        print_error "Main Dockerfile not found"
        return 1
    fi
}

# Test 6: Check git status
test_git_status() {
    print_status "Testing git status..."
    
    # Check if we're in a git repo
    if git rev-parse --git-dir > /dev/null 2>&1; then
        print_success "In git repository"
    else
        print_error "Not in a git repository"
        return 1
    fi
    
    # Check current branch
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    print_status "Current branch: $BRANCH"
    
    # Check if there are uncommitted changes
    if git diff --quiet && git diff --staged --quiet; then
        print_success "No uncommitted changes"
    else
        print_warning "Uncommitted changes present"
        git status --porcelain
    fi
}

# Run all tests
echo "Running deployment setup tests..."
echo ""

TESTS_PASSED=0
TESTS_TOTAL=6

test_deployment_script && ((TESTS_PASSED++))
test_github_workflow && ((TESTS_PASSED++))
test_prerequisites && ((TESTS_PASSED++))
test_python_setup && ((TESTS_PASSED++))
test_docker_setup && ((TESTS_PASSED++))
test_git_status && ((TESTS_PASSED++))

echo ""
echo "Test Results:"
echo "============="
print_status "Tests passed: $TESTS_PASSED/$TESTS_TOTAL"

if [[ $TESTS_PASSED -eq $TESTS_TOTAL ]]; then
    print_success "All tests passed! Deployment setup is ready."
    exit 0
else
    print_warning "Some tests failed. Review the issues above."
    exit 1
fi
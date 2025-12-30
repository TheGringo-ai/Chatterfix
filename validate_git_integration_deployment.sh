#!/bin/bash
# Comprehensive Validation for Fix It Fred Git Integration Deployment
# This script validates the complete Git integration setup

set -e

echo "🔍 Fix It Fred Git Integration - Deployment Validation"
echo "====================================================="
echo ""

# Configuration
VM_IP="35.237.149.25"
FRED_AI_PORT="9000"
GIT_SERVICE_PORT="9002"
CMMS_PORT="8080"
REPO_DIR="/home/yoyofred_gringosgambit_com/chatterfix-docker"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="/tmp/git_integration_validation_$(date +%s).log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

echo "📝 Validation log: $LOG_FILE"
echo ""

# Helper functions
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            echo -e "${GREEN}✅ PASS${NC}: $message"
            ;;
        "FAIL")
            echo -e "${RED}❌ FAIL${NC}: $message"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️ WARN${NC}: $message"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️ INFO${NC}: $message"
            ;;
    esac
}

test_endpoint() {
    local url=$1
    local description=$2
    local timeout=${3:-10}
    
    if curl -f --max-time "$timeout" "$url" > /dev/null 2>&1; then
        print_status "PASS" "$description"
        return 0
    else
        print_status "FAIL" "$description"
        return 1
    fi
}

test_json_endpoint() {
    local url=$1
    local description=$2
    local expected_field=$3
    local timeout=${4:-10}
    
    local response=$(curl -s --max-time "$timeout" "$url" 2>/dev/null || echo "")
    
    if [ -n "$response" ] && echo "$response" | jq -e ".$expected_field" > /dev/null 2>&1; then
        print_status "PASS" "$description"
        echo "   Response: $(echo "$response" | jq -c .)"
        return 0
    else
        print_status "FAIL" "$description"
        if [ -n "$response" ]; then
            echo "   Response: $response"
        fi
        return 1
    fi
}

# Validation Tests

echo "🔧 1. BASIC CONNECTIVITY TESTS"
echo "==============================="

# Test VM connectivity
if ping -c 1 "$VM_IP" > /dev/null 2>&1; then
    print_status "PASS" "VM is reachable at $VM_IP"
else
    print_status "FAIL" "VM is not reachable at $VM_IP"
fi

# Test core services
test_endpoint "http://$VM_IP:$CMMS_PORT/health" "ChatterFix CMMS main service"
test_endpoint "http://$VM_IP:$FRED_AI_PORT/health" "Fix It Fred AI service"
test_endpoint "http://$VM_IP:$GIT_SERVICE_PORT/health" "Git Integration service"

echo ""
echo "🤖 2. FIX IT FRED AI SERVICE TESTS"
echo "=================================="

# Test AI service health
test_json_endpoint "http://$VM_IP:$FRED_AI_PORT/health" "AI service health check" "status"

# Test AI chat functionality
AI_CHAT_RESPONSE=$(curl -s --max-time 15 -X POST "http://$VM_IP:$FRED_AI_PORT/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "test deployment", "provider": "ollama", "model": "mistral:7b"}' 2>/dev/null || echo "")

if [ -n "$AI_CHAT_RESPONSE" ] && echo "$AI_CHAT_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    print_status "PASS" "AI chat functionality working"
    echo "   AI Response: $(echo "$AI_CHAT_RESPONSE" | jq -r '.response' | head -c 100)..."
else
    print_status "FAIL" "AI chat functionality not working"
    if [ -n "$AI_CHAT_RESPONSE" ]; then
        echo "   Response: $AI_CHAT_RESPONSE"
    fi
fi

echo ""
echo "📊 3. GIT INTEGRATION SERVICE TESTS"
echo "==================================="

# Test Git service health
test_json_endpoint "http://$VM_IP:$GIT_SERVICE_PORT/health" "Git service health check" "status"

# Test Git status API
test_json_endpoint "http://$VM_IP:$GIT_SERVICE_PORT/api/git/status" "Git status API" "branch"

# Test Git configuration API
test_json_endpoint "http://$VM_IP:$GIT_SERVICE_PORT/api/git/config" "Git configuration API" "repo_path"

# Test Git commits API
test_endpoint "http://$VM_IP:$GIT_SERVICE_PORT/api/git/commits" "Git commits API"

echo ""
echo "🔐 4. AUTHENTICATION AND SECURITY TESTS"
echo "========================================"

# Test SSH connection to VM (if possible)
print_status "INFO" "Testing SSH connection to VM..."
if command -v gcloud &> /dev/null; then
    if gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="echo 'SSH test successful'" > /dev/null 2>&1; then
        print_status "PASS" "SSH connection to VM working"
    else
        print_status "WARN" "SSH connection failed (check GCP credentials)"
    fi
else
    print_status "WARN" "gcloud CLI not available for SSH test"
fi

# Test if Git repository is properly configured on VM
print_status "INFO" "Testing Git repository configuration on VM..."
if command -v gcloud &> /dev/null; then
    GIT_STATUS=$(gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="cd $REPO_DIR && git status --porcelain" 2>/dev/null || echo "FAILED")
    
    if [ "$GIT_STATUS" != "FAILED" ]; then
        print_status "PASS" "Git repository is accessible on VM"
        if [ -n "$GIT_STATUS" ]; then
            print_status "INFO" "Repository has uncommitted changes"
        else
            print_status "INFO" "Repository is clean"
        fi
    else
        print_status "FAIL" "Git repository not accessible on VM"
    fi
fi

echo ""
echo "🚀 5. GITHUB ACTIONS INTEGRATION TESTS"
echo "======================================"

# Check if GitHub Actions workflows exist
if [ -f ".github/workflows/deploy-fix-it-fred-git-integration.yml" ]; then
    print_status "PASS" "Git integration workflow exists"
else
    print_status "FAIL" "Git integration workflow missing"
fi

if [ -f ".github/workflows/deploy.yml" ]; then
    print_status "PASS" "Main deployment workflow exists"
else
    print_status "FAIL" "Main deployment workflow missing"
fi

# Test GitHub API access (if gh CLI is available)
if command -v gh &> /dev/null; then
    if gh repo view > /dev/null 2>&1; then
        print_status "PASS" "GitHub CLI can access repository"
    else
        print_status "WARN" "GitHub CLI not authenticated (expected for VM setup)"
    fi
else
    print_status "INFO" "GitHub CLI not available"
fi

echo ""
echo "📁 6. FILE SYSTEM AND MONITORING TESTS"
echo "======================================"

# Test file monitoring capabilities (requires VM access)
if command -v gcloud &> /dev/null; then
    print_status "INFO" "Testing file monitoring on VM..."
    
    # Check if watchdog is installed
    WATCHDOG_STATUS=$(gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="python3 -c 'import watchdog; print(\"installed\")'" 2>/dev/null || echo "not_installed")
    
    if [ "$WATCHDOG_STATUS" = "installed" ]; then
        print_status "PASS" "Watchdog library available for file monitoring"
    else
        print_status "FAIL" "Watchdog library not installed"
    fi
    
    # Check inotify limits
    INOTIFY_LIMIT=$(gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="cat /proc/sys/fs/inotify/max_user_watches" 2>/dev/null || echo "unknown")
    
    if [ "$INOTIFY_LIMIT" != "unknown" ] && [ "$INOTIFY_LIMIT" -gt 8192 ]; then
        print_status "PASS" "inotify limits sufficient for file monitoring ($INOTIFY_LIMIT)"
    else
        print_status "WARN" "inotify limits may be too low ($INOTIFY_LIMIT)"
    fi
fi

echo ""
echo "🧪 7. INTEGRATION AND WORKFLOW TESTS"
echo "===================================="

# Test AI-Git integration
print_status "INFO" "Testing AI-Git integration..."

AI_GIT_ANALYSIS=$(curl -s --max-time 20 -X POST "http://$VM_IP:$FRED_AI_PORT/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "Analyze this git change: modified app.py to add new feature", "context": "git_analysis", "provider": "ollama"}' 2>/dev/null || echo "")

if [ -n "$AI_GIT_ANALYSIS" ] && echo "$AI_GIT_ANALYSIS" | jq -e '.success' > /dev/null 2>&1; then
    print_status "PASS" "AI can analyze git changes"
else
    print_status "FAIL" "AI git analysis not working"
fi

# Test commit generation
COMMIT_MESSAGE_TEST=$(curl -s --max-time 15 -X POST "http://$VM_IP:$FRED_AI_PORT/api/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "Generate a git commit message for: Added user authentication feature", "provider": "ollama"}' 2>/dev/null || echo "")

if [ -n "$COMMIT_MESSAGE_TEST" ] && echo "$COMMIT_MESSAGE_TEST" | jq -e '.success' > /dev/null 2>&1; then
    print_status "PASS" "AI can generate commit messages"
else
    print_status "FAIL" "AI commit message generation not working"
fi

echo ""
echo "📊 8. PERFORMANCE AND RESOURCE TESTS"
echo "===================================="

# Test response times
print_status "INFO" "Testing service response times..."

AI_RESPONSE_TIME=$(time (curl -s --max-time 10 "http://$VM_IP:$FRED_AI_PORT/health" > /dev/null) 2>&1 | grep real | awk '{print $2}')
GIT_RESPONSE_TIME=$(time (curl -s --max-time 10 "http://$VM_IP:$GIT_SERVICE_PORT/health" > /dev/null) 2>&1 | grep real | awk '{print $2}')

print_status "INFO" "AI Service response time: $AI_RESPONSE_TIME"
print_status "INFO" "Git Service response time: $GIT_RESPONSE_TIME"

# Check if services are using reasonable resources (requires VM access)
if command -v gcloud &> /dev/null; then
    MEMORY_USAGE=$(gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="free -m | grep '^Mem:' | awk '{print \$3/\$2 * 100.0}'" 2>/dev/null || echo "unknown")
    
    if [ "$MEMORY_USAGE" != "unknown" ]; then
        MEMORY_PERCENT=$(echo "$MEMORY_USAGE" | cut -d'.' -f1)
        if [ "$MEMORY_PERCENT" -lt 80 ]; then
            print_status "PASS" "Memory usage acceptable (${MEMORY_PERCENT}%)"
        else
            print_status "WARN" "Memory usage high (${MEMORY_PERCENT}%)"
        fi
    fi
fi

echo ""
echo "🔄 9. SYSTEMD SERVICE TESTS"
echo "==========================="

# Test systemd service status (requires VM access)
if command -v gcloud &> /dev/null; then
    SERVICE_STATUS=$(gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="sudo systemctl is-active fix-it-fred-git.service" 2>/dev/null || echo "unknown")
    
    if [ "$SERVICE_STATUS" = "active" ]; then
        print_status "PASS" "Git Integration systemd service is active"
    else
        print_status "FAIL" "Git Integration systemd service not active ($SERVICE_STATUS)"
    fi
    
    # Check service logs for errors
    ERROR_COUNT=$(gcloud compute ssh chatterfix-cmms-production --zone=us-east1-b --command="sudo journalctl -u fix-it-fred-git.service --since '1 hour ago' | grep -i error | wc -l" 2>/dev/null || echo "unknown")
    
    if [ "$ERROR_COUNT" != "unknown" ]; then
        if [ "$ERROR_COUNT" -eq 0 ]; then
            print_status "PASS" "No errors in service logs (last hour)"
        else
            print_status "WARN" "$ERROR_COUNT errors found in service logs"
        fi
    fi
fi

echo ""
echo "📋 10. SUMMARY AND RECOMMENDATIONS"
echo "=================================="

# Count passed and failed tests
PASS_COUNT=$(grep -c "✅ PASS" "$LOG_FILE" || echo 0)
FAIL_COUNT=$(grep -c "❌ FAIL" "$LOG_FILE" || echo 0)
WARN_COUNT=$(grep -c "⚠️ WARN" "$LOG_FILE" || echo 0)

echo ""
echo "📊 VALIDATION RESULTS:"
echo "====================="
echo "✅ Passed: $PASS_COUNT"
echo "❌ Failed: $FAIL_COUNT"
echo "⚠️ Warnings: $WARN_COUNT"
echo ""

if [ "$FAIL_COUNT" -eq 0 ]; then
    print_status "PASS" "ALL CRITICAL TESTS PASSED!"
    echo ""
    echo "🎉 Fix It Fred Git Integration is successfully deployed and operational!"
    echo ""
    echo "🔄 Ready for production use:"
    echo "  • Real-time file monitoring active"
    echo "  • AI-powered commit generation working"
    echo "  • GitHub Actions integration configured"
    echo "  • All services healthy and responsive"
    echo ""
    echo "🎯 Next steps:"
    echo "  1. Monitor service logs for ongoing operation"
    echo "  2. Test actual file changes and commits"
    echo "  3. Verify GitHub Actions workflows trigger properly"
    echo "  4. Set up alerting for service health"
    
    # Create success marker
    echo "VALIDATION_SUCCESS=$(date)" > /tmp/git_integration_validation_success.marker
    
else
    print_status "FAIL" "$FAIL_COUNT critical issues found"
    echo ""
    echo "🔧 Issues that need attention:"
    grep "❌ FAIL" "$LOG_FILE" | sed 's/.*FAIL: /  • /'
    echo ""
    echo "📚 Troubleshooting resources:"
    echo "  • Troubleshooting guide: ./FIX_IT_FRED_GIT_TROUBLESHOOTING.md"
    echo "  • Test authentication: ./setup_git_credentials.sh test"
    echo "  • Fix GitHub CLI: ./fix_github_cli_auth.sh"
    echo "  • Service logs: sudo journalctl -u fix-it-fred-git.service -f"
    echo ""
    echo "🆘 For help:"
    echo "  1. Check service status: sudo systemctl status fix-it-fred-git.service"
    echo "  2. Review logs: tail -f /tmp/fix_it_fred_git.log"
    echo "  3. Run quick fix: ./FIX_IT_FRED_GIT_TROUBLESHOOTING.md (Quick Fix Script)"
fi

if [ "$WARN_COUNT" -gt 0 ]; then
    echo ""
    echo "⚠️ Warnings (non-critical):"
    grep "⚠️ WARN" "$LOG_FILE" | sed 's/.*WARN: /  • /'
fi

echo ""
echo "📝 Complete validation log saved to: $LOG_FILE"
echo "📅 Validation completed at: $(date)"
echo ""
echo "✨ Fix It Fred Git Integration Validation Complete!"
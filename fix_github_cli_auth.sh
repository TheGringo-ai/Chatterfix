#!/bin/bash
# Fix GitHub CLI Authentication Conflicts
# Resolves conflicts between GitHub CLI and repository secrets

set -e

echo "🔧 Fixing GitHub CLI Authentication Conflicts"
echo "============================================="
echo ""

# Configuration
VM_DIR="/home/yoyofred_gringosgambit_com/chatterfix-docker"
CONFIG_DIR="$HOME/.config/gh"

# Function to check GitHub CLI status
check_gh_status() {
    echo "🔍 Checking GitHub CLI status..."
    
    if command -v gh &> /dev/null; then
        echo "✅ GitHub CLI is installed"
        
        # Check authentication status
        if gh auth status &> /dev/null; then
            echo "✅ GitHub CLI is authenticated"
            gh auth status
        else
            echo "⚠️ GitHub CLI is not authenticated"
        fi
    else
        echo "❌ GitHub CLI is not installed"
    fi
}

# Function to configure GitHub CLI for Fix It Fred
configure_gh_for_fred() {
    echo "⚙️ Configuring GitHub CLI for Fix It Fred..."
    
    # Create GitHub CLI config directory
    mkdir -p "$CONFIG_DIR"
    
    # Configure GitHub CLI to use git credentials instead of its own auth
    cat > "$CONFIG_DIR/config.yml" << 'EOF'
# GitHub CLI configuration for Fix It Fred
version: 1
git_protocol: ssh
editor: nano
prompt: enabled
pager: less
http_unix_socket: 
browser: 

# Use git's credential system instead of gh auth
aliases:
    co: pr checkout
    pv: pr view

# Disable automatic authentication
oauth_token: ""
EOF
    
    echo "✅ GitHub CLI configured to use git credentials"
}

# Function to create GitHub CLI wrapper for Fix It Fred
create_gh_wrapper() {
    echo "🤖 Creating GitHub CLI wrapper for Fix It Fred..."
    
    # Create wrapper script
    cat > "$VM_DIR/gh_fred_wrapper.sh" << 'EOF'
#!/bin/bash
# GitHub CLI wrapper for Fix It Fred
# Uses git credentials instead of gh auth

# Check if command requires authentication
if [[ "$*" =~ (pr create|issue create|release create|repo create) ]]; then
    echo "🔐 Using git credentials for GitHub operation..."
    
    # Use git-based operations instead of gh
    case "$1" in
        "pr")
            if [ "$2" = "create" ]; then
                echo "📝 Creating pull request via git push..."
                # Create branch and push
                BRANCH="fix-it-fred-$(date +%s)"
                git checkout -b "$BRANCH"
                git push -u origin "$BRANCH"
                echo "✅ Branch pushed: $BRANCH"
                echo "🔗 Create PR manually at: https://github.com/$(git remote get-url origin | sed 's|.*github.com[/:]||; s|\.git||')/compare/$BRANCH"
            fi
            ;;
        *)
            echo "⚠️ Operation not supported in Fix It Fred mode"
            echo "💡 Use git commands directly or configure proper GitHub authentication"
            ;;
    esac
else
    # For read-only operations, use gh directly
    command gh "$@"
fi
EOF
    
    chmod +x "$VM_DIR/gh_fred_wrapper.sh"
    echo "✅ GitHub CLI wrapper created"
}

# Function to configure git for GitHub operations
configure_git_for_github() {
    echo "📝 Configuring git for GitHub operations..."
    
    cd "$VM_DIR"
    
    # Configure git to work well with GitHub
    git config --local hub.protocol ssh
    git config --local github.user "fix-it-fred-ai"
    
    # Configure push behavior
    git config --local push.default simple
    git config --local push.autoSetupRemote true
    
    # Configure pull behavior
    git config --local pull.rebase false
    
    echo "✅ Git configured for GitHub operations"
}

# Function to create authentication test script
create_auth_test() {
    echo "🧪 Creating authentication test script..."
    
    cat > "$VM_DIR/test_github_auth.sh" << 'EOF'
#!/bin/bash
# Test GitHub authentication for Fix It Fred

echo "🧪 Testing GitHub Authentication"
echo "==============================="

# Test git access
echo "📝 Testing git access..."
if git ls-remote origin > /dev/null 2>&1; then
    echo "✅ Git can access remote repository"
else
    echo "❌ Git cannot access remote repository"
    echo "💡 Run: ./setup_git_credentials.sh"
fi

# Test GitHub CLI (read operations)
echo ""
echo "📊 Testing GitHub CLI (read operations)..."
if gh repo view > /dev/null 2>&1; then
    echo "✅ GitHub CLI can read repository info"
else
    echo "⚠️ GitHub CLI read operations not working"
    echo "💡 This is expected if gh auth is not configured"
fi

# Test repository write access
echo ""
echo "✏️ Testing repository write access..."
TEST_BRANCH="auth-test-$(date +%s)"
git checkout -b "$TEST_BRANCH" > /dev/null 2>&1
echo "# Auth test $(date)" > auth_test.tmp

if git add auth_test.tmp && git commit -m "Test commit" > /dev/null 2>&1; then
    echo "✅ Can create commits"
    
    if git push -u origin "$TEST_BRANCH" > /dev/null 2>&1; then
        echo "✅ Can push to remote repository"
        
        # Cleanup
        git checkout main > /dev/null 2>&1
        git branch -D "$TEST_BRANCH" > /dev/null 2>&1
        git push origin --delete "$TEST_BRANCH" > /dev/null 2>&1
        rm -f auth_test.tmp
        echo "✅ Cleanup completed"
    else
        echo "❌ Cannot push to remote repository"
    fi
else
    echo "❌ Cannot create commits"
fi

echo ""
echo "✅ Authentication test complete"
EOF
    
    chmod +x "$VM_DIR/test_github_auth.sh"
    echo "✅ Authentication test script created"
}

# Function to resolve common conflicts
resolve_conflicts() {
    echo "🔧 Resolving common authentication conflicts..."
    
    # Clear any conflicting environment variables
    unset GITHUB_TOKEN
    unset GH_TOKEN
    
    # Remove any gh auth tokens that might conflict
    if [ -f "$CONFIG_DIR/hosts.yml" ]; then
        echo "🧹 Backing up and clearing gh auth tokens..."
        mv "$CONFIG_DIR/hosts.yml" "$CONFIG_DIR/hosts.yml.backup.$(date +%s)"
    fi
    
    # Ensure git credentials take precedence
    git config --global credential.helper store
    
    echo "✅ Conflicts resolved"
}

# Function to create monitoring script
create_monitoring_script() {
    echo "📊 Creating authentication monitoring script..."
    
    cat > "$VM_DIR/monitor_github_auth.sh" << 'EOF'
#!/bin/bash
# Monitor GitHub authentication status for Fix It Fred

while true; do
    clear
    echo "📊 GitHub Authentication Monitor"
    echo "==============================="
    echo "🕐 $(date)"
    echo ""
    
    # Check git status
    echo "📝 Git Status:"
    if git ls-remote origin > /dev/null 2>&1; then
        echo "  ✅ Git authentication: Working"
    else
        echo "  ❌ Git authentication: Failed"
    fi
    
    # Check GitHub CLI
    echo ""
    echo "🔧 GitHub CLI Status:"
    if gh auth status > /dev/null 2>&1; then
        echo "  ✅ GitHub CLI: Authenticated"
    else
        echo "  ⚠️ GitHub CLI: Not authenticated (expected for Fix It Fred)"
    fi
    
    # Check Fix It Fred Git Integration Service
    echo ""
    echo "🤖 Fix It Fred Services:"
    if curl -s http://localhost:9002/health | grep -q "healthy"; then
        echo "  ✅ Git Integration Service: Healthy"
    else
        echo "  ❌ Git Integration Service: Unhealthy"
    fi
    
    if curl -s http://localhost:9000/health | grep -q "healthy"; then
        echo "  ✅ AI Service: Healthy"
    else
        echo "  ❌ AI Service: Unhealthy"
    fi
    
    echo ""
    echo "Press Ctrl+C to exit, or wait 30 seconds for refresh..."
    sleep 30
done
EOF
    
    chmod +x "$VM_DIR/monitor_github_auth.sh"
    echo "✅ Authentication monitoring script created"
}

# Main execution
main() {
    echo "🚀 Starting GitHub CLI authentication fix..."
    echo ""
    
    # Check current status
    check_gh_status
    echo ""
    
    # Configure GitHub CLI
    configure_gh_for_fred
    echo ""
    
    # Create wrapper
    create_gh_wrapper
    echo ""
    
    # Configure git
    configure_git_for_github
    echo ""
    
    # Create test script
    create_auth_test
    echo ""
    
    # Resolve conflicts
    resolve_conflicts
    echo ""
    
    # Create monitoring script
    create_monitoring_script
    echo ""
    
    echo "✅ GitHub CLI authentication fix complete!"
    echo ""
    echo "📋 Summary of changes:"
    echo "  ✅ GitHub CLI configured to use git credentials"
    echo "  ✅ Created GitHub CLI wrapper for Fix It Fred"
    echo "  ✅ Configured git for GitHub operations"
    echo "  ✅ Created authentication test script"
    echo "  ✅ Resolved authentication conflicts"
    echo "  ✅ Created monitoring script"
    echo ""
    echo "🔄 Next steps:"
    echo "  1. Test authentication: ./test_github_auth.sh"
    echo "  2. Monitor status: ./monitor_github_auth.sh"
    echo "  3. Use git commands directly for Fix It Fred operations"
    echo "  4. Avoid using 'gh auth' commands on the VM"
    echo ""
    echo "💡 For Fix It Fred Git Integration:"
    echo "  • Use git commands for all repository operations"
    echo "  • GitHub Actions workflows handle deployment"
    echo "  • No GitHub token needed on VM"
    echo "  • All authentication via SSH keys or git credentials"
}

# Command line interface
if [ "$#" -eq 0 ]; then
    main
else
    case "$1" in
        check)
            check_gh_status
            ;;
        configure)
            configure_gh_for_fred
            ;;
        test)
            cd "$VM_DIR" && ./test_github_auth.sh
            ;;
        monitor)
            cd "$VM_DIR" && ./monitor_github_auth.sh
            ;;
        resolve)
            resolve_conflicts
            ;;
        *)
            echo "Usage: $0 [check|configure|test|monitor|resolve]"
            echo ""
            echo "Commands:"
            echo "  check     - Check current GitHub CLI status"
            echo "  configure - Configure GitHub CLI for Fix It Fred"
            echo "  test      - Test authentication"
            echo "  monitor   - Monitor authentication status"
            echo "  resolve   - Resolve authentication conflicts"
            echo ""
            echo "Run without arguments for complete setup"
            ;;
    esac
fi
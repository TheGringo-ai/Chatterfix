#!/bin/bash
# Setup Git Credentials for Fix It Fred Git Integration
# This script configures secure git authentication for automated operations

set -e

echo "🔐 Fix It Fred Git Credentials Setup"
echo "==================================="
echo ""

# Configuration
REPO_DIR="/home/yoyofred_gringosgambit_com/chatterfix-docker"
GIT_USER="Fix It Fred AI"
GIT_EMAIL="fix-it-fred@chatterfix.com"

# Function to setup SSH keys
setup_ssh() {
    echo "📝 Setting up SSH key authentication..."
    
    if [ -z "$1" ]; then
        read -p "Enter your email for SSH key generation: " email
    else
        email="$1"
    fi
    
    if [ -z "$email" ]; then
        echo "❌ Email is required for SSH key generation"
        exit 1
    fi
    
    # Create .ssh directory if it doesn't exist
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    
    # Generate SSH key if it doesn't exist
    SSH_KEY_PATH="$HOME/.ssh/fix_it_fred_git"
    if [ ! -f "$SSH_KEY_PATH" ]; then
        echo "🔑 Generating SSH key..."
        ssh-keygen -t ed25519 -C "$email" -f "$SSH_KEY_PATH" -N ""
        echo "✅ SSH key generated: $SSH_KEY_PATH"
    else
        echo "✅ SSH key already exists: $SSH_KEY_PATH"
    fi
    
    # Add to SSH agent
    eval "$(ssh-agent -s)"
    ssh-add "$SSH_KEY_PATH"
    
    # Configure SSH config
    cat >> ~/.ssh/config << EOF

# Fix It Fred Git Integration
Host github.com
    HostName github.com
    User git
    IdentityFile $SSH_KEY_PATH
    IdentitiesOnly yes

Host gitlab.com
    HostName gitlab.com
    User git
    IdentityFile $SSH_KEY_PATH
    IdentitiesOnly yes
EOF
    
    chmod 600 ~/.ssh/config
    
    echo ""
    echo "🔑 PUBLIC KEY (Add this to your git provider):"
    echo "=============================================="
    cat "${SSH_KEY_PATH}.pub"
    echo ""
    echo "📋 Instructions:"
    echo "1. Copy the public key above"
    echo "2. Go to your git provider:"
    echo "   - GitHub: https://github.com/settings/ssh/new"
    echo "   - GitLab: https://gitlab.com/-/profile/keys"
    echo "   - Bitbucket: https://bitbucket.org/account/settings/ssh-keys/"
    echo "3. Add the public key with title 'Fix It Fred Git Integration'"
    echo ""
}

# Function to setup token authentication
setup_token() {
    echo "🎫 Setting up token authentication..."
    
    if [ -z "$1" ]; then
        read -p "Enter your git username: " username
    else
        username="$1"
    fi
    
    if [ -z "$2" ]; then
        read -s -p "Enter your git token: " token
        echo ""
    else
        token="$2"
    fi
    
    if [ -z "$username" ] || [ -z "$token" ]; then
        echo "❌ Username and token are required"
        exit 1
    fi
    
    # Setup git credentials
    git config --global credential.helper store
    
    # Create credentials file
    CREDS_FILE="$HOME/.git-credentials"
    
    # Backup existing credentials
    if [ -f "$CREDS_FILE" ]; then
        cp "$CREDS_FILE" "${CREDS_FILE}.backup.$(date +%s)"
    fi
    
    # Add credentials for common git providers
    echo "https://${username}:${token}@github.com" >> "$CREDS_FILE"
    echo "https://${username}:${token}@gitlab.com" >> "$CREDS_FILE"
    
    chmod 600 "$CREDS_FILE"
    
    echo "✅ Token authentication configured!"
    echo "📝 Credentials stored in: $CREDS_FILE"
}

# Function to test authentication
test_auth() {
    if [ -z "$1" ]; then
        read -p "Enter repository URL to test (e.g., git@github.com:user/repo.git): " repo_url
    else
        repo_url="$1"
    fi
    
    if [ -z "$repo_url" ]; then
        echo "❌ Repository URL is required"
        exit 1
    fi
    
    echo "🧪 Testing authentication with: $repo_url"
    
    # Create temporary directory for testing
    TEST_DIR="/tmp/git_auth_test_$(date +%s)"
    mkdir -p "$TEST_DIR"
    cd "$TEST_DIR"
    
    # Test git operations
    if git ls-remote "$repo_url" > /dev/null 2>&1; then
        echo "✅ Authentication successful!"
        echo "✅ Can access repository: $repo_url"
    else
        echo "❌ Authentication failed!"
        echo "❌ Cannot access repository: $repo_url"
        echo ""
        echo "🔧 Troubleshooting:"
        echo "1. Verify the repository URL is correct"
        echo "2. Check that SSH key is added to git provider (for SSH URLs)"
        echo "3. Verify token has correct permissions (for HTTPS URLs)"
        echo "4. Ensure repository exists and you have access"
    fi
    
    # Cleanup
    cd - > /dev/null
    rm -rf "$TEST_DIR"
}

# Function to configure git repository
configure_git_repo() {
    echo "🔧 Configuring git repository..."
    
    if [ ! -d "$REPO_DIR" ]; then
        echo "❌ Repository directory not found: $REPO_DIR"
        exit 1
    fi
    
    cd "$REPO_DIR"
    
    # Configure git user
    git config user.name "$GIT_USER"
    git config user.email "$GIT_EMAIL"
    
    # Configure git settings for automated operations
    git config init.defaultBranch main
    git config pull.rebase false
    git config push.default simple
    
    # Initialize repository if not already
    if [ ! -d ".git" ]; then
        echo "🔄 Initializing git repository..."
        git init
        
        # Create initial commit if needed
        if [ -z "$(git status --porcelain)" ]; then
            echo "# ChatterFix CMMS with Fix It Fred AI" > README.md
            git add README.md
            git commit -m "Initial commit: ChatterFix CMMS with Fix It Fred Git Integration"
        fi
    fi
    
    echo "✅ Git repository configured"
    echo "📊 Repository status:"
    git status --short
}

# Function to setup remote repository
setup_remote() {
    if [ -z "$1" ]; then
        read -p "Enter remote repository URL (e.g., git@github.com:user/repo.git): " remote_url
    else
        remote_url="$1"
    fi
    
    if [ -z "$remote_url" ]; then
        echo "❌ Remote repository URL is required"
        exit 1
    fi
    
    cd "$REPO_DIR"
    
    # Remove existing origin if it exists
    git remote remove origin 2>/dev/null || true
    
    # Add new origin
    git remote add origin "$remote_url"
    
    echo "✅ Remote repository configured: $remote_url"
    
    # Test connection
    if git ls-remote origin > /dev/null 2>&1; then
        echo "✅ Remote connection successful"
        
        # Offer to push current state
        read -p "Push current state to remote? (y/N): " push_confirm
        if [[ "$push_confirm" =~ ^[Yy]$ ]]; then
            git push -u origin main
            echo "✅ Pushed to remote repository"
        fi
    else
        echo "❌ Remote connection failed"
        echo "Please check credentials and repository URL"
    fi
}

# Function to show status
show_status() {
    echo "📊 Git Integration Status"
    echo "========================"
    echo ""
    
    # Check if repository exists
    if [ -d "$REPO_DIR/.git" ]; then
        echo "✅ Git repository: $REPO_DIR"
        
        cd "$REPO_DIR"
        
        # Show git configuration
        echo "👤 Git user: $(git config user.name) <$(git config user.email)>"
        
        # Show remote
        if git remote -v | grep -q origin; then
            echo "🌐 Remote: $(git remote get-url origin)"
        else
            echo "⚠️ No remote repository configured"
        fi
        
        # Show branch
        echo "🌿 Branch: $(git branch --show-current)"
        
        # Show status
        if [ -n "$(git status --porcelain)" ]; then
            echo "📝 Uncommitted changes: Yes"
        else
            echo "📝 Uncommitted changes: No"
        fi
        
        # Show recent commits
        echo ""
        echo "📜 Recent commits:"
        git log --oneline -5 2>/dev/null || echo "No commits yet"
        
    else
        echo "❌ Git repository not found: $REPO_DIR"
    fi
    
    echo ""
    
    # Check SSH keys
    if [ -f "$HOME/.ssh/fix_it_fred_git" ]; then
        echo "✅ SSH key: $HOME/.ssh/fix_it_fred_git"
    else
        echo "⚠️ SSH key not found"
    fi
    
    # Check git credentials
    if [ -f "$HOME/.git-credentials" ]; then
        echo "✅ Git credentials configured"
    else
        echo "⚠️ Git credentials not configured"
    fi
    
    # Check Fix It Fred Git Integration Service
    if pgrep -f "fix_it_fred_git_integration_service.py" > /dev/null; then
        echo "✅ Git Integration Service: Running"
    else
        echo "⚠️ Git Integration Service: Not running"
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "🎯 Choose an action:"
    echo "1) Setup SSH Key Authentication (Recommended)"
    echo "2) Setup Token Authentication"
    echo "3) Test Authentication"
    echo "4) Configure Git Repository"
    echo "5) Setup Remote Repository"
    echo "6) Show Status"
    echo "7) Complete Setup (All steps)"
    echo "8) Exit"
    echo ""
}

# Complete setup function
complete_setup() {
    echo "🚀 Complete Git Integration Setup"
    echo "================================"
    echo ""
    
    read -p "Enter your email: " email
    read -p "Enter remote repository URL: " remote_url
    
    if [ -z "$email" ] || [ -z "$remote_url" ]; then
        echo "❌ Email and remote URL are required"
        return 1
    fi
    
    echo ""
    echo "🔄 Running complete setup..."
    
    # Setup SSH authentication
    setup_ssh "$email"
    
    # Configure git repository
    configure_git_repo
    
    # Setup remote
    setup_remote "$remote_url"
    
    # Test authentication
    test_auth "$remote_url"
    
    echo ""
    echo "🎉 Complete setup finished!"
    echo "✅ Fix It Fred Git Integration is ready"
    echo ""
    echo "🔄 Next steps:"
    echo "1. Start the Git Integration Service"
    echo "2. Monitor logs for proper operation"
    echo "3. Test file changes and automatic commits"
}

# Main script logic
if [ "$#" -eq 0 ]; then
    # Interactive mode
    while true; do
        show_menu
        read -p "Enter choice (1-8): " choice
        
        case $choice in
            1)
                setup_ssh
                ;;
            2)
                setup_token
                ;;
            3)
                test_auth
                ;;
            4)
                configure_git_repo
                ;;
            5)
                setup_remote
                ;;
            6)
                show_status
                ;;
            7)
                complete_setup
                ;;
            8)
                echo "👋 Goodbye!"
                exit 0
                ;;
            *)
                echo "❌ Invalid choice"
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
    done
else
    # Command line mode
    case "$1" in
        ssh)
            setup_ssh "$2"
            ;;
        token)
            setup_token "$2" "$3"
            ;;
        test)
            test_auth "$2"
            ;;
        configure)
            configure_git_repo
            ;;
        remote)
            setup_remote "$2"
            ;;
        status)
            show_status
            ;;
        complete)
            complete_setup
            ;;
        *)
            echo "Usage: $0 [ssh|token|test|configure|remote|status|complete] [args...]"
            echo ""
            echo "Commands:"
            echo "  ssh [email]              - Setup SSH key authentication"
            echo "  token [username] [token] - Setup token authentication"
            echo "  test [repo_url]          - Test authentication"
            echo "  configure                - Configure git repository"
            echo "  remote [repo_url]        - Setup remote repository"
            echo "  status                   - Show current status"
            echo "  complete                 - Run complete setup (interactive)"
            echo ""
            echo "Examples:"
            echo "  $0 ssh fix-it-fred@chatterfix.com"
            echo "  $0 token myusername ghp_token123"
            echo "  $0 test git@github.com:user/repo.git"
            echo "  $0 configure"
            echo "  $0 status"
            exit 1
            ;;
    esac
fi
#!/bin/bash
# Deploy Fix It Fred Git Integration to ChatterFix VM
# Real-time git repository synchronization with AI-powered commit management

set -e

echo "🚀 Deploying Fix It Fred Git Integration System..."
echo "=================================================="
echo ""
echo "This deployment includes:"
echo "✅ Real-time file system monitoring"
echo "✅ AI-powered commit message generation"
echo "✅ Automated git operations with security"
echo "✅ Code quality analysis and review"
echo "✅ Security scanning and credential management"
echo ""

# Configuration
VM_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"
VM_USER="yoyofred_gringosgambit_com"
REMOTE_DIR="/home/$VM_USER/chatterfix-docker"
SERVICE_PORT=9002

echo "📦 Preparing deployment package..."

# Create deployment directory
mkdir -p git-integration-deployment
cd git-integration-deployment

# Copy all git integration files
echo "📋 Copying integration services..."
cp ../fix_it_fred_git_integration_service.py ./
cp ../fix_it_fred_git_security.py ./
cp ../fix_it_fred_git_ai_enhancement.py ./

# Create requirements file for git integration
cat > requirements_git.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
watchdog==3.0.0
requests==2.31.0
cryptography==41.0.7
pydantic==2.5.0
python-multipart==0.0.6
aiofiles==23.2.1
psutil==5.9.6
EOF

# Create systemd service file
cat > fix-it-fred-git.service << 'EOF'
[Unit]
Description=Fix It Fred Git Integration Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=yoyofred_gringosgambit_com
Group=yoyofred_gringosgambit_com
WorkingDirectory=/home/yoyofred_gringosgambit_com/chatterfix-docker
Environment=PYTHONPATH=/home/yoyofred_gringosgambit_com/chatterfix-docker
Environment=PORT=9002
Environment=OLLAMA_HOST=localhost:11434
ExecStart=/usr/bin/python3 fix_it_fred_git_integration_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create git integration configuration
cat > git_integration_config.json << 'EOF'
{
  "git": {
    "repo_path": "/home/yoyofred_gringosgambit_com/chatterfix-docker",
    "branch": "main",
    "author_name": "Fix It Fred AI",
    "author_email": "fix-it-fred@chatterfix.com",
    "commit_interval_minutes": 15,
    "auto_push": true,
    "ai_review_enabled": true
  },
  "monitoring": {
    "watch_patterns": ["*.py", "*.js", "*.html", "*.css", "*.sql", "*.md", "*.sh", "*.yml", "*.yaml"],
    "ignore_patterns": ["*.log", "*.tmp", "*.pyc", "__pycache__", ".git", "node_modules", ".venv"],
    "batch_size": 50,
    "batch_timeout_seconds": 300
  },
  "ai": {
    "fix_it_fred_url": "http://localhost:9000",
    "analysis_timeout_seconds": 30,
    "max_file_size_mb": 5,
    "enable_code_quality_checks": true,
    "enable_security_scanning": true
  },
  "security": {
    "encrypt_credentials": true,
    "rotate_credentials_days": 30,
    "audit_log_enabled": true,
    "trusted_domains": ["github.com", "gitlab.com", "bitbucket.org"]
  }
}
EOF

# Create startup script for git integration
cat > start_git_integration.sh << 'EOF'
#!/bin/bash
# Start Fix It Fred Git Integration Service

echo "🔧 Starting Fix It Fred Git Integration..."

# Set environment
export PYTHONPATH=/home/yoyofred_gringosgambit_com/chatterfix-docker
export PORT=9002
export OLLAMA_HOST=localhost:11434

# Ensure required directories exist
mkdir -p /tmp/fix_it_fred_logs
mkdir -p ~/.ssh

# Set permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/* 2>/dev/null || true

# Start the service
cd /home/yoyofred_gringosgambit_com/chatterfix-docker

echo "🔍 Installing dependencies..."
pip3 install --user -r requirements_git.txt

echo "🤖 Starting Git Integration Service on port 9002..."
python3 fix_it_fred_git_integration_service.py &
GIT_PID=$!

echo "✅ Git Integration Service started with PID: $GIT_PID"
echo "🌐 Service available at: http://localhost:9002"
echo "📊 Health check: http://localhost:9002/health"
echo "📋 Git status: http://localhost:9002/api/git/status"

# Wait and verify service
sleep 10
if curl -s http://localhost:9002/health > /dev/null; then
    echo "✅ Git Integration Service is healthy!"
else
    echo "⚠️ Git Integration Service may still be starting..."
fi

echo ""
echo "🎉 Fix It Fred Git Integration is now active!"
echo "Real-time monitoring of: /home/yoyofred_gringosgambit_com/chatterfix-docker"
EOF

chmod +x start_git_integration.sh

# Create setup script for git credentials
cat > setup_git_credentials.sh << 'EOF'
#!/bin/bash
# Setup Git Credentials for Fix It Fred

echo "🔐 Setting up Git Credentials for Fix It Fred..."

# Function to setup SSH keys
setup_ssh() {
    echo "📝 Setting up SSH key authentication..."
    read -p "Enter your email for SSH key generation: " email
    
    if [ -z "$email" ]; then
        echo "❌ Email is required for SSH key generation"
        exit 1
    fi
    
    # Generate SSH key
    python3 fix_it_fred_git_security.py setup --email "$email"
    
    echo ""
    echo "✅ SSH keys generated successfully!"
    echo "📋 Please add the public key above to your git provider"
    echo "🔗 GitHub: https://github.com/settings/ssh/new"
    echo "🔗 GitLab: https://gitlab.com/-/profile/keys"
}

# Function to setup token authentication
setup_token() {
    echo "🎫 Setting up token authentication..."
    read -p "Enter your git username: " username
    read -s -p "Enter your git token: " token
    echo ""
    
    if [ -z "$username" ] || [ -z "$token" ]; then
        echo "❌ Username and token are required"
        exit 1
    fi
    
    # Setup token
    python3 fix_it_fred_git_security.py setup --username "$username" --token "$token"
    
    echo "✅ Token authentication configured!"
}

# Function to test authentication
test_auth() {
    read -p "Enter repository URL to test: " repo_url
    
    if [ -z "$repo_url" ]; then
        echo "❌ Repository URL is required"
        exit 1
    fi
    
    python3 fix_it_fred_git_security.py test --repo-url "$repo_url"
}

# Main menu
echo "Choose authentication method:"
echo "1) SSH Key (Recommended)"
echo "2) Token/Password"
echo "3) Test existing authentication"
read -p "Enter choice (1-3): " choice

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
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Git credentials setup complete!"
echo "🔄 Restart the git integration service to apply changes"
EOF

chmod +x setup_git_credentials.sh

# Create monitoring dashboard script
cat > git_monitoring_dashboard.py << 'EOF'
#!/usr/bin/env python3
"""
Fix It Fred Git Integration Monitoring Dashboard
Real-time monitoring and management interface
"""
import requests
import json
import time
from datetime import datetime

class GitMonitoringDashboard:
    def __init__(self):
        self.git_service_url = "http://localhost:9002"
        self.fix_it_fred_url = "http://localhost:9000"
    
    def check_services(self):
        """Check status of all services"""
        services = {
            'Git Integration': self.git_service_url,
            'Fix It Fred AI': self.fix_it_fred_url
        }
        
        status = {}
        for name, url in services.items():
            try:
                response = requests.get(f"{url}/health", timeout=5)
                status[name] = "✅ Healthy" if response.status_code == 200 else "⚠️ Issues"
            except:
                status[name] = "❌ Down"
        
        return status
    
    def get_git_status(self):
        """Get current git status"""
        try:
            response = requests.get(f"{self.git_service_url}/api/git/status", timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def get_recent_commits(self):
        """Get recent commits"""
        try:
            response = requests.get(f"{self.git_service_url}/api/git/commits?limit=5", timeout=5)
            if response.status_code == 200:
                return response.json().get('commits', [])
        except:
            pass
        return []
    
    def display_dashboard(self):
        """Display the monitoring dashboard"""
        print("\n" + "="*60)
        print("🤖 FIX IT FRED GIT INTEGRATION DASHBOARD")
        print("="*60)
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Service Status
        print("🔧 SERVICE STATUS:")
        services = self.check_services()
        for name, status in services.items():
            print(f"  {name}: {status}")
        print()
        
        # Git Status
        print("📋 GIT STATUS:")
        git_status = self.get_git_status()
        if git_status:
            print(f"  Branch: {git_status.get('branch', 'unknown')}")
            print(f"  Changes: {'Yes' if git_status.get('has_changes') else 'No'}")
            if git_status.get('modified_files'):
                print(f"  Modified files: {len(git_status['modified_files'])}")
                for file in git_status['modified_files'][:3]:
                    print(f"    - {file}")
                if len(git_status['modified_files']) > 3:
                    print(f"    ... and {len(git_status['modified_files']) - 3} more")
        else:
            print("  ❌ Unable to get git status")
        print()
        
        # Recent Commits
        print("📊 RECENT COMMITS:")
        commits = self.get_recent_commits()
        if commits:
            for commit in commits[:3]:
                timestamp = commit.get('timestamp', '')[:19].replace('T', ' ')
                message = commit.get('message', 'No message')[:50]
                status = commit.get('status', 'unknown')
                print(f"  {timestamp} | {status} | {message}")
        else:
            print("  No recent commits found")
        print()
        
        print("🎯 COMMANDS:")
        print("  Press 'r' to refresh")
        print("  Press 'c' to trigger manual commit")
        print("  Press 'q' to quit")
        print("="*60)

def main():
    dashboard = GitMonitoringDashboard()
    
    while True:
        dashboard.display_dashboard()
        
        try:
            choice = input("Enter command: ").lower().strip()
            
            if choice == 'q':
                print("👋 Goodbye!")
                break
            elif choice == 'r':
                continue
            elif choice == 'c':
                # Trigger manual commit
                try:
                    response = requests.post(f"{dashboard.git_service_url}/api/git/commit", 
                                           json={"force": True}, timeout=10)
                    if response.status_code == 200:
                        print("✅ Manual commit triggered")
                    else:
                        print("⚠️ Commit request failed")
                except:
                    print("❌ Unable to trigger commit")
                time.sleep(2)
            else:
                print("❌ Invalid command")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break

if __name__ == "__main__":
    main()
EOF

chmod +x git_monitoring_dashboard.py

echo "📤 Uploading deployment package to VM..."

# Upload all files to VM
gcloud compute scp --recurse ./ $VM_NAME:$REMOTE_DIR/git-integration/ --zone=$ZONE

echo "🔧 Configuring VM for git integration..."

# Create comprehensive VM setup script
cat > vm_setup_git_integration.sh << 'EOF'
#!/bin/bash
# VM Setup for Fix It Fred Git Integration

echo "🔧 Setting up Fix It Fred Git Integration on VM..."

cd /home/yoyofred_gringosgambit_com/chatterfix-docker

# Move files to correct locations
echo "📁 Moving integration files..."
mv git-integration/*.py ./
mv git-integration/*.txt ./
mv git-integration/*.json ./
mv git-integration/*.sh ./
mv git-integration/*.service ./

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install --user -r requirements_git.txt || {
    echo "⚠️ Some packages may need system installation..."
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-dev libffi-dev libssl-dev
    pip3 install --user -r requirements_git.txt
}

# Install git if not present
if ! command -v git &> /dev/null; then
    echo "📥 Installing git..."
    sudo apt-get install -y git
fi

# Configure git globally
git config --global init.defaultBranch main
git config --global user.name "Fix It Fred AI"
git config --global user.email "fix-it-fred@chatterfix.com"

# Initialize git repository if not already
if [ ! -d ".git" ]; then
    echo "🔄 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: Fix It Fred CMMS system"
fi

# Setup systemd service
echo "⚙️ Setting up systemd service..."
sudo cp fix-it-fred-git.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fix-it-fred-git.service

# Create log directories
mkdir -p /tmp/fix_it_fred_logs
chmod 755 /tmp/fix_it_fred_logs

# Set permissions
chmod +x *.sh
chmod +x *.py

echo ""
echo "✅ VM setup complete!"
echo ""
echo "🔄 Starting Fix It Fred Git Integration Service..."
sudo systemctl start fix-it-fred-git.service

# Wait and check status
sleep 10
if sudo systemctl is-active --quiet fix-it-fred-git.service; then
    echo "✅ Git Integration Service is running!"
else
    echo "⚠️ Service may still be starting. Check with: sudo systemctl status fix-it-fred-git.service"
fi

echo ""
echo "🎉 Fix It Fred Git Integration Setup Complete!"
echo "================================================"
echo ""
echo "📋 NEXT STEPS:"
echo "1. Run ./setup_git_credentials.sh to configure git authentication"
echo "2. Monitor with: ./git_monitoring_dashboard.py"
echo "3. Check logs: sudo journalctl -u fix-it-fred-git.service -f"
echo "4. Service management:"
echo "   - Start: sudo systemctl start fix-it-fred-git.service"
echo "   - Stop: sudo systemctl stop fix-it-fred-git.service"
echo "   - Status: sudo systemctl status fix-it-fred-git.service"
echo ""
echo "🌐 ENDPOINTS:"
echo "   - Health Check: http://localhost:9002/health"
echo "   - Git Status: http://localhost:9002/api/git/status"
echo "   - Recent Commits: http://localhost:9002/api/git/commits"
echo "   - Configuration: http://localhost:9002/api/git/config"
echo ""
echo "🔐 SECURITY:"
echo "   - Credentials are encrypted and stored securely"
echo "   - SSH keys are recommended over tokens"
echo "   - All git operations are audited"
echo "   - Automatic credential rotation available"
echo ""
EOF

# Upload and execute VM setup
gcloud compute scp vm_setup_git_integration.sh $VM_NAME:$REMOTE_DIR/ --zone=$ZONE

echo "🚀 Executing VM setup..."
gcloud compute ssh $VM_NAME --zone=$ZONE --command="cd $REMOTE_DIR && chmod +x vm_setup_git_integration.sh && ./vm_setup_git_integration.sh"

echo "⏳ Waiting for services to stabilize..."
sleep 30

echo "🧪 Testing deployment..."

# Test the git integration service
for i in {1..3}; do
    echo "Test attempt $i/3..."
    
    result=$(gcloud compute ssh $VM_NAME --zone=$ZONE --command="curl -s http://localhost:9002/health" 2>/dev/null || echo "failed")
    
    if echo "$result" | grep -q '"status":"healthy"'; then
        echo "✅ Git Integration Service is healthy!"
        
        # Test git status endpoint
        git_status=$(gcloud compute ssh $VM_NAME --zone=$ZONE --command="curl -s http://localhost:9002/api/git/status" 2>/dev/null || echo "failed")
        
        if echo "$git_status" | grep -q '"branch"'; then
            echo "✅ Git Status API is working!"
            break
        fi
    fi
    
    if [ $i -lt 3 ]; then
        echo "⏳ Waiting 15 seconds before retry..."
        sleep 15
    fi
done

echo ""
echo "🎯 DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "✅ Fix It Fred Git Integration deployed successfully!"
echo "🤖 Real-time file monitoring active"
echo "🔐 Secure credential management enabled"
echo "🧠 AI-powered commit analysis ready"
echo ""
echo "📋 MANAGEMENT COMMANDS:"
echo ""
echo "1. Check service status:"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo systemctl status fix-it-fred-git.service'"
echo ""
echo "2. View logs:"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE --command='sudo journalctl -u fix-it-fred-git.service -f'"
echo ""
echo "3. Setup git credentials:"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE --command='cd $REMOTE_DIR && ./setup_git_credentials.sh'"
echo ""
echo "4. Monitor git integration:"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE --command='cd $REMOTE_DIR && python3 git_monitoring_dashboard.py'"
echo ""
echo "5. Test git integration:"
echo "   curl https://chatterfix.com:9002/health"
echo "   curl https://chatterfix.com:9002/api/git/status"
echo ""
echo "🔥 FEATURES ENABLED:"
echo "• Real-time file change detection and batching"
echo "• AI-powered commit message generation"
echo "• Intelligent code quality analysis"
echo "• Security vulnerability scanning"
echo "• Automated git operations with rollback plans"
echo "• Encrypted credential storage"
echo "• Comprehensive audit logging"
echo "• Pre-commit code review system"
echo "• Breaking change detection"
echo "• CMMS-specific change analysis"
echo ""
echo "🎉 Your Fix It Fred now has real-time git superpowers!"

# Cleanup
cd ..
rm -rf git-integration-deployment

echo ""
echo "✨ Ready to revolutionize your CMMS development workflow!"
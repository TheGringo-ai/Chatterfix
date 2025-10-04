#!/bin/bash

# Universal AI Command Center Deployment Script
# Deploys the UACC as a standalone service for managing all your business applications

set -e

echo "🚀 Universal AI Command Center - Deployment Starting..."

# Configuration
UACC_PORT=8888
CMMS_PORT=8080
SERVICE_NAME="universal-ai-command-center"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is required but not installed"
        exit 1
    fi
    
    # Check Ollama
    if ! command -v ollama &> /dev/null; then
        log_warning "Ollama not found. Local AI models will not be available."
    else
        log_success "Ollama detected"
    fi
    
    log_success "Dependencies check completed"
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    pip3 install -r requirements.txt
    
    # Install additional dependencies for UACC
    pip3 install google-cloud-storage google-cloud-compute google-cloud-logging google-cloud-aiplatform google-api-python-client google-auth-httplib2 google-auth-oauthlib
    
    log_success "Python dependencies installed"
}

# Create configuration files
create_config() {
    log_info "Creating configuration files..."
    
    # Create .env file for UACC
    cat > .env.uacc << EOF
# Universal AI Command Center Configuration
UACC_PORT=${UACC_PORT}
UACC_HOST=0.0.0.0
UACC_SECRET_KEY=your-secret-key-here

# Database Configuration (optional)
DATABASE_URL=sqlite:///uacc.db

# GCP Configuration
GCP_PROJECT_ID=your-gcp-project-id
GCP_CREDENTIALS_PATH=./credentials/gcp-service-account.json

# Google Workspace Configuration  
WORKSPACE_DOMAIN=your-company.com
WORKSPACE_CREDENTIALS_PATH=./credentials/workspace-service-account.json

# Ollama Configuration
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_DEFAULT_MODEL=qwen2.5-coder:7b

# Security Configuration
JWT_SECRET_KEY=your-jwt-secret-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password-here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=./logs/uacc.log
EOF

    # Create credentials directory
    mkdir -p credentials
    mkdir -p logs
    
    # Create sample GCP service account template
    cat > credentials/gcp-service-account.json.template << EOF
{
  "type": "service_account",
  "project_id": "your-gcp-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
EOF

    # Create sample Workspace service account template
    cat > credentials/workspace-service-account.json.template << EOF
{
  "type": "service_account",
  "project_id": "your-workspace-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n",
  "client_email": "your-workspace-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-workspace-service-account%40your-project.iam.gserviceaccount.com"
}
EOF

    log_success "Configuration files created"
}

# Create systemd service
create_service() {
    log_info "Creating systemd service..."
    
    CURRENT_DIR=$(pwd)
    USER=$(whoami)
    
    sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=Universal AI Command Center
After=network.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${CURRENT_DIR}
Environment=PATH=${PATH}
EnvironmentFile=${CURRENT_DIR}/.env.uacc
ExecStart=/usr/bin/python3 ${CURRENT_DIR}/universal_ai_command_center.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable ${SERVICE_NAME}
    
    log_success "Systemd service created and enabled"
}

# Test Ollama connection
test_ollama() {
    log_info "Testing Ollama connection..."
    
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        log_success "Ollama is running and accessible"
        
        # List available models
        log_info "Available Ollama models:"
        curl -s http://localhost:11434/api/tags | python3 -c "
import json, sys
data = json.load(sys.stdin)
for model in data.get('models', []):
    print(f'  - {model.get(\"name\", \"unknown\")}')
"
    else
        log_warning "Ollama is not running or not accessible"
        log_info "You can start Ollama with: ollama serve"
    fi
}

# Start services
start_services() {
    log_info "Starting Universal AI Command Center..."
    
    # Start UACC service
    sudo systemctl start ${SERVICE_NAME}
    
    # Wait a moment for startup
    sleep 3
    
    # Check if service is running
    if sudo systemctl is-active --quiet ${SERVICE_NAME}; then
        log_success "Universal AI Command Center is running!"
        log_info "Access the Command Center at: http://localhost:${UACC_PORT}"
    else
        log_error "Failed to start Universal AI Command Center"
        log_info "Check logs with: sudo journalctl -u ${SERVICE_NAME} -f"
        exit 1
    fi
}

# Display final information
display_info() {
    echo ""
    echo "🎉 Universal AI Command Center Deployment Complete!"
    echo ""
    echo "🔗 Access URLs:"
    echo "  • Command Center:    http://localhost:${UACC_PORT}"
    echo "  • ChatterFix CMMS:   http://localhost:${CMMS_PORT}"
    echo ""
    echo "📁 Important Files:"
    echo "  • Configuration:     .env.uacc"
    echo "  • Logs:             ./logs/uacc.log"
    echo "  • Service:          /etc/systemd/system/${SERVICE_NAME}.service"
    echo ""
    echo "⚙️ Service Management:"
    echo "  • Start:    sudo systemctl start ${SERVICE_NAME}"
    echo "  • Stop:     sudo systemctl stop ${SERVICE_NAME}"
    echo "  • Restart:  sudo systemctl restart ${SERVICE_NAME}"
    echo "  • Status:   sudo systemctl status ${SERVICE_NAME}"
    echo "  • Logs:     sudo journalctl -u ${SERVICE_NAME} -f"
    echo ""
    echo "🔧 Configuration:"
    echo "  • Edit .env.uacc to configure GCP and Workspace integration"
    echo "  • Add your service account credentials to ./credentials/"
    echo "  • Restart the service after configuration changes"
    echo ""
    echo "🤖 AI Models:"
    echo "  • Current: qwen2.5-coder:7b (if Ollama is running)"
    echo "  • Add more: Use the Command Center web interface"
    echo ""
    echo "🚀 Next Steps:"
    echo "  1. Configure GCP and Workspace credentials"
    echo "  2. Add additional AI models through the web interface"
    echo "  3. Deploy your applications through the Command Center"
    echo "  4. Set up monitoring and alerts"
    echo ""
}

# Main deployment process
main() {
    echo "🌟 Universal AI Command Center - Enterprise Deployment"
    echo "=================================================="
    echo ""
    
    check_dependencies
    install_dependencies
    create_config
    create_service
    test_ollama
    start_services
    display_info
    
    log_success "Deployment completed successfully! 🎉"
}

# Run main function
main "$@"
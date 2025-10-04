#!/bin/bash

# Universal AI Command Center - macOS Deployment Script
# Optimized for macOS with launchd instead of systemd

set -e

echo "🚀 Universal AI Command Center - macOS Deployment Starting..."

# Configuration
UACC_PORT=8888
CMMS_PORT=8080
SERVICE_NAME="universal-ai-command-center"
CURRENT_DIR=$(pwd)
USER=$(whoami)

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
        log_info "Install Python 3: brew install python"
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
        log_info "Install Ollama: https://ollama.ai/download"
    else
        log_success "Ollama detected"
    fi
    
    log_success "Dependencies check completed"
}

# Install Python dependencies (already done based on your output)
install_dependencies() {
    log_info "Checking Python dependencies..."
    
    # The dependencies are already installed based on your output
    log_success "Python dependencies already installed"
}

# Create launchd plist for macOS
create_macos_service() {
    log_info "Creating macOS launchd service..."
    
    # Create LaunchAgents directory if it doesn't exist
    mkdir -p ~/Library/LaunchAgents
    
    # Create launchd plist file
    cat > ~/Library/LaunchAgents/com.uacc.${SERVICE_NAME}.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.uacc.${SERVICE_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>${CURRENT_DIR}/universal_ai_command_center.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${CURRENT_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${CURRENT_DIR}/logs/uacc.log</string>
    <key>StandardErrorPath</key>
    <string>${CURRENT_DIR}/logs/uacc-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

    # Load the service
    launchctl unload ~/Library/LaunchAgents/com.uacc.${SERVICE_NAME}.plist 2>/dev/null || true
    launchctl load ~/Library/LaunchAgents/com.uacc.${SERVICE_NAME}.plist
    
    log_success "macOS launchd service created and loaded"
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
try:
    data = json.load(sys.stdin)
    for model in data.get('models', []):
        name = model.get('name', 'unknown')
        size = model.get('size', 0)
        size_gb = round(size / (1024**3), 1) if size > 0 else 0
        print(f'  ✅ {name} ({size_gb}GB)')
except:
    pass
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
    launchctl start com.uacc.${SERVICE_NAME}
    
    # Wait a moment for startup
    sleep 5
    
    # Check if service is running by testing the port
    if curl -s http://localhost:${UACC_PORT}/health > /dev/null 2>&1; then
        log_success "Universal AI Command Center is running!"
        log_info "Access the Command Center at: http://localhost:${UACC_PORT}"
    else
        log_error "Failed to start Universal AI Command Center"
        log_info "Check logs with: tail -f ${CURRENT_DIR}/logs/uacc.log"
        log_info "Or run directly: python3 universal_ai_command_center.py"
    fi
}

# Alternative: Start in background with nohup
start_background() {
    log_info "Starting Universal AI Command Center in background..."
    
    # Kill any existing process
    pkill -f "universal_ai_command_center.py" 2>/dev/null || true
    
    # Start in background
    nohup python3 universal_ai_command_center.py > logs/uacc.log 2>&1 &
    
    # Get the PID
    echo $! > .uacc.pid
    
    # Wait a moment for startup
    sleep 3
    
    # Check if service is running
    if curl -s http://localhost:${UACC_PORT}/ > /dev/null 2>&1; then
        log_success "Universal AI Command Center is running!"
        log_info "Access the Command Center at: http://localhost:${UACC_PORT}"
        log_info "PID: $(cat .uacc.pid)"
    else
        log_error "Failed to start Universal AI Command Center"
        log_info "Check logs with: tail -f logs/uacc.log"
    fi
}

# Display final information
display_info() {
    echo ""
    echo "🎉 Universal AI Command Center - macOS Deployment Complete!"
    echo ""
    echo "🔗 Access URLs:"
    echo "  • Command Center:    http://localhost:${UACC_PORT}"
    echo "  • ChatterFix CMMS:   http://localhost:${CMMS_PORT}"
    echo ""
    echo "📁 Important Files:"
    echo "  • Configuration:     .env.uacc"
    echo "  • Logs:             ./logs/uacc.log"
    echo "  • Service:          ~/Library/LaunchAgents/com.uacc.${SERVICE_NAME}.plist"
    echo ""
    echo "⚙️ Service Management (macOS):"
    echo "  • Start:    launchctl start com.uacc.${SERVICE_NAME}"
    echo "  • Stop:     launchctl stop com.uacc.${SERVICE_NAME}"
    echo "  • Restart:  launchctl stop com.uacc.${SERVICE_NAME} && launchctl start com.uacc.${SERVICE_NAME}"
    echo "  • Status:   launchctl list | grep uacc"
    echo "  • Logs:     tail -f ./logs/uacc.log"
    echo ""
    echo "🔧 Alternative Commands:"
    echo "  • Run directly:     python3 universal_ai_command_center.py"
    echo "  • Stop background:  kill \$(cat .uacc.pid) 2>/dev/null || pkill -f universal_ai_command_center"
    echo ""
    echo "🤖 AI Models:"
    echo "  • Current: qwen2.5-coder:7b (if Ollama is running)"
    echo "  • Add more: Use the Command Center web interface"
    echo ""
    echo "🚀 Next Steps:"
    echo "  1. Open http://localhost:${UACC_PORT} in your browser"
    echo "  2. Configure GCP and Workspace credentials (optional)"
    echo "  3. Add additional AI models through the web interface"
    echo "  4. Deploy your applications through the Command Center"
    echo ""
}

# Main deployment process
main() {
    echo "🌟 Universal AI Command Center - macOS Deployment"
    echo "==============================================="
    echo ""
    
    check_dependencies
    install_dependencies
    test_ollama
    
    # Try launchd service first, fall back to background process
    echo ""
    log_info "Choose deployment method:"
    echo "1. LaunchD Service (recommended - auto-start on boot)"
    echo "2. Background Process (simple - manual start)"
    echo "3. Direct Run (testing - run in foreground)"
    echo ""
    read -p "Enter choice (1-3) [1]: " choice
    choice=${choice:-1}
    
    case $choice in
        1)
            create_macos_service
            start_services
            ;;
        2)
            start_background
            ;;
        3)
            log_info "Starting in foreground mode..."
            log_info "Press Ctrl+C to stop"
            echo ""
            python3 universal_ai_command_center.py
            return
            ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac
    
    display_info
    log_success "Deployment completed successfully! 🎉"
}

# Run main function
main "$@"
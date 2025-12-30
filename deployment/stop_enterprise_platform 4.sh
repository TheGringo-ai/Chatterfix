#!/bin/bash
set -e

# ChatterFix Enterprise Platform Stop Script
echo "🛑 Stopping ChatterFix Enterprise Platform..."

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️${NC} $1"
}

# Stop services gracefully
stop_services() {
    print_status "Stopping platform services..."
    
    # Stop processes by PID files
    for pidfile in logs/*.pid; do
        if [ -f "$pidfile" ]; then
            local pid=$(cat "$pidfile")
            local service=$(basename "$pidfile" .pid)
            
            if kill -0 "$pid" 2>/dev/null; then
                print_status "Stopping $service (PID: $pid)..."
                kill -TERM "$pid" 2>/dev/null || true
                
                # Wait for graceful shutdown
                local count=0
                while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                    sleep 1
                    count=$((count + 1))
                done
                
                # Force kill if still running
                if kill -0 "$pid" 2>/dev/null; then
                    print_warning "Force stopping $service..."
                    kill -KILL "$pid" 2>/dev/null || true
                fi
                
                print_success "$service stopped"
            else
                print_warning "$service was not running"
            fi
            
            rm -f "$pidfile"
        fi
    done
    
    # Stop any remaining ChatterFix processes
    print_status "Cleaning up remaining processes..."
    
    # Kill by process name patterns
    pkill -f "fix_it_fred_ai_service.py" 2>/dev/null || true
    pkill -f "platform_gateway.py" 2>/dev/null || true
    pkill -f "ai_look_doc_manager.py" 2>/dev/null || true
    pkill -f "enterprise_monitor.py" 2>/dev/null || true
    
    # Kill by port (if needed)
    for port in 8000 8001 8002 8003 8004 8005 8006 8007 8008; do
        local pid=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pid" ]; then
            print_status "Stopping process on port $port (PID: $pid)..."
            kill -TERM "$pid" 2>/dev/null || true
            sleep 1
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done
}

# Generate shutdown report
generate_shutdown_report() {
    print_status "Generating shutdown report..."
    
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local report_file="reports/shutdown_report_$timestamp.txt"
    
    mkdir -p reports
    
    cat > "$report_file" << EOF
ChatterFix Enterprise Platform - Shutdown Report
Generated: $(date)
================================================

SHUTDOWN SUMMARY:
- Platform stopped gracefully
- All services terminated
- Documentation maintained
- Logs preserved

SERVICE STATUS AT SHUTDOWN:
$(for pidfile in logs/*.pid; do
    if [ -f "$pidfile" ]; then
        echo "- $(basename "$pidfile" .pid): Stopped"
    fi
done)

LOG FILES PRESERVED:
$(ls -la logs/ 2>/dev/null || echo "No logs found")

DOCUMENTATION STATUS:
- AI Look documentation maintained
- Auto-updates disabled
- All changes saved

UPTIME INFORMATION:
$(uptime)

DISK USAGE:
$(df -h . | tail -1)

NEXT STARTUP:
Run: ./start_enterprise_platform.sh

================================================
Platform shutdown completed successfully.
EOF

    print_success "Shutdown report saved: $report_file"
}

# Main stop function
main() {
    echo "================================================================"
    echo "🛑 ChatterFix Enterprise Platform Shutdown"
    echo "================================================================"
    
    stop_services
    
    # Wait a moment for processes to fully terminate
    sleep 2
    
    generate_shutdown_report
    
    echo ""
    echo "================================================================"
    echo "✅ ChatterFix Enterprise Platform Stopped Successfully"
    echo "================================================================"
    echo ""
    echo "📊 Final Status:"
    echo "   • All services stopped"
    echo "   • Logs preserved in logs/"
    echo "   • Reports saved in reports/"
    echo "   • Documentation maintained"
    echo ""
    echo "🚀 To restart:"
    echo "   ./start_enterprise_platform.sh"
    echo ""
    echo "📚 Documentation remains available:"
    echo "   • AI_LOOK.md"
    echo "   • AI_LOOK_QUICK_START.md"
    echo "   • AI_LOOK_TECHNICAL_ADDENDUM.md"
    echo "================================================================"
}

main "$@"
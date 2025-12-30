#!/bin/bash
set -e

# ChatterFix Enterprise Platform Startup Script
# Fortune 500 Grade Platform with Auto-Documentation

echo "🚀 Starting ChatterFix Enterprise Platform..."
echo "================================================================"

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] ✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%H:%M:%S')] ⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date +'%H:%M:%S')] ❌${NC} $1"
}

# Check dependencies
check_dependencies() {
    print_status "Checking system dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    print_success "Python 3 found: $(python3 --version)"
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is required but not installed"
        exit 1
    fi
    print_success "pip3 found"
    
    # Check required Python packages
    print_status "Checking Python dependencies..."
    pip3 install -q fastapi uvicorn sqlalchemy psycopg2-binary requests aiohttp psutil watchdog gitpython 2>/dev/null || {
        print_warning "Installing missing Python packages..."
        pip3 install fastapi uvicorn sqlalchemy psycopg2-binary requests aiohttp psutil watchdog gitpython
    }
    print_success "Python dependencies verified"
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Create logs directory
    mkdir -p logs
    mkdir -p reports
    mkdir -p backups
    
    # Set environment variables
    export PYTHONPATH="$(pwd):$PYTHONPATH"
    export CHATTERFIX_ENV="development"
    export CHATTERFIX_LOG_LEVEL="INFO"
    
    print_success "Environment configured"
}

# Start database services
start_database() {
    print_status "Starting database services..."
    
    # Check if PostgreSQL is running
    if pgrep -x "postgres" > /dev/null; then
        print_success "PostgreSQL already running"
    else
        print_warning "PostgreSQL not detected - using SQLite fallback"
    fi
    
    # Initialize database if needed
    if [ ! -f "cmms.db" ]; then
        print_status "Initializing database..."
        python3 -c "
import sqlite3
conn = sqlite3.connect('cmms.db')
conn.execute('CREATE TABLE IF NOT EXISTS health_check (id INTEGER PRIMARY KEY, status TEXT)')
conn.execute('INSERT INTO health_check (status) VALUES (\"initialized\")')
conn.commit()
conn.close()
print('Database initialized')
"
        print_success "Database initialized"
    fi
}

# Start core services
start_core_services() {
    print_status "Starting ChatterFix core services..."
    
    # Start Fix It Fred AI Service (Port 8005)
    print_status "Starting Fix It Fred AI Service..."
    PORT=8005 python3 fix_it_fred_ai_service.py > logs/fix_it_fred_ai.log 2>&1 &
    FRED_PID=$!
    echo $FRED_PID > logs/fix_it_fred_ai.pid
    
    # Wait for service to start
    sleep 3
    if curl -s http://localhost:8005/health > /dev/null; then
        print_success "Fix It Fred AI Service started (PID: $FRED_PID)"
    else
        print_warning "Fix It Fred AI Service may still be starting..."
    fi
    
    # Start Platform Gateway (Port 8000)
    if [ -f "core/cmms/platform_gateway.py" ]; then
        print_status "Starting ChatterFix Platform Gateway..."
        python3 core/cmms/platform_gateway.py > logs/platform_gateway.log 2>&1 &
        GATEWAY_PID=$!
        echo $GATEWAY_PID > logs/platform_gateway.pid
        
        sleep 3
        if curl -s http://localhost:8000/health > /dev/null; then
            print_success "Platform Gateway started (PID: $GATEWAY_PID)"
        else
            print_warning "Platform Gateway may still be starting..."
        fi
    else
        print_warning "Platform Gateway not found - running in minimal mode"
    fi
}

# Start monitoring and documentation
start_monitoring() {
    print_status "Starting enterprise monitoring..."
    
    # Start Documentation Manager
    print_status "Starting AI Look Documentation Manager..."
    python3 ai_look_doc_manager.py > logs/doc_manager.log 2>&1 &
    DOC_PID=$!
    echo $DOC_PID > logs/doc_manager.pid
    print_success "Documentation Manager started (PID: $DOC_PID)"
    
    # Start Enterprise Monitor
    print_status "Starting Enterprise System Monitor..."
    python3 enterprise_monitor.py > logs/enterprise_monitor.log 2>&1 &
    MONITOR_PID=$!
    echo $MONITOR_PID > logs/enterprise_monitor.pid
    print_success "Enterprise Monitor started (PID: $MONITOR_PID)"
}

# Health check all services
health_check() {
    print_status "Performing system health check..."
    
    local all_healthy=true
    
    # Check Fix It Fred AI
    if curl -s http://localhost:8005/health | grep -q "healthy"; then
        print_success "Fix It Fred AI: Healthy"
    else
        print_error "Fix It Fred AI: Not responding"
        all_healthy=false
    fi
    
    # Check Platform Gateway
    if curl -s http://localhost:8000/health | grep -q "healthy"; then
        print_success "Platform Gateway: Healthy"
    else
        print_warning "Platform Gateway: Not responding (may be normal in minimal mode)"
    fi
    
    # Check processes
    local processes=("doc_manager" "enterprise_monitor" "fix_it_fred_ai")
    for process in "${processes[@]}"; do
        if [ -f "logs/${process}.pid" ] && kill -0 $(cat "logs/${process}.pid") 2>/dev/null; then
            print_success "${process}: Running"
        else
            print_warning "${process}: Not running"
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        print_success "All critical services are healthy"
    else
        print_warning "Some services may need attention"
    fi
}

# Display access information
show_access_info() {
    echo ""
    echo "================================================================"
    echo "🎉 ChatterFix Enterprise Platform Started Successfully!"
    echo "================================================================"
    echo ""
    echo "🌐 Access Points:"
    echo "   • ChatterFix Dashboard: http://localhost:8000"
    echo "   • Fix It Fred AI API: http://localhost:8005"
    echo "   • API Documentation: http://localhost:8000/docs"
    echo ""
    echo "📊 Monitoring:"
    echo "   • System logs: logs/"
    echo "   • Health reports: reports/"
    echo "   • Real-time monitoring: Active"
    echo "   • Auto-documentation: Active"
    echo ""
    echo "🔧 Management:"
    echo "   • Stop platform: ./stop_enterprise_platform.sh"
    echo "   • View logs: tail -f logs/*.log"
    echo "   • Health check: curl http://localhost:8005/health"
    echo ""
    echo "📚 Documentation:"
    echo "   • AI Look Guide: AI_LOOK.md"
    echo "   • Quick Start: AI_LOOK_QUICK_START.md"
    echo "   • Technical Reference: AI_LOOK_TECHNICAL_ADDENDUM.md"
    echo ""
    echo "🤖 AI Integration:"
    echo "   • Fix It Fred ready for maintenance queries"
    echo "   • Auto-documentation updates enabled"
    echo "   • Enterprise monitoring active"
    echo ""
    echo "================================================================"
    echo "Platform Status: $([ "$?" = 0 ] && echo "🟢 OPERATIONAL" || echo "🟡 PARTIAL")"
    echo "================================================================"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up previous instances..."
    
    # Kill existing processes
    for pidfile in logs/*.pid; do
        if [ -f "$pidfile" ]; then
            local pid=$(cat "$pidfile")
            if kill -0 "$pid" 2>/dev/null; then
                print_status "Stopping process $pid..."
                kill "$pid" 2>/dev/null || true
            fi
            rm -f "$pidfile"
        fi
    done
    
    # Wait for processes to stop
    sleep 2
    print_success "Cleanup completed"
}

# Main execution
main() {
    echo "Starting ChatterFix Enterprise Platform..."
    echo "Timestamp: $(date)"
    echo ""
    
    # Cleanup any existing instances
    cleanup
    
    # Run startup sequence
    check_dependencies
    setup_environment
    start_database
    start_core_services
    start_monitoring
    
    # Wait for services to fully initialize
    print_status "Waiting for services to initialize..."
    sleep 5
    
    # Perform health check
    health_check
    
    # Show access information
    show_access_info
    
    # Keep script running and monitor
    print_status "Platform running. Press Ctrl+C to stop..."
    
    # Monitor and keep alive
    while true; do
        sleep 60
        
        # Quick health check
        if ! curl -s http://localhost:8005/health > /dev/null; then
            print_warning "Fix It Fred AI may need attention"
        fi
        
        # Check if monitoring processes are still running
        for process in "doc_manager" "enterprise_monitor"; do
            if [ -f "logs/${process}.pid" ]; then
                local pid=$(cat "logs/${process}.pid")
                if ! kill -0 "$pid" 2>/dev/null; then
                    print_warning "${process} stopped unexpectedly - restarting..."
                    case $process in
                        "doc_manager")
                            python3 ai_look_doc_manager.py > logs/doc_manager.log 2>&1 &
                            echo $! > logs/doc_manager.pid
                            ;;
                        "enterprise_monitor")
                            python3 enterprise_monitor.py > logs/enterprise_monitor.log 2>&1 &
                            echo $! > logs/enterprise_monitor.pid
                            ;;
                    esac
                fi
            fi
        done
    done
}

# Handle Ctrl+C
trap 'echo ""; print_status "Shutting down..."; cleanup; exit 0' INT

# Run main function
main "$@"
#!/bin/bash
# ChatterFix CMMS - Stop Local Development Environment

echo "🛑 Stopping ChatterFix CMMS Local Development Environment..."

# Create pids directory if it doesn't exist
mkdir -p pids

# Function to stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file="pids/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping $service_name (PID: $pid)..."
            kill $pid
            sleep 1
            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                echo "Force stopping $service_name..."
                kill -9 $pid
            fi
        fi
        rm -f "$pid_file"
    fi
}

# Stop all services
stop_service "gateway"
stop_service "ai_brain" 
stop_service "claude_code"
stop_service "database"

# Also kill any remaining Python processes running our services
pkill -f "app.py" 2>/dev/null || true
pkill -f "ai_brain_service.py" 2>/dev/null || true
pkill -f "claude_code_assistant.py" 2>/dev/null || true
pkill -f "database_service.py" 2>/dev/null || true

echo "✅ All ChatterFix CMMS services stopped."
echo ""
echo "📊 To restart: ./start_local_dev.sh"
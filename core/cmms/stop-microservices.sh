#!/bin/bash
# Stop all ChatterFix microservices

echo "🛑 Stopping ChatterFix Microservices..."

# Stop services by PID files
if [ -d "pids" ]; then
    for pidfile in pids/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            service_name=$(basename "$pidfile" .pid)
            echo "  Stopping $service_name (PID: $pid)"
            kill "$pid" 2>/dev/null || true
            rm "$pidfile"
        fi
    done
fi

# Kill any remaining services on ports 8001-8008
echo "🔍 Checking for remaining services..."
for port in {8001..8008}; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "  Killing service on port $port"
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
    fi
done

echo "✅ All microservices stopped"
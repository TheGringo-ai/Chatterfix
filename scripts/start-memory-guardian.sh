#!/bin/bash
# Start Memory Guardian daemon
# Run this to protect VS Code from memory crashes

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
GUARDIAN_SCRIPT="$SCRIPT_DIR/memory-guardian.py"
PID_FILE="$HOME/.memory-guardian.pid"

start() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Memory Guardian is already running (PID: $PID)"
            return
        fi
    fi

    echo "Starting Memory Guardian..."
    nohup python3 "$GUARDIAN_SCRIPT" > "$HOME/.memory-guardian-output.log" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Memory Guardian started (PID: $!)"
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping Memory Guardian (PID: $PID)..."
            kill $PID
            rm "$PID_FILE"
            echo "Memory Guardian stopped"
        else
            echo "Memory Guardian not running"
            rm "$PID_FILE"
        fi
    else
        echo "Memory Guardian not running"
    fi
}

status() {
    python3 "$GUARDIAN_SCRIPT" status
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        stop
        sleep 1
        start
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo ""
        echo "Commands:"
        echo "  start   - Start Memory Guardian daemon"
        echo "  stop    - Stop Memory Guardian daemon"
        echo "  restart - Restart Memory Guardian daemon"
        echo "  status  - Show current memory status"
        exit 1
        ;;
esac

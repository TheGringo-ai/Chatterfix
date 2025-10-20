#!/bin/bash
set -e

echo "🚀 Starting ChatterFix Integrated System"
echo "========================================"

# Kill any existing services
pkill -f "python.*database_service.py" || true
pkill -f "python.*work_orders_service.py" || true
pkill -f "python.*assets_service.py" || true
pkill -f "python.*parts_service.py" || true
pkill -f "python.*fix_it_fred_universal_ai.py" || true

sleep 2

# Initialize database
echo "📊 Initializing database..."
python3 database_service.py --init-db

# Start services in background
echo "🗄️  Starting database service (port 8001)..."
nohup python3 database_service.py --port 8001 > logs/database.log 2>&1 &

sleep 3

echo "🔧 Starting work orders service (port 8002)..."
nohup python3 work_orders_service.py --port 8002 > logs/work_orders.log 2>&1 &

echo "🏭 Starting assets service (port 8003)..."
nohup python3 assets_service.py --port 8003 > logs/assets.log 2>&1 &

echo "📦 Starting parts service (port 8004)..."
nohup python3 parts_service.py --port 8004 > logs/parts.log 2>&1 &

echo "🤖 Starting Fix It Fred Universal AI (port 8005)..."
nohup python3 fix_it_fred_universal_ai.py > logs/fix_it_fred.log 2>&1 &

sleep 5

echo "✅ All services started!"
echo ""
echo "🌐 Service URLs:"
echo "  Database Service:    http://localhost:8001"
echo "  Work Orders Service: http://localhost:8002"
echo "  Assets Service:      http://localhost:8003"
echo "  Parts Service:       http://localhost:8004"
echo "  Fix It Fred AI:      http://localhost:8005"
echo ""
echo "🔗 External Access:"
echo "  Main Site: https://chatterfix.com"
echo "  AI Interface: https://chatterfix.com/ai"
echo ""

# Test services
echo "🧪 Testing services..."
for port in 8001 8002 8003 8004 8005; do
    if curl -s "http://localhost:$port/health" > /dev/null; then
        echo "  ✅ Port $port: OK"
    else
        echo "  ❌ Port $port: FAILED"
    fi
done

echo ""
echo "🎉 ChatterFix Integrated System Ready!"

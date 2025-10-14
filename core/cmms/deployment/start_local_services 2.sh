#!/bin/bash

# ChatterFix CMMS - Local Services Startup Script
# Starts all microservices on different ports for local development

echo "🚀 Starting ChatterFix CMMS Local Services..."

# Kill any existing services
pkill -f "python.*service.py"
sleep 2

# Start Database Service on port 8001
echo "Starting Database Service on port 8001..."
PORT=8001 python3 database_service.py &
sleep 3

# Start Work Orders Service on port 8002
echo "Starting Work Orders Service on port 8002..."
PORT=8002 python3 work_orders_service.py &
sleep 2

# Start Assets Service on port 8003
echo "Starting Assets Service on port 8003..."
PORT=8003 python3 assets_service.py &
sleep 2

# Start Parts Service on port 8004
echo "Starting Parts Service on port 8004..."
PORT=8004 python3 parts_service.py &
sleep 2

# Start AI Brain Service on port 8005
echo "Starting AI Brain Service on port 8005..."
PORT=8005 python3 ai_brain_service.py &
sleep 2

# Start Document Intelligence Service on port 8006
echo "Starting Document Intelligence Service on port 8006..."
PORT=8006 python3 document_intelligence_service.py &
sleep 2

# UI Gateway runs on 8080 (default)
echo "UI Gateway running on port 8080..."

echo "✅ All services started successfully!"
echo ""
echo "Service URLs:"
echo "  🌐 UI Gateway:            http://localhost:8080"
echo "  🗄️  Database Service:      http://localhost:8001"
echo "  🛠️  Work Orders Service:   http://localhost:8002" 
echo "  🏭 Assets Service:        http://localhost:8003"
echo "  🔧 Parts Service:         http://localhost:8004"
echo "  🧠 AI Brain Service:      http://localhost:8005"
echo "  📄 Document Intelligence: http://localhost:8006"
echo ""
echo "🎯 Access ChatterFix CMMS at: http://localhost:8080"

# Test all services
echo "🔍 Testing service health..."
sleep 5

services=(
  "8001:Database"
  "8002:Work-Orders"
  "8003:Assets"
  "8004:Parts"
  "8005:AI-Brain"
  "8006:Document-Intelligence"
)

for service in "${services[@]}"; do
  IFS=':' read -r port name <<< "$service"
  status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health 2>/dev/null)
  if [ "$status" = "200" ]; then
    echo "✅ $name Service (port $port): Healthy"
  else
    echo "❌ $name Service (port $port): Unhealthy (status: $status)"
  fi
done

echo ""
echo "🎉 ChatterFix CMMS is ready for development!"
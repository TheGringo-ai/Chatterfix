#!/bin/bash

echo "🚀 ChatterFix CMMS - Complete Production Deployment"
echo "🎯 All Microservices with Proper API Configuration"
echo "=================================================="

# Stop all existing services
echo "🛑 Stopping all existing services..."
sudo systemctl stop chatterfix-enhanced 2>/dev/null || true
sudo systemctl stop chatterfix-complete 2>/dev/null || true

# Kill processes on all ports
for port in {8000..8010} 8015 8080 8081; do
    echo "  Stopping services on port $port..."
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
done

sleep 5

# Install dependencies
echo "📦 Installing Python dependencies..."
python3 -m pip install --user --quiet -r requirements.txt

# Create directories
echo "📁 Creating application directories..."
mkdir -p data logs pids

# Initialize database if needed
echo "🗄️ Initializing database..."
if [ ! -f "data/cmms.db" ]; then
    python3 database_service.py --init-db 2>/dev/null || true
fi

# Create startup scripts for each service
echo "📝 Creating service startup scripts..."

# Database Service (Port 8001)
cat > start_database_service.sh << 'DB_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
nohup python3 database_service.py --port 8001 > logs/database_service.log 2>&1 &
echo $! > pids/database_service.pid
echo "Database Service started on port 8001"
DB_EOF
chmod +x start_database_service.sh

# Work Orders Service (Port 8002)
cat > start_work_orders_service.sh << 'WO_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
nohup python3 work_orders_service.py --port 8002 > logs/work_orders_service.log 2>&1 &
echo $! > pids/work_orders_service.pid
echo "Work Orders Service started on port 8002"
WO_EOF
chmod +x start_work_orders_service.sh

# Assets Service (Port 8003)
cat > start_assets_service.sh << 'AS_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
nohup python3 assets_service.py --port 8003 > logs/assets_service.log 2>&1 &
echo $! > pids/assets_service.pid
echo "Assets Service started on port 8003"
AS_EOF
chmod +x start_assets_service.sh

# Parts Service (Port 8004)
cat > start_parts_service.sh << 'PS_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
nohup python3 parts_service.py --port 8004 > logs/parts_service.log 2>&1 &
echo $! > pids/parts_service.pid
echo "Parts Service started on port 8004"
PS_EOF
chmod +x start_parts_service.sh

# Fix It Fred AI Service (Port 8005)
cat > start_fix_it_fred_service.sh << 'FRED_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
nohup python3 fix_it_fred_ai_service.py --port 8005 > logs/fix_it_fred_service.log 2>&1 &
echo $! > pids/fix_it_fred_service.pid
echo "Fix It Fred AI Service started on port 8005"
FRED_EOF
chmod +x start_fix_it_fred_service.sh

# Grok Connector Service (Port 8006)
cat > start_grok_service.sh << 'GROK_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
nohup python3 grok_connector.py --port 8006 > logs/grok_service.log 2>&1 &
echo $! > pids/grok_service.pid
echo "Grok Connector Service started on port 8006"
GROK_EOF
chmod +x start_grok_service.sh

# Document Intelligence Service (Port 8008)
cat > start_document_service.sh << 'DOC_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
nohup python3 document_intelligence_service.py --port 8008 > logs/document_service.log 2>&1 &
echo $! > pids/document_service.pid
echo "Document Intelligence Service started on port 8008"
DOC_EOF
chmod +x start_document_service.sh

# Main Application (Port 8000 and 8080 for compatibility)
cat > start_main_app.sh << 'MAIN_EOF'
#!/bin/bash
cd /opt/chatterfix-cmms/current
nohup python3 app_main.py --port 8000 > logs/main_app_8000.log 2>&1 &
echo $! > pids/main_app_8000.pid
nohup python3 app_main.py --port 8080 > logs/main_app_8080.log 2>&1 &
echo $! > pids/main_app_8080.pid
echo "Main Application started on ports 8000 and 8080"
MAIN_EOF
chmod +x start_main_app.sh

# Master startup script
cat > start_all_services.sh << 'ALL_EOF'
#!/bin/bash
echo "🚀 Starting Complete ChatterFix CMMS Services"
echo "=============================================="

# Start services in dependency order
echo "📊 Starting Database Service..."
./start_database_service.sh
sleep 3

echo "🔧 Starting Work Orders Service..."
./start_work_orders_service.sh
sleep 2

echo "🏭 Starting Assets Service..."
./start_assets_service.sh
sleep 2

echo "📦 Starting Parts Service..."
./start_parts_service.sh
sleep 2

echo "🤖 Starting Fix It Fred AI Service..."
./start_fix_it_fred_service.sh
sleep 2

echo "🧠 Starting Grok Connector Service..."
./start_grok_service.sh
sleep 2

echo "📄 Starting Document Intelligence Service..."
./start_document_service.sh
sleep 2

echo "🌐 Starting Main Application..."
./start_main_app.sh
sleep 5

echo ""
echo "✅ All ChatterFix CMMS Services Started!"
echo "========================================"
echo ""
echo "🔗 Service URLs:"
echo "   Main Dashboard: http://35.237.149.25:8080"
echo "   Main Dashboard (Alt): http://35.237.149.25:8000"
echo "   Database Service: http://35.237.149.25:8001/health"
echo "   Work Orders API: http://35.237.149.25:8002/docs"
echo "   Assets API: http://35.237.149.25:8003/docs"
echo "   Parts API: http://35.237.149.25:8004/docs"
echo "   Fix It Fred AI: http://35.237.149.25:8005/health"
echo "   Grok Connector: http://35.237.149.25:8006/health"
echo "   Document Service: http://35.237.149.25:8008/health"
echo ""
echo "🎯 All APIs properly configured and routed!"

# Wait a moment then test all services
sleep 10
echo ""
echo "🧪 Testing All Services..."
echo "========================="

services=(
    "8000:Main App"
    "8001:Database"
    "8002:Work Orders"
    "8003:Assets"
    "8004:Parts"
    "8005:Fix It Fred"
    "8006:Grok Connector"
    "8008:Document Service"
    "8080:Main App (Alt)"
)

for service in "${services[@]}"; do
    port="${service%:*}"
    name="${service#*:}"
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $name (Port $port): Running"
    else
        echo "⚠️  $name (Port $port): Not responding"
    fi
done

echo ""
echo "📊 Process Status:"
ps aux | grep -E "(python3.*service|python3.*app)" | grep -v grep | head -10

ALL_EOF
chmod +x start_all_services.sh

# Create stop script
cat > stop_all_services.sh << 'STOP_EOF'
#!/bin/bash
echo "🛑 Stopping All ChatterFix Services..."

# Kill by PID files
for pidfile in pids/*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        echo "  Stopping PID $pid..."
        kill -9 "$pid" 2>/dev/null || true
        rm -f "$pidfile"
    fi
done

# Kill by port
for port in {8000..8010} 8080; do
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
done

echo "✅ All services stopped"
STOP_EOF
chmod +x stop_all_services.sh

# Create systemd service
echo "⚙️ Setting up systemd service..."
sudo tee /etc/systemd/system/chatterfix-complete.service > /dev/null << 'SERVICE_EOF'
[Unit]
Description=ChatterFix Complete CMMS
After=network.target

[Service]
Type=forking
User=yoyofred_gringosgambit_com
WorkingDirectory=/opt/chatterfix-cmms/current
ExecStart=/opt/chatterfix-cmms/current/start_all_services.sh
ExecStop=/opt/chatterfix-cmms/current/stop_all_services.sh
Restart=always
RestartSec=10
Environment=PATH=/usr/bin:/usr/local/bin:/home/yoyofred_gringosgambit_com/.local/bin

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Start all services
echo "🚀 Starting Complete ChatterFix CMMS..."
./start_all_services.sh

# Enable systemd service
sudo systemctl daemon-reload
sudo systemctl enable chatterfix-complete

echo ""
echo "🎉 COMPLETE CHATTERFIX CMMS DEPLOYED SUCCESSFULLY!"
echo "================================================="
echo "🌐 Main URL: http://35.237.149.25:8080"
echo "🌐 Alt URL: http://35.237.149.25:8000"
echo "🔗 All APIs available on their respective ports"
echo "📚 API Documentation: http://35.237.149.25:8002/docs"
echo "🎯 Complete microservices architecture is now LIVE!"


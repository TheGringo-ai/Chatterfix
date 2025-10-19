#!/bin/bash
set -e

echo "🚀 DEPLOYING INTEGRATED CHATTERFIX + FIX IT FRED TO VM"
echo "====================================================="
echo "Deploying complete integrated system to chatterfix.com"
echo ""

# Configuration
VM_USER="yoyofred_gringosgambit_com"
VM_HOST="35.237.149.25"
VM_PATH="/home/$VM_USER/chatterfix-integrated"
DEPLOYMENT_NAME="chatterfix-integrated-$(date +%Y%m%d-%H%M%S)"

echo "🎯 TARGET: $VM_USER@$VM_HOST:$VM_PATH"
echo "📦 DEPLOYMENT: $DEPLOYMENT_NAME"
echo ""

# Create deployment package
echo "📦 CREATING DEPLOYMENT PACKAGE"
echo "==============================="
mkdir -p deployment-package/chatterfix-integrated
cd deployment-package/chatterfix-integrated

# Copy core integrated services
echo "📋 Copying integrated services..."

# Fix It Fred Universal AI
cp ../../fix_it_fred_universal_ai.py .
cp ../../chatterfix_ai_helper.py .

# ChatterFix CMMS Microservices
cp ../../core/cmms/database_service.py .
cp ../../core/cmms/work_orders_service.py .
cp ../../core/cmms/assets_service.py .
cp ../../core/cmms/parts_service.py .

# Create requirements.txt for the integrated system
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
requests==2.31.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dateutil==2.8.2
typing-extensions==4.8.0
aiofiles==23.2.1
jinja2==3.1.2
EOF

# Create startup script for all services
cat > start_all_services.sh << 'EOF'
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
EOF

chmod +x start_all_services.sh

# Create stop script
cat > stop_all_services.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping ChatterFix Integrated System"
echo "========================================"

pkill -f "python.*database_service.py" || true
pkill -f "python.*work_orders_service.py" || true
pkill -f "python.*assets_service.py" || true
pkill -f "python.*parts_service.py" || true
pkill -f "python.*fix_it_fred_universal_ai.py" || true

echo "✅ All services stopped"
EOF

chmod +x stop_all_services.sh

# Create nginx configuration for chatterfix.com
cat > nginx_chatterfix.conf << 'EOF'
# ChatterFix CMMS with Fix It Fred AI Integration
# Nginx configuration for chatterfix.com

upstream chatterfix_database {
    server 127.0.0.1:8001;
}

upstream chatterfix_work_orders {
    server 127.0.0.1:8002;
}

upstream chatterfix_assets {
    server 127.0.0.1:8003;
}

upstream chatterfix_parts {
    server 127.0.0.1:8004;
}

upstream fix_it_fred_ai {
    server 127.0.0.1:8005;
}

server {
    listen 80;
    server_name chatterfix.com www.chatterfix.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name chatterfix.com www.chatterfix.com;
    
    # SSL configuration (you'll need to set up SSL certificates)
    # ssl_certificate /path/to/certificate.crt;
    # ssl_certificate_key /path/to/private.key;
    
    # Main ChatterFix interface (Fix It Fred AI)
    location / {
        proxy_pass http://fix_it_fred_ai;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # AI-specific endpoints
    location /api/universal/ {
        proxy_pass http://fix_it_fred_ai;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # ChatterFix CMMS API endpoints
    location /api/database/ {
        proxy_pass http://chatterfix_database/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/work_orders/ {
        proxy_pass http://chatterfix_work_orders/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/assets/ {
        proxy_pass http://chatterfix_assets/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/parts/ {
        proxy_pass http://chatterfix_parts/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health checks
    location /health {
        proxy_pass http://fix_it_fred_ai;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Create systemd service files
cat > chatterfix-integrated.service << 'EOF'
[Unit]
Description=ChatterFix Integrated CMMS System
After=network.target

[Service]
Type=forking
User=yoyofred_gringosgambit_com
WorkingDirectory=/home/yoyofred_gringosgambit_com/chatterfix-integrated
ExecStart=/home/yoyofred_gringosgambit_com/chatterfix-integrated/start_all_services.sh
ExecStop=/home/yoyofred_gringosgambit_com/chatterfix-integrated/stop_all_services.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create status check script
cat > check_status.sh << 'EOF'
#!/bin/bash
echo "🔍 ChatterFix Integrated System Status"
echo "====================================="

echo ""
echo "📊 Service Status:"
for port in 8001 8002 8003 8004 8005; do
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "  ✅ Port $port: Running"
    else
        echo "  ❌ Port $port: Not responding"
    fi
done

echo ""
echo "🔗 Process Status:"
echo "Database Service:    $(pgrep -f database_service.py || echo 'Not running')"
echo "Work Orders Service: $(pgrep -f work_orders_service.py || echo 'Not running')"
echo "Assets Service:      $(pgrep -f assets_service.py || echo 'Not running')"
echo "Parts Service:       $(pgrep -f parts_service.py || echo 'Not running')"
echo "Fix It Fred AI:      $(pgrep -f fix_it_fred_universal_ai.py || echo 'Not running')"

echo ""
echo "📝 Recent logs:"
echo "Last 5 lines from Fix It Fred AI:"
tail -5 logs/fix_it_fred.log 2>/dev/null || echo "No log file found"
EOF

chmod +x check_status.sh

echo "✅ Deployment package created"
echo ""

# Upload to VM
echo "📤 UPLOADING TO VM"
echo "=================="

echo "🔑 Connecting to $VM_HOST..."
ssh -o StrictHostKeyChecking=no $VM_USER@$VM_HOST "mkdir -p $VM_PATH/logs"

echo "📁 Uploading files..."
scp -o StrictHostKeyChecking=no -r * $VM_USER@$VM_HOST:$VM_PATH/

echo "✅ Upload complete"
echo ""

# Install dependencies and start services
echo "🔧 INSTALLING AND STARTING SERVICES"
echo "===================================="

ssh -o StrictHostKeyChecking=no $VM_USER@$VM_HOST << EOF
cd $VM_PATH

echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

echo "🚀 Starting all services..."
./start_all_services.sh

echo "⏳ Waiting for services to stabilize..."
sleep 10

echo "🧪 Final status check..."
./check_status.sh

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "🌐 Your integrated ChatterFix system is now running at:"
echo "   https://chatterfix.com"
echo ""
echo "🔧 To manage the system:"
echo "   Start:  ssh $VM_USER@$VM_HOST 'cd $VM_PATH && ./start_all_services.sh'"
echo "   Stop:   ssh $VM_USER@$VM_HOST 'cd $VM_PATH && ./stop_all_services.sh'"
echo "   Status: ssh $VM_USER@$VM_HOST 'cd $VM_PATH && ./check_status.sh'"
echo ""
EOF

echo ""
echo "✅ INTEGRATED CHATTERFIX DEPLOYMENT COMPLETE!"
echo "=============================================="
echo ""
echo "🎯 All services deployed to: $VM_USER@$VM_HOST:$VM_PATH"
echo "🌐 Available at: https://chatterfix.com"
echo ""
echo "📋 Services running:"
echo "  🗄️  Database Service (port 8001)"
echo "  🔧 Work Orders Service (port 8002)"  
echo "  🏭 Assets Service (port 8003)"
echo "  📦 Parts Service (port 8004)"
echo "  🤖 Fix It Fred Universal AI (port 8005)"
echo ""
echo "🔗 Integration: ChatterFix CMMS + Fix It Fred AI working together!"
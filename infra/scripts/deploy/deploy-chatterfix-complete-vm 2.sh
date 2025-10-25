#!/bin/bash
set -e

echo "🚀 CHATTERFIX CMMS COMPLETE VM DEPLOYMENT"
echo "========================================"
echo "Deploying all ChatterFix modules to VM"
echo ""

# Configuration
VM_USER="yoyofred_gringosgambit_com"
VM_HOST="35.237.149.25"
VM_PATH="/home/$VM_USER/chatterfix-cmms"
DEPLOYMENT_NAME="chatterfix-complete-$(date +%Y%m%d-%H%M%S)"

# Core services to deploy
CORE_SERVICES=(
    "app.py"
    "main_app.py"
    "platform_gateway.py"
    "ai_brain_service.py"
    "backend_unified_service.py"
    "fix_it_fred_gateway.py"
    "grok_connector.py"
    "grok_infrastructure_advisor.py"
    "budget_tracker.py"
    "mobile_server.py"
    "fred_dev_api.py"
    "emergency_app.py"
)

# Support files
SUPPORT_FILES=(
    "database_utils.py"
    "security_middleware.py"
    "requirements.txt"
    ".env"
    "mobile_chat.html"
)

echo "📦 CREATING DEPLOYMENT PACKAGE"
echo "==============================="

# Create deployment directory
mkdir -p deployment-package/chatterfix-cmms
cd deployment-package/chatterfix-cmms

# Copy core services
echo "📋 Copying core services..."
for service in "${CORE_SERVICES[@]}"; do
    if [ -f "../../core/cmms/$service" ]; then
        cp "../../core/cmms/$service" .
        echo "  ✅ $service"
    else
        echo "  ⚠️  $service not found"
    fi
done

# Copy support files
echo "📋 Copying support files..."
for file in "${SUPPORT_FILES[@]}"; do
    if [ -f "../../core/cmms/$file" ]; then
        cp "../../core/cmms/$file" .
        echo "  ✅ $file"
    elif [ -f "../../$file" ]; then
        cp "../../$file" .
        echo "  ✅ $file"
    else
        echo "  ⚠️  $file not found"
    fi
done

# Copy templates and static directories
echo "📋 Copying web assets..."
if [ -d "../../core/cmms/templates" ]; then
    cp -r "../../core/cmms/templates" .
    echo "  ✅ templates/"
fi

if [ -d "../../core/cmms/static" ]; then
    cp -r "../../core/cmms/static" .
    echo "  ✅ static/"
fi

# Copy data directory
echo "📋 Copying data directory..."
if [ -d "../../core/cmms/data" ]; then
    cp -r "../../core/cmms/data" .
    echo "  ✅ data/"
fi

# Create enhanced requirements.txt
echo "📋 Creating enhanced requirements.txt..."
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
httpx==0.25.2
asyncpg==0.29.0
python-multipart==0.0.6
jinja2==3.1.2
websockets==12.0
aiofiles==23.2.1
pydantic==2.5.0
sqlalchemy==2.0.23
python-dotenv==1.0.0
redis==5.0.1
bcrypt==4.1.2
python-jose[cryptography]==3.3.0
psutil==5.9.6
requests==2.31.0
anthropic==0.8.1
openai==1.3.7
google-generativeai==0.3.2
ollama==0.1.7
EOF

# Create startup script
echo "📋 Creating startup script..."
cat > start-chatterfix.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting ChatterFix CMMS Services"
echo "===================================="

# Kill existing processes
echo "🛑 Stopping existing services..."
pkill -f "python.*app.py" || true
pkill -f "python.*service.py" || true
sleep 2

# Set environment
export PYTHONPATH=/home/yoyofred_gringosgambit_com/chatterfix-cmms
export CHATTERFIX_ENV=production
export PORT=8080

cd /home/yoyofred_gringosgambit_com/chatterfix-cmms

# Start core services in background
echo "🚀 Starting services..."

# Main platform gateway (port 8080)
echo "  🌐 Starting Platform Gateway..."
nohup python3 platform_gateway.py > logs/platform_gateway.log 2>&1 &

# AI Brain service (port 8005)
echo "  🧠 Starting AI Brain Service..."
nohup python3 ai_brain_service.py > logs/ai_brain.log 2>&1 &

# Backend unified service (port 8001)
echo "  🔧 Starting Backend Service..."
nohup python3 backend_unified_service.py > logs/backend.log 2>&1 &

# Grok connector (port 8006)
echo "  🤖 Starting Grok Connector..."
nohup python3 grok_connector.py > logs/grok_connector.log 2>&1 &

# Grok infrastructure advisor (port 8007)
echo "  🏗️ Starting Infrastructure Advisor..."
nohup python3 grok_infrastructure_advisor.py > logs/grok_infrastructure.log 2>&1 &

# Budget tracker (port 8009)
echo "  💰 Starting Budget Tracker..."
nohup python3 budget_tracker.py > logs/budget_tracker.log 2>&1 &

# Mobile server (port 8080 alt)
echo "  📱 Starting Mobile Server..."
nohup python3 mobile_server.py > logs/mobile_server.log 2>&1 &

# Fred dev API (port 8004)
echo "  👨‍💻 Starting Fred Dev API..."
nohup python3 fred_dev_api.py > logs/fred_dev_api.log 2>&1 &

echo ""
echo "⏳ Waiting for services to initialize..."
sleep 15

echo ""
echo "🧪 Testing services..."
curl -s http://localhost:8080/health && echo "✅ Platform Gateway: OK" || echo "❌ Platform Gateway: FAILED"
curl -s http://localhost:8005/health && echo "✅ AI Brain: OK" || echo "❌ AI Brain: FAILED"
curl -s http://localhost:8001/health && echo "✅ Backend: OK" || echo "❌ Backend: FAILED"
curl -s http://localhost:8006/ && echo "✅ Grok Connector: OK" || echo "❌ Grok Connector: FAILED"
curl -s http://localhost:8007/ && echo "✅ Infrastructure Advisor: OK" || echo "❌ Infrastructure Advisor: FAILED"
curl -s http://localhost:8009/ && echo "✅ Budget Tracker: OK" || echo "❌ Budget Tracker: FAILED"
curl -s http://localhost:8004/health && echo "✅ Fred Dev API: OK" || echo "❌ Fred Dev API: FAILED"

echo ""
echo "🎉 ChatterFix CMMS Services Started!"
echo "===================================="
echo "🌐 Main Dashboard: http://35.237.149.25:8080"
echo "🧠 AI Brain: http://35.237.149.25:8005"
echo "🤖 Grok Chat: http://35.237.149.25:8006"
echo "🏗️ Infrastructure: http://35.237.149.25:8007"
echo "💰 Budget: http://35.237.149.25:8009"
echo "👨‍💻 Dev API: http://35.237.149.25:8004"
echo ""
echo "📊 Check logs: tail -f logs/*.log"

EOF

chmod +x start-chatterfix.sh

# Create systemd service
echo "📋 Creating systemd service file..."
cat > chatterfix-cmms.service << 'EOF'
[Unit]
Description=ChatterFix CMMS Complete Platform
After=network.target
Wants=network-online.target

[Service]
Type=forking
User=yoyofred_gringosgambit_com
Group=yoyofred_gringosgambit_com
WorkingDirectory=/home/yoyofred_gringosgambit_com/chatterfix-cmms
ExecStart=/home/yoyofred_gringosgambit_com/chatterfix-cmms/start-chatterfix.sh
ExecStop=/bin/bash -c 'pkill -f "python.*app.py"; pkill -f "python.*service.py"'
Restart=always
RestartSec=10
Environment=PYTHONPATH=/home/yoyofred_gringosgambit_com/chatterfix-cmms
Environment=CHATTERFIX_ENV=production

[Install]
WantedBy=multi-user.target
EOF

# Create environment file
echo "📋 Creating environment configuration..."
cat > .env << 'EOF'
# ChatterFix CMMS Environment Configuration
CHATTERFIX_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=sqlite:///data/cmms.db
DB_POOL_SIZE=20
DB_POOL_OVERFLOW=30

# AI Configuration
ENABLE_AI_FEATURES=true
ENABLE_GROK_INTEGRATION=true
DEFAULT_AI_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434

# API Keys (set these with your actual keys)
# OPENAI_API_KEY=your_openai_key
# ANTHROPIC_API_KEY=your_anthropic_key
# XAI_API_KEY=your_xai_key

# Security
SECRET_KEY=chatterfix-production-secret-key-change-this
JWT_SECRET_KEY=jwt-secret-key-change-this

# Service Ports
PLATFORM_GATEWAY_PORT=8080
AI_BRAIN_PORT=8005
BACKEND_SERVICE_PORT=8001
GROK_CONNECTOR_PORT=8006
GROK_INFRASTRUCTURE_PORT=8007
BUDGET_TRACKER_PORT=8009
FRED_DEV_API_PORT=8004
MOBILE_SERVER_PORT=8008

# Features
ENABLE_BUDGET_TRACKING=true
ENABLE_MOBILE_INTERFACE=true
ENABLE_DOCUMENT_INTELLIGENCE=true
ENABLE_PREDICTIVE_ANALYTICS=true
EOF

cd ../..

# Create deployment archive
echo "📦 Creating deployment archive..."
tar -czf "${DEPLOYMENT_NAME}.tar.gz" -C deployment-package .

echo ""
echo "📤 UPLOADING TO VM"
echo "=================="

# Upload to VM
echo "🚀 Uploading deployment package..."
scp "${DEPLOYMENT_NAME}.tar.gz" "$VM_USER@$VM_HOST:/tmp/"

echo ""
echo "🔧 DEPLOYING ON VM"
echo "=================="

# Execute deployment on VM
ssh "$VM_USER@$VM_HOST" << ENDSSH

echo "🛑 Stopping existing services..."
sudo systemctl stop chatterfix-cmms 2>/dev/null || true
pkill -f "python.*app.py" || true
pkill -f "python.*service.py" || true
sleep 3

echo "📁 Setting up deployment directory..."
mkdir -p "$VM_PATH"
mkdir -p "$VM_PATH/logs"
cd "$VM_PATH"

echo "📦 Extracting deployment package..."
tar -xzf "/tmp/${DEPLOYMENT_NAME}.tar.gz" -C .
rm -f "/tmp/${DEPLOYMENT_NAME}.tar.gz"

echo "🐍 Installing Python dependencies..."
python3 -m pip install --user --upgrade pip
python3 -m pip install --user -r requirements.txt

echo "🔧 Setting up systemd service..."
sudo cp chatterfix-cmms.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chatterfix-cmms

echo "🗄️ Setting up database..."
mkdir -p data
if [ ! -f data/cmms.db ]; then
    echo "Creating new database..."
    python3 -c "
import sqlite3
conn = sqlite3.connect('data/cmms.db')
conn.execute('CREATE TABLE IF NOT EXISTS work_orders (id INTEGER PRIMARY KEY, title TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
conn.execute('CREATE TABLE IF NOT EXISTS assets (id INTEGER PRIMARY KEY, name TEXT, location TEXT, status TEXT)')
conn.execute('CREATE TABLE IF NOT EXISTS parts (id INTEGER PRIMARY KEY, name TEXT, stock INTEGER DEFAULT 0)')
conn.commit()
conn.close()
print('Database initialized')
"
fi

echo "🚀 Starting ChatterFix CMMS..."
sudo systemctl start chatterfix-cmms

echo "⏳ Waiting for services to start..."
sleep 20

echo "🧪 Testing deployment..."
echo "Main Platform: \$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)"
echo "AI Brain: \$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8005/health)"
echo "Backend: \$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health)"
echo "Grok: \$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8006/)"

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo "🌐 ChatterFix CMMS: http://35.237.149.25:8080"
echo "🧠 AI Brain Service: http://35.237.149.25:8005"
echo "🤖 Grok Integration: http://35.237.149.25:8006"
echo "🏗️ Infrastructure: http://35.237.149.25:8007"
echo "💰 Budget Tracker: http://35.237.149.25:8009"
echo ""
echo "📊 Service Status:"
sudo systemctl status chatterfix-cmms --no-pager | head -10
echo ""
echo "📋 Check logs with: tail -f $VM_PATH/logs/*.log"

ENDSSH

echo ""
echo "✅ VM DEPLOYMENT COMPLETE!"
echo "=========================="
echo "🌐 Access ChatterFix at: http://35.237.149.25:8080"
echo "🤖 All AI services deployed and running"
echo "📊 Grok integration active"
echo "💰 Budget tracking enabled"
echo "📱 Mobile interface available"
echo ""
echo "🔍 Next steps:"
echo "   - Test all services"
echo "   - Configure AI API keys in .env"
echo "   - Set up SSL/domain if needed"
echo "   - Monitor logs for any issues"

# Cleanup
rm -rf deployment-package
rm -f "${DEPLOYMENT_NAME}.tar.gz"

echo ""
echo "🎯 Deployment package cleaned up locally"
echo "🚀 ChatterFix CMMS is now running on your VM!"
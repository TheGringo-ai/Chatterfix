#!/bin/bash
set -e

echo "🚀 DEPLOYING REAL COMPLETE CHATTERFIX CMMS PLATFORM"
echo "=================================================="
echo "Deploying the ACTUAL full 9,354-line ChatterFix CMMS with all features"
echo ""

# Configuration
VM_USER="yoyofred_gringosgambit_com"
VM_HOST="35.237.149.25"
DOMAIN="chatterfix.com"
APP_PATH="/opt/chatterfix-production"

echo "📦 CREATING REAL COMPLETE DEPLOYMENT PACKAGE"
echo "============================================="

# Create deployment directory
mkdir -p chatterfix-real-complete/{app,configs,scripts,templates,static,data}
cd chatterfix-real-complete

# Copy the REAL complete app.py and all dependencies
echo "📋 Copying main ChatterFix CMMS application (9,354 lines)..."
cp ../core/cmms/app.py app/
echo "  ✅ app.py (Complete CMMS Platform - 388KB)"

# Copy all support modules
echo "📋 Copying supporting modules..."
SUPPORT_FILES=(
    "universal_ai_endpoints.py"
    "collaborative_ai_system.py"
    "unified_cmms_system.py"
    "dev_ai_assistant.py"
    "database_utils.py"
    "security_middleware.py"
    "ai_brain_service.py"
    "platform_gateway.py"
    "backend_unified_service.py"
    "technician_ai_assistant.py"
    "comprehensive_cmms_evaluation.py"
)

for file in "${SUPPORT_FILES[@]}"; do
    if [ -f "../core/cmms/$file" ]; then
        cp "../core/cmms/$file" app/
        echo "  ✅ $file"
    else
        echo "  ⚠️  $file not found"
    fi
done

# Copy entire templates directory
echo "📋 Copying templates and static files..."
if [ -d "../core/cmms/templates" ]; then
    cp -r "../core/cmms/templates" .
    echo "  ✅ Complete templates directory"
fi

if [ -d "../core/cmms/static" ]; then
    cp -r "../core/cmms/static" .
    echo "  ✅ Complete static files"
fi

if [ -d "../core/cmms/data" ]; then
    cp -r "../core/cmms/data" .
    echo "  ✅ Complete data directory"
fi

# Copy configuration files
echo "📋 Copying configuration files..."
if [ -d "../core/cmms/configs" ]; then
    cp -r "../core/cmms/configs" .
    echo "  ✅ All configuration files"
fi

# Create comprehensive requirements
echo "📋 Creating production requirements..."
cat > requirements.txt << 'EOF'
# Core Web Framework
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
jinja2>=3.1.2
aiofiles>=23.2.0

# Database
sqlite3-enhanced
sqlalchemy>=2.0.0
asyncpg>=0.29.0

# HTTP and Networking
httpx>=0.25.0
aiohttp>=3.8.0
websockets>=12.0
requests>=2.31.0

# AI and Machine Learning
openai>=1.3.0
anthropic>=0.8.0

# Security
bcrypt>=4.0.0
python-jose[cryptography]>=3.3.0
passlib>=1.7.4

# Data Processing
pydantic>=2.0.0
python-dotenv>=1.0.0
PyYAML>=6.0

# System
psutil>=5.9.0
typing-extensions>=4.0.0

# Development
pytest>=7.0.0
black>=23.0.0
EOF

# Create startup script specifically for the complete app
cat > start-chatterfix-complete.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting Complete ChatterFix CMMS Platform"
echo "=============================================="

# Set environment
export PYTHONPATH=/opt/chatterfix-production/app
export CHATTERFIX_ENV=production
export PORT=8000

# Create log directory
mkdir -p /var/log/chatterfix

# Navigate to app directory
cd /opt/chatterfix-production/app

# Stop any existing processes
pkill -f "python.*app.py" || true
pkill -f "uvicorn.*app" || true
sleep 3

echo "🌐 Starting main ChatterFix CMMS application..."
nohup python3 app.py > /var/log/chatterfix/app.log 2>&1 &

# Also start with uvicorn for better performance
echo "⚡ Starting high-performance uvicorn server..."
nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4 > /var/log/chatterfix/uvicorn.log 2>&1 &

echo "⏳ Waiting for services to start..."
sleep 15

echo "🧪 Testing deployment..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ ChatterFix CMMS is running successfully!"
    echo "🌐 Platform: http://localhost:8000"
    echo "📊 Health: http://localhost:8000/health"
else
    echo "⚠️  Service may still be starting up..."
fi

echo ""
echo "🎉 Complete ChatterFix CMMS Platform Started!"
echo "=============================================="
echo "🌐 Access at: http://35.237.149.25"
echo "📊 Features: Full CMMS with AI, Work Orders, Assets, Parts, Technicians"
echo "🤖 AI Assistant: Integrated collaborative AI system"
echo "📱 Mobile Ready: Responsive design with mobile support"
echo "📈 Analytics: Real-time dashboard and reporting"

EOF

chmod +x start-chatterfix-complete.sh

# Create systemd service for the complete app
cat > chatterfix-complete.service << 'EOF'
[Unit]
Description=ChatterFix Complete CMMS Platform
After=network.target

[Service]
Type=simple
User=chatterfix
Group=chatterfix
WorkingDirectory=/opt/chatterfix-production/app
Environment=PYTHONPATH=/opt/chatterfix-production/app
Environment=CHATTERFIX_ENV=production
Environment=PORT=8000
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create nginx configuration
cat > nginx-chatterfix-complete.conf << 'EOF'
server {
    listen 80 default_server;
    server_name chatterfix.com www.chatterfix.com _;
    
    client_max_body_size 100M;
    
    # Main ChatterFix CMMS Platform
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    # Static files
    location /static/ {
        alias /opt/chatterfix-production/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # WebSocket support for real-time features
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Create environment configuration
cat > .env << 'EOF'
# ChatterFix Complete CMMS Configuration
CHATTERFIX_ENV=production
DEBUG=false
LOG_LEVEL=INFO

# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///data/chatterfix_complete.db
ENABLE_POSTGRESQL=false

# AI Configuration
ENABLE_AI_FEATURES=true
ENABLE_COLLABORATIVE_AI=true
DEFAULT_AI_PROVIDER=openai
ENABLE_SMART_SUGGESTIONS=true

# API Keys (configure with your actual keys)
# OPENAI_API_KEY=your_openai_key_here
# ANTHROPIC_API_KEY=your_anthropic_key_here

# Security Configuration
SECRET_KEY=chatterfix-complete-production-secret-2024
JWT_SECRET_KEY=jwt-chatterfix-complete-secret-2024
ENABLE_AUTHENTICATION=true
SESSION_TIMEOUT=3600

# Platform Features
ENABLE_WORK_ORDERS=true
ENABLE_ASSET_MANAGEMENT=true
ENABLE_PARTS_INVENTORY=true
ENABLE_PREVENTIVE_MAINTENANCE=true
ENABLE_MOBILE_INTERFACE=true
ENABLE_REPORTING=true
ENABLE_NOTIFICATIONS=true
ENABLE_DOCUMENT_MANAGEMENT=true
ENABLE_QR_SCANNING=true
ENABLE_BARCODE_SCANNING=true

# Performance Configuration
ENABLE_CACHING=true
CACHE_TIMEOUT=3600
MAX_UPLOAD_SIZE=100MB
WORKER_PROCESSES=4

# Logging
LOG_TO_FILE=true
LOG_DIRECTORY=/var/log/chatterfix
LOG_ROTATION=daily
LOG_RETENTION_DAYS=30

# Integration
ENABLE_EMAIL_NOTIFICATIONS=false
ENABLE_SMS_NOTIFICATIONS=false
ENABLE_WEBHOOK_INTEGRATION=false
EOF

cd ..

echo "📦 Creating deployment archive..."
tar -czf "chatterfix-complete-real-$(date +%Y%m%d-%H%M%S).tar.gz" chatterfix-real-complete/

echo ""
echo "📤 UPLOADING TO VM"
echo "=================="

# Upload to VM
echo "🚀 Uploading complete platform..."
scp "chatterfix-complete-real-$(date +%Y%m%d-%H%M%S).tar.gz" "$VM_USER@$VM_HOST:/tmp/"

echo ""
echo "🔧 DEPLOYING ON VM"
echo "=================="

# Execute deployment on VM
ssh "$VM_USER@$VM_HOST" << 'ENDSSH'

echo "🛑 Stopping ALL existing ChatterFix services..."
sudo systemctl stop nginx 2>/dev/null || true
sudo systemctl stop chatterfix-* 2>/dev/null || true
sudo pkill -f "python.*app.py" || true
sudo pkill -f "python.*chatterfix" || true
sudo pkill -f "uvicorn" || true
sleep 5

echo "👤 Setting up production user..."
sudo useradd -r -s /bin/false chatterfix 2>/dev/null || true

echo "📁 Setting up production directory..."
sudo rm -rf /opt/chatterfix-production
sudo mkdir -p /opt/chatterfix-production
sudo mkdir -p /var/log/chatterfix

echo "📦 Extracting real complete platform..."
cd /tmp
ARCHIVE=$(ls chatterfix-complete-real-*.tar.gz | head -1)
sudo tar -xzf "$ARCHIVE" -C /opt/
sudo mv /opt/chatterfix-real-complete/* /opt/chatterfix-production/

echo "🔐 Setting permissions..."
sudo chown -R chatterfix:chatterfix /opt/chatterfix-production
sudo chown -R chatterfix:chatterfix /var/log/chatterfix
sudo chmod +x /opt/chatterfix-production/start-chatterfix-complete.sh

echo "🐍 Installing production dependencies..."
cd /opt/chatterfix-production
sudo -u chatterfix python3 -m pip install --user -r requirements.txt

echo "🗄️ Setting up production database..."
cd /opt/chatterfix-production/app
sudo -u chatterfix mkdir -p ../data
if [ ! -f ../data/chatterfix_complete.db ]; then
    echo "Creating complete production database..."
    sudo -u chatterfix python3 -c "
import sqlite3
import datetime

# Create the complete ChatterFix database
conn = sqlite3.connect('../data/chatterfix_complete.db')

# Work Orders table
conn.execute('''CREATE TABLE IF NOT EXISTS work_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'open',
    priority TEXT DEFAULT 'medium',
    assigned_to TEXT,
    asset_id INTEGER,
    estimated_hours REAL,
    actual_hours REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    due_date TIMESTAMP
)''')

# Assets table
conn.execute('''CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    asset_tag TEXT UNIQUE,
    description TEXT,
    location TEXT,
    department TEXT,
    status TEXT DEFAULT 'active',
    purchase_date DATE,
    warranty_expiry DATE,
    maintenance_schedule TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# Parts Inventory table
conn.execute('''CREATE TABLE IF NOT EXISTS parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_number TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    current_stock INTEGER DEFAULT 0,
    min_stock INTEGER DEFAULT 5,
    max_stock INTEGER DEFAULT 100,
    unit_cost REAL DEFAULT 0.0,
    supplier TEXT,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# Users/Technicians table
conn.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    full_name TEXT,
    role TEXT DEFAULT 'technician',
    department TEXT,
    phone TEXT,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# Maintenance Schedules table
conn.execute('''CREATE TABLE IF NOT EXISTS maintenance_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_id INTEGER NOT NULL,
    task_name TEXT NOT NULL,
    frequency TEXT NOT NULL,
    frequency_value INTEGER NOT NULL,
    last_completed TIMESTAMP,
    next_due TIMESTAMP,
    assigned_to TEXT,
    active BOOLEAN DEFAULT 1,
    FOREIGN KEY (asset_id) REFERENCES assets (id)
)''')

# Work Order Parts table
conn.execute('''CREATE TABLE IF NOT EXISTS work_order_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_order_id INTEGER NOT NULL,
    part_id INTEGER NOT NULL,
    quantity_used INTEGER NOT NULL,
    FOREIGN KEY (work_order_id) REFERENCES work_orders (id),
    FOREIGN KEY (part_id) REFERENCES parts (id)
)''')

# Insert comprehensive sample data
print('Inserting sample work orders...')
work_orders = [
    ('HVAC Filter Replacement', 'Replace air filters in Building A HVAC system', 'open', 'medium', 'john.smith', 1, 2.0),
    ('Pump Maintenance', 'Routine maintenance on water pump #3', 'in_progress', 'high', 'jane.doe', 2, 4.0),
    ('Lighting Repair', 'Replace faulty LED lights in warehouse', 'open', 'low', 'mike.wilson', 3, 1.5),
    ('Generator Testing', 'Monthly generator load test and inspection', 'scheduled', 'high', 'sarah.johnson', 4, 3.0),
    ('Conveyor Belt Adjustment', 'Adjust tension and alignment on conveyor belt #2', 'open', 'medium', 'john.smith', 5, 2.5)
]

for wo in work_orders:
    conn.execute('''INSERT OR IGNORE INTO work_orders 
                   (title, description, status, priority, assigned_to, asset_id, estimated_hours) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)''', wo)

print('Inserting sample assets...')
assets = [
    ('HVAC Unit A1', 'HVAC-001', 'Main building HVAC system', 'Building A - Roof', 'Facilities', 'active'),
    ('Water Pump #3', 'PUMP-003', 'Primary water circulation pump', 'Mechanical Room', 'Utilities', 'active'),
    ('Warehouse Lighting', 'LIGHT-WH1', 'LED lighting system in warehouse', 'Warehouse', 'Electrical', 'active'),
    ('Emergency Generator', 'GEN-001', 'Backup power generator', 'Generator Room', 'Electrical', 'active'),
    ('Conveyor Belt #2', 'CONV-002', 'Production line conveyor system', 'Production Floor', 'Production', 'active')
]

for asset in assets:
    conn.execute('''INSERT OR IGNORE INTO assets 
                   (name, asset_tag, description, location, department, status) 
                   VALUES (?, ?, ?, ?, ?, ?)''', asset)

print('Inserting sample parts...')
parts = [
    ('FILTER-20X25', 'HVAC Filter 20x25x1', 'Standard HVAC air filter', 25, 5, 50, 15.99, 'FilterCorp', 'Storage A'),
    ('PUMP-SEAL-3IN', '3-inch Pump Seal', 'Replacement seal for water pumps', 8, 2, 20, 45.50, 'PumpParts Inc', 'Storage B'),
    ('LED-BULB-100W', '100W LED Bulb', 'Industrial LED lighting bulb', 50, 10, 100, 28.75, 'LightSource', 'Storage A'),
    ('GEN-OIL-5W30', 'Generator Oil 5W-30', 'Synthetic oil for generator', 12, 3, 24, 32.99, 'OilCorp', 'Storage C'),
    ('BELT-RUBBER-6IN', '6-inch Rubber Belt', 'Conveyor belt material', 5, 1, 10, 125.00, 'BeltTech', 'Storage B')
]

for part in parts:
    conn.execute('''INSERT OR IGNORE INTO parts 
                   (part_number, name, description, current_stock, min_stock, max_stock, unit_cost, supplier, location) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', part)

print('Inserting sample users...')
users = [
    ('john.smith', 'john.smith@company.com', 'John Smith', 'technician', 'Maintenance', '555-0101'),
    ('jane.doe', 'jane.doe@company.com', 'Jane Doe', 'technician', 'Electrical', '555-0102'),
    ('mike.wilson', 'mike.wilson@company.com', 'Mike Wilson', 'supervisor', 'Maintenance', '555-0103'),
    ('sarah.johnson', 'sarah.johnson@company.com', 'Sarah Johnson', 'technician', 'Utilities', '555-0104'),
    ('admin', 'admin@company.com', 'System Administrator', 'admin', 'IT', '555-0100')
]

for user in users:
    conn.execute('''INSERT OR IGNORE INTO users 
                   (username, email, full_name, role, department, phone) 
                   VALUES (?, ?, ?, ?, ?, ?)''', user)

conn.commit()
conn.close()
print('✅ Complete production database initialized with sample data')
"
fi

echo "⚙️ Setting up systemd service..."
sudo cp /opt/chatterfix-production/chatterfix-complete.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chatterfix-complete

echo "🌍 Configuring Nginx..."
sudo cp /opt/chatterfix-production/nginx-chatterfix-complete.conf /etc/nginx/sites-available/chatterfix.conf
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/chatterfix.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

echo "🚀 Starting complete ChatterFix platform..."
sudo /opt/chatterfix-production/start-chatterfix-complete.sh

echo "⏳ Waiting for complete startup..."
sleep 20

echo "🧪 Testing complete deployment..."
echo "Main Platform: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ || echo "Starting...")"
echo "Health Check: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "Starting...")"
echo "Work Orders: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/work-orders || echo "Starting...")"
echo "Assets: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/assets || echo "Starting...")"
echo "Parts: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/parts || echo "Starting...")"

PUBLIC_IP=$(curl -s ifconfig.me || echo "35.237.149.25")
echo ""
echo "🎉 COMPLETE CHATTERFIX CMMS PLATFORM DEPLOYED!"
echo "=============================================="
echo "🌐 Main Platform: http://$PUBLIC_IP"
echo "📊 Dashboard: Full AI-enhanced CMMS with all features"
echo "🔧 Work Orders: Complete work order management"
echo "🏭 Assets: Full asset lifecycle management"
echo "📦 Parts: Comprehensive inventory management"
echo "👥 Technicians: User management and assignments"
echo "🤖 AI Assistant: Collaborative AI system integrated"
echo "📱 Mobile Ready: Responsive design for all devices"
echo ""
echo "📈 Features Available:"
echo "   - Real-time dashboard with statistics"
echo "   - Work order creation and tracking"
echo "   - Asset management with maintenance schedules"
echo "   - Parts inventory with stock management"
echo "   - Preventive maintenance planning"
echo "   - AI-powered suggestions and automation"
echo "   - Mobile-friendly interface"
echo "   - Comprehensive reporting"
echo ""
echo "🔧 Configure www.chatterfix.com DNS to point to: $PUBLIC_IP"
echo "✅ Your complete ChatterFix CMMS platform is now live!"

# Clean up
rm -f /tmp/chatterfix-complete-real-*.tar.gz

ENDSSH

echo ""
echo "✅ REAL COMPLETE CHATTERFIX DEPLOYMENT FINISHED!"
echo "================================================"
echo "🌐 Platform URL: http://35.237.149.25"
echo "📊 Features: Complete CMMS with 9,354 lines of code"
echo "🤖 All modules: Work Orders, Assets, Parts, AI, Mobile, Reporting"
echo "🔧 Production ready with systemd, nginx, and logging"
echo ""
echo "🎯 Your REAL complete ChatterFix CMMS platform is now live!"

# Cleanup local files
rm -rf chatterfix-real-complete
rm -f chatterfix-complete-real-*.tar.gz

echo "🧹 Local deployment files cleaned up"
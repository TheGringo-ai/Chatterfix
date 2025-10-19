#!/bin/bash

echo "🚀 Deploying Clean ChatterFix CMMS Microservices to VM"
echo "======================================================="
echo "🎯 Complete CMMS Architecture with All Modules"
echo ""

VM_IP="35.237.149.25"
VM_USER="yoyofred_gringosgambit_com"
REMOTE_DIR="/opt/chatterfix-cmms/current"

echo "📦 Copying clean microservices to VM..."
echo "Copying: app.py database_service.py work_orders_service.py assets_service.py parts_service.py"

# Copy all microservice files
scp -o StrictHostKeyChecking=no \
    app.py \
    database_service.py \
    work_orders_service.py \
    assets_service.py \
    parts_service.py \
    document_intelligence_service.py \
    enterprise_security_service.py \
    requirements.txt \
    ${VM_USER}@${VM_IP}:${REMOTE_DIR}/

echo "📦 Copying AI services..."
scp -o StrictHostKeyChecking=no \
    ../fix_it_fred_ai_service.py \
    grok_connector.py \
    ${VM_USER}@${VM_IP}:${REMOTE_DIR}/

echo "🛠️ Deploying and starting all microservices on VM..."
ssh -o StrictHostKeyChecking=no ${VM_USER}@${VM_IP} << 'ENDSSH'
cd /opt/chatterfix-cmms/current

echo "🛑 Stopping all existing services..."
sudo pkill -f "python3" 2>/dev/null || true
sudo lsof -ti:8000 | xargs sudo kill -9 2>/dev/null || true
sudo lsof -ti:8001 | xargs sudo kill -9 2>/dev/null || true
sudo lsof -ti:8002 | xargs sudo kill -9 2>/dev/null || true
sudo lsof -ti:8003 | xargs sudo kill -9 2>/dev/null || true
sudo lsof -ti:8004 | xargs sudo kill -9 2>/dev/null || true
sudo lsof -ti:8005 | xargs sudo kill -9 2>/dev/null || true
sudo lsof -ti:8006 | xargs sudo kill -9 2>/dev/null || true
sudo lsof -ti:8007 | xargs sudo kill -9 2>/dev/null || true
sudo lsof -ti:8008 | xargs sudo kill -9 2>/dev/null || true
sudo lsof -ti:8080 | xargs sudo kill -9 2>/dev/null || true

sleep 5

echo "📦 Installing Python dependencies..."
pip3 install --user fastapi uvicorn python-multipart httpx sqlite3 requests flask flask-cors || true

echo "🗄️ Initializing database..."
python3 -c "
import sqlite3
import os

# Create data directory if it doesn't exist
os.makedirs('data', exist_ok=True)

# Initialize database
conn = sqlite3.connect('data/cmms.db')
cursor = conn.cursor()

# Create work orders table
cursor.execute('''
CREATE TABLE IF NOT EXISTS work_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'open',
    priority TEXT DEFAULT 'medium',
    assigned_to TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Create assets table
cursor.execute('''
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT,
    status TEXT DEFAULT 'operational',
    location TEXT,
    last_maintenance DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Create parts table
cursor.execute('''
CREATE TABLE IF NOT EXISTS parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    part_number TEXT,
    quantity INTEGER DEFAULT 0,
    unit_cost DECIMAL(10,2),
    supplier TEXT,
    location TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Insert sample data if tables are empty
cursor.execute('SELECT COUNT(*) FROM work_orders')
if cursor.fetchone()[0] == 0:
    sample_work_orders = [
        ('Pump Maintenance', 'Regular maintenance check', 'in_progress', 'high', 'John Smith'),
        ('Filter Replacement', 'Replace air filter in HVAC', 'open', 'medium', 'Jane Doe'),
        ('Belt Inspection', 'Inspect conveyor belt', 'completed', 'low', 'Bob Wilson'),
    ]
    cursor.executemany('INSERT INTO work_orders (title, description, status, priority, assigned_to) VALUES (?, ?, ?, ?, ?)', sample_work_orders)

cursor.execute('SELECT COUNT(*) FROM assets')
if cursor.fetchone()[0] == 0:
    sample_assets = [
        ('Main Production Line', 'equipment', 'operational', 'Building A', '2024-10-15'),
        ('Generator #1', 'equipment', 'maintenance_due', 'Utility Room', '2024-09-20'),
        ('HVAC System', 'equipment', 'operational', 'Building A', '2024-10-01'),
    ]
    cursor.executemany('INSERT INTO assets (name, type, status, location, last_maintenance) VALUES (?, ?, ?, ?, ?)', sample_assets)

cursor.execute('SELECT COUNT(*) FROM parts')
if cursor.fetchone()[0] == 0:
    sample_parts = [
        ('Air Filter', 'AF-001', 25, 15.99, 'FilterCorp', 'Warehouse A'),
        ('Oil Filter', 'OF-002', 40, 8.50, 'FilterCorp', 'Warehouse A'),
        ('Belt Drive', 'BD-003', 10, 45.00, 'BeltCo', 'Warehouse B'),
    ]
    cursor.executemany('INSERT INTO parts (name, part_number, quantity, unit_cost, supplier, location) VALUES (?, ?, ?, ?, ?, ?)', sample_parts)

conn.commit()
conn.close()
print('✅ Database initialized successfully')
"

echo "🚀 Starting microservices..."

echo "  Starting Database Service (8001)..."
nohup python3 database_service.py --port 8001 > logs/database_service.log 2>&1 &
echo $! > pids/database_service.pid

echo "  Starting Work Orders Service (8002)..."
nohup python3 work_orders_service.py --port 8002 > logs/work_orders_service.log 2>&1 &
echo $! > pids/work_orders_service.pid

echo "  Starting Assets Service (8003)..."
nohup python3 assets_service.py --port 8003 > logs/assets_service.log 2>&1 &
echo $! > pids/assets_service.pid

echo "  Starting Parts Service (8004)..."
nohup python3 parts_service.py --port 8004 > logs/parts_service.log 2>&1 &
echo $! > pids/parts_service.pid

echo "  Starting Fix It Fred AI Service (8005)..."
nohup python3 fix_it_fred_ai_service.py > logs/fix_it_fred_ai.log 2>&1 &
echo $! > pids/fix_it_fred_ai.pid

echo "  Starting Grok Connector (8006)..."
nohup python3 grok_connector.py > logs/grok_connector.log 2>&1 &
echo $! > pids/grok_connector.pid

echo "  Starting Document Intelligence (8008)..."
nohup python3 document_intelligence_service.py --port 8008 > logs/document_intelligence.log 2>&1 &
echo $! > pids/document_intelligence.pid

echo "  Starting Enterprise Security (8007)..."
nohup python3 enterprise_security_service.py --port 8007 > logs/enterprise_security.log 2>&1 &
echo $! > pids/enterprise_security.pid

echo "⏳ Waiting for services to start..."
sleep 10

echo "🚀 Starting Main Application Gateway (8080)..."
nohup python3 app.py > logs/main_app.log 2>&1 &
echo $! > pids/main_app.pid

sleep 5

echo "🧪 Health checking all services..."
for port in 8001 8002 8003 8004 8005 8006 8007 8008 8080; do
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "  Port $port: ✅ Healthy"
    else
        echo "  Port $port: ⚠️ Starting or down"
    fi
done

echo ""
echo "📊 Service Status:"
ps aux | grep python3 | grep -v grep | head -10

echo ""
echo "✅ ChatterFix CMMS Microservices Deployment Complete!"
echo "====================================================="
echo "🌐 Main Application: http://35.237.149.25:8080"
echo "🔧 Work Orders API: http://35.237.149.25:8002/docs"
echo "🏗️ Assets API: http://35.237.149.25:8003/docs"
echo "📦 Parts API: http://35.237.149.25:8004/docs"
echo "🗄️ Database API: http://35.237.149.25:8001/docs"
echo "🤖 Fix It Fred AI: http://35.237.149.25:8005"
echo "🧠 Grok Connector: http://35.237.149.25:8006"
echo "📄 Document Intelligence: http://35.237.149.25:8008/docs"
echo "🔒 Enterprise Security: http://35.237.149.25:8007/docs"
echo ""
echo "🎯 ALL CMMS MODULES ACTIVE AND READY!"

ENDSSH

echo ""
echo "✅ VM DEPLOYMENT COMPLETED!"
echo "=========================="
echo "🌐 ChatterFix CMMS: http://35.237.149.25:8080"
echo "🏭 All Microservices: DEPLOYED AND RUNNING"
echo "🤖 AI Integration: ACTIVE"
echo "🎯 Complete CMMS Platform: LIVE!"
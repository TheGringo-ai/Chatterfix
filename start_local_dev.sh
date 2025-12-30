#!/bin/bash
# ChatterFix CMMS - Local Development Startup Script

echo "🚀 Starting ChatterFix CMMS Local Development Environment..."

# Set environment
export ENVIRONMENT=development
export ENV_FILE=.env.local

# Check if virtual environment exists
if [ ! -d "core/cmms/venv" ]; then
    echo "📦 Creating Python virtual environment..."
    cd core/cmms
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ../..
fi

# Activate virtual environment
echo "🐍 Activating Python environment..."
source core/cmms/venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
cd core/cmms
pip install -r requirements.txt

# Create local database
echo "🗄️ Setting up local database..."
if [ ! -f "chatterfix_local.db" ]; then
    echo "Creating local SQLite database..."
    python3 -c "
import sqlite3
import os

# Create database and basic tables
conn = sqlite3.connect('chatterfix_local.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
CREATE TABLE IF NOT EXISTS work_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'open',
    assigned_to TEXT,
    asset_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    location TEXT,
    status TEXT DEFAULT 'active',
    asset_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    part_number TEXT UNIQUE,
    description TEXT,
    category TEXT,
    quantity INTEGER DEFAULT 0,
    min_stock INTEGER DEFAULT 0,
    unit_cost REAL DEFAULT 0.0,
    location TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Insert sample data
cursor.execute('''
INSERT OR IGNORE INTO assets (name, description, location, asset_type) VALUES 
('HVAC Unit 1', 'Main building HVAC system', 'Building A - Roof', 'HVAC'),
('Generator 1', 'Emergency backup generator', 'Building B - Basement', 'Power'),
('Conveyor Belt 1', 'Production line conveyor', 'Factory Floor - Line 1', 'Production')
''')

cursor.execute('''
INSERT OR IGNORE INTO parts (name, part_number, description, category, quantity, min_stock, unit_cost, location) VALUES 
('Air Filter', 'AF-001', 'HVAC air filter', 'HVAC', 50, 10, 25.99, 'Warehouse A'),
('Belt Drive', 'BD-002', 'Conveyor belt drive', 'Mechanical', 20, 5, 149.99, 'Warehouse B'),
('Oil Filter', 'OF-003', 'Generator oil filter', 'Engine', 15, 3, 39.99, 'Warehouse A')
''')

cursor.execute('''
INSERT OR IGNORE INTO work_orders (title, description, priority, status, asset_id) VALUES 
('Replace HVAC Filter', 'Monthly filter replacement for HVAC Unit 1', 'medium', 'open', 1),
('Generator Maintenance', 'Quarterly maintenance check for Generator 1', 'high', 'in_progress', 2),
('Conveyor Inspection', 'Weekly safety inspection of conveyor belt', 'low', 'open', 3)
''')

conn.commit()
conn.close()
print('✅ Local database created with sample data')
"
fi

echo "🌐 Starting development servers..."

# Start services in background
echo "Starting UI Gateway on port 8080..."
ENV_FILE=../../.env.local python3 app.py &
echo $! > ../../pids/gateway.pid

sleep 2

echo "Starting AI Brain Service on port 8005..."
ENV_FILE=../../.env.local PORT=8005 python3 ai_brain_service.py &
echo $! > ../../pids/ai_brain.pid

sleep 2

echo "Starting Claude Code Assistant on port 8009..."
ENV_FILE=../../.env.local PORT=8009 python3 claude_code_assistant.py &
echo $! > ../../pids/claude_code.pid

sleep 2

echo "Starting Database Service on port 8001..."
ENV_FILE=../../.env.local PORT=8001 python3 database_service.py &
echo $! > ../../pids/database.pid

sleep 2

cd ../..

echo ""
echo "🎉 ChatterFix CMMS Development Environment Started!"
echo ""
echo "🌐 Services Running:"
echo "   • UI Gateway:         http://localhost:8080"
echo "   • AI Brain Service:   http://localhost:8005"
echo "   • Claude Code Assistant: http://localhost:8009"
echo "   • Database Service:   http://localhost:8001"
echo ""
echo "🛠️ Development URLs:"
echo "   • Main Dashboard:     http://localhost:8080"
echo "   • API Docs:          http://localhost:8080/docs"
echo "   • Claude Code Help:   http://localhost:8009/docs"
echo ""
echo "📋 To stop all services: ./stop_local_dev.sh"
echo "📊 To view logs: tail -f core/cmms/logs/*.log"
echo ""
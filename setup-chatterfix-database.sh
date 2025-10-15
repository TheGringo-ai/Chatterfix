#!/bin/bash
# ChatterFix CMMS Database Setup Script
set -e

echo "🗄️ Setting up ChatterFix CMMS PostgreSQL Database..."
echo "=================================================="

# Database connection info
DB_INSTANCE="chatterfix-saas-db"
DB_NAME="chatterfix_cmms"
DB_USER="postgres"
DB_HOST="35.225.244.14"

echo "📊 Creating comprehensive CMMS database schema..."

# Create SQL schema file
cat > cmms_schema.sql << 'EOF'
-- ChatterFix CMMS Database Schema
-- Complete maintenance management system

-- Drop existing tables if they exist
DROP TABLE IF EXISTS work_order_parts CASCADE;
DROP TABLE IF EXISTS work_order_tasks CASCADE;
DROP TABLE IF EXISTS work_orders CASCADE;
DROP TABLE IF EXISTS maintenance_schedules CASCADE;
DROP TABLE IF EXISTS asset_parts CASCADE;
DROP TABLE IF EXISTS parts_inventory CASCADE;
DROP TABLE IF EXISTS assets CASCADE;
DROP TABLE IF EXISTS locations CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS categories CASCADE;

-- Categories for assets and parts
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    category_type VARCHAR(20) CHECK (category_type IN ('asset', 'part')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users (technicians, managers, etc.)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) UNIQUE,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'technician' CHECK (role IN ('technician', 'manager', 'admin')),
    phone VARCHAR(20),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations/Facilities
CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    building VARCHAR(50),
    floor VARCHAR(20),
    room VARCHAR(20),
    coordinates POINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assets/Equipment
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    asset_tag VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES categories(id),
    location_id INTEGER REFERENCES locations(id),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    purchase_date DATE,
    purchase_cost DECIMAL(10,2),
    warranty_expiry DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'maintenance', 'retired', 'repair')),
    criticality VARCHAR(10) DEFAULT 'medium' CHECK (criticality IN ('low', 'medium', 'high', 'critical')),
    installation_date DATE,
    last_maintenance DATE,
    next_maintenance DATE,
    operating_hours INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Parts Inventory
CREATE TABLE parts_inventory (
    id SERIAL PRIMARY KEY,
    part_number VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id INTEGER REFERENCES categories(id),
    manufacturer VARCHAR(100),
    supplier VARCHAR(100),
    unit_cost DECIMAL(10,2),
    quantity_on_hand INTEGER DEFAULT 0,
    min_stock_level INTEGER DEFAULT 0,
    max_stock_level INTEGER DEFAULT 0,
    reorder_point INTEGER DEFAULT 0,
    unit_of_measure VARCHAR(20) DEFAULT 'each',
    location VARCHAR(100),
    bin_location VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'discontinued', 'obsolete')),
    last_ordered DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Asset-Parts relationship (what parts belong to which assets)
CREATE TABLE asset_parts (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    part_id INTEGER REFERENCES parts_inventory(id),
    quantity_required INTEGER DEFAULT 1,
    replacement_frequency_days INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Maintenance Schedules
CREATE TABLE maintenance_schedules (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    schedule_name VARCHAR(200) NOT NULL,
    description TEXT,
    frequency_type VARCHAR(20) CHECK (frequency_type IN ('daily', 'weekly', 'monthly', 'quarterly', 'yearly', 'hours', 'usage')),
    frequency_value INTEGER NOT NULL,
    estimated_duration INTEGER, -- in minutes
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    assigned_to INTEGER REFERENCES users(id),
    next_due_date DATE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Work Orders
CREATE TABLE work_orders (
    id SERIAL PRIMARY KEY,
    work_order_number VARCHAR(50) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    asset_id INTEGER REFERENCES assets(id),
    location_id INTEGER REFERENCES locations(id),
    work_type VARCHAR(20) DEFAULT 'corrective' CHECK (work_type IN ('preventive', 'corrective', 'emergency', 'inspection', 'upgrade')),
    priority VARCHAR(10) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'assigned', 'in_progress', 'completed', 'closed', 'cancelled')),
    requested_by INTEGER REFERENCES users(id),
    assigned_to INTEGER REFERENCES users(id),
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    estimated_cost DECIMAL(10,2),
    actual_cost DECIMAL(10,2),
    due_date DATE,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Work Order Tasks (subtasks within work orders)
CREATE TABLE work_order_tasks (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id) ON DELETE CASCADE,
    task_description TEXT NOT NULL,
    estimated_minutes INTEGER,
    actual_minutes INTEGER,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'skipped')),
    assigned_to INTEGER REFERENCES users(id),
    completed_by INTEGER REFERENCES users(id),
    completed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Work Order Parts (parts used in work orders)
CREATE TABLE work_order_parts (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id) ON DELETE CASCADE,
    part_id INTEGER REFERENCES parts_inventory(id),
    quantity_requested INTEGER NOT NULL,
    quantity_used INTEGER DEFAULT 0,
    unit_cost DECIMAL(10,2),
    total_cost DECIMAL(10,2),
    issued_at TIMESTAMP,
    returned_quantity INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_assets_status ON assets(status);
CREATE INDEX idx_assets_location ON assets(location_id);
CREATE INDEX idx_assets_category ON assets(category_id);
CREATE INDEX idx_assets_next_maintenance ON assets(next_maintenance);

CREATE INDEX idx_work_orders_status ON work_orders(status);
CREATE INDEX idx_work_orders_asset ON work_orders(asset_id);
CREATE INDEX idx_work_orders_assigned ON work_orders(assigned_to);
CREATE INDEX idx_work_orders_due_date ON work_orders(due_date);
CREATE INDEX idx_work_orders_created ON work_orders(created_at);

CREATE INDEX idx_parts_quantity ON parts_inventory(quantity_on_hand);
CREATE INDEX idx_parts_reorder ON parts_inventory(reorder_point);
CREATE INDEX idx_parts_status ON parts_inventory(status);

-- Insert sample data for testing
INSERT INTO categories (name, description, category_type) VALUES 
('HVAC', 'Heating, Ventilation, Air Conditioning', 'asset'),
('Electrical', 'Electrical equipment and components', 'asset'),
('Mechanical', 'Mechanical systems and machinery', 'asset'),
('Filters', 'Air and fluid filters', 'part'),
('Belts', 'Drive belts and timing belts', 'part'),
('Electrical Components', 'Wires, switches, relays', 'part');

INSERT INTO locations (name, address, building, floor) VALUES 
('Main Building', '123 Industrial Way', 'Building A', '1'),
('Warehouse', '123 Industrial Way', 'Building B', '1'),
('Office Complex', '123 Industrial Way', 'Building C', '2');

INSERT INTO users (username, email, full_name, role) VALUES 
('jsmith', 'john.smith@company.com', 'John Smith', 'technician'),
('mwilson', 'mary.wilson@company.com', 'Mary Wilson', 'manager'),
('bgreen', 'bob.green@company.com', 'Bob Green', 'technician');

-- Sample assets
INSERT INTO assets (asset_tag, name, description, category_id, location_id, manufacturer, model, status, criticality) VALUES 
('HVAC-001', 'Main HVAC Unit', 'Primary building HVAC system', 1, 1, 'Carrier', 'Model-XYZ', 'active', 'critical'),
('PUMP-001', 'Water Pump #1', 'Primary water circulation pump', 3, 2, 'Grundfos', 'CR-150', 'active', 'high'),
('GEN-001', 'Emergency Generator', 'Backup power generator', 2, 2, 'Generac', 'RG048', 'active', 'critical');

-- Sample parts
INSERT INTO parts_inventory (part_number, name, description, category_id, quantity_on_hand, min_stock_level, reorder_point, unit_cost) VALUES 
('FILTER-001', 'HVAC Air Filter 20x25x4', 'High-efficiency particulate filter', 4, 25, 5, 10, 45.99),
('BELT-001', 'V-Belt A-Section 48"', 'Standard V-belt for pumps', 5, 8, 2, 5, 12.50),
('RELAY-001', '24V Control Relay', 'DPDT control relay', 6, 15, 3, 8, 23.75);

-- Sample work order
INSERT INTO work_orders (work_order_number, title, description, asset_id, work_type, priority, status, requested_by, assigned_to) VALUES 
('WO-2025-001', 'HVAC Filter Replacement', 'Replace air filters in main HVAC unit', 1, 'preventive', 'medium', 'open', 2, 1);

-- Functions to automatically generate work order numbers
CREATE OR REPLACE FUNCTION generate_work_order_number()
RETURNS TRIGGER AS $$
DECLARE
    next_num INTEGER;
    year_part TEXT;
BEGIN
    IF NEW.work_order_number IS NULL THEN
        year_part := EXTRACT(year FROM CURRENT_DATE)::TEXT;
        
        SELECT COALESCE(MAX(CAST(SUBSTRING(work_order_number FROM '\\d+$') AS INTEGER)), 0) + 1
        INTO next_num
        FROM work_orders 
        WHERE work_order_number LIKE 'WO-' || year_part || '-%';
        
        NEW.work_order_number := 'WO-' || year_part || '-' || LPAD(next_num::TEXT, 3, '0');
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_generate_work_order_number
    BEFORE INSERT ON work_orders
    FOR EACH ROW
    EXECUTE FUNCTION generate_work_order_number();

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_work_orders_updated_at
    BEFORE UPDATE ON work_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_update_parts_updated_at
    BEFORE UPDATE ON parts_inventory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE VIEW active_work_orders AS
SELECT 
    wo.id,
    wo.work_order_number,
    wo.title,
    wo.priority,
    wo.status,
    wo.due_date,
    a.asset_tag,
    a.name as asset_name,
    u.full_name as assigned_to_name,
    wo.created_at
FROM work_orders wo
LEFT JOIN assets a ON wo.asset_id = a.id
LEFT JOIN users u ON wo.assigned_to = u.id
WHERE wo.status NOT IN ('completed', 'closed', 'cancelled')
ORDER BY wo.priority DESC, wo.due_date ASC;

CREATE VIEW low_stock_parts AS
SELECT 
    part_number,
    name,
    quantity_on_hand,
    min_stock_level,
    reorder_point,
    (reorder_point - quantity_on_hand) as shortage_quantity,
    unit_cost
FROM parts_inventory 
WHERE quantity_on_hand <= reorder_point 
    AND status = 'active'
ORDER BY (reorder_point - quantity_on_hand) DESC;

CREATE VIEW asset_maintenance_due AS
SELECT 
    a.asset_tag,
    a.name,
    a.next_maintenance,
    a.criticality,
    l.name as location_name,
    CASE 
        WHEN a.next_maintenance < CURRENT_DATE THEN 'OVERDUE'
        WHEN a.next_maintenance <= CURRENT_DATE + INTERVAL '7 days' THEN 'DUE_SOON'
        ELSE 'SCHEDULED'
    END as maintenance_status
FROM assets a
LEFT JOIN locations l ON a.location_id = l.id
WHERE a.next_maintenance IS NOT NULL 
    AND a.status = 'active'
    AND a.next_maintenance <= CURRENT_DATE + INTERVAL '30 days'
ORDER BY a.next_maintenance ASC;

COMMIT;
EOF

echo "🔌 Applying database schema..."
gcloud sql connect $DB_INSTANCE --user=$DB_USER --database=$DB_NAME --quiet < cmms_schema.sql

echo "✅ Database schema created successfully!"

# Create Python database connection module
cat > database_config.py << 'EOF'
"""
ChatterFix CMMS Database Configuration
PostgreSQL connection and utilities
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

# Database configuration
DB_CONFIG = {
    'host': '35.225.244.14',
    'database': 'chatterfix_cmms',
    'user': 'postgres',
    'password': os.getenv('DB_PASSWORD', ''),  # Set via environment variable
    'port': 5432
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        yield conn
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()

def execute_query(query, params=None, fetch=True):
    """Execute a database query"""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch and cur.description:
                return cur.fetchall()
            conn.commit()
            return cur.rowcount

# Common CMMS queries
class CMMSQueries:
    @staticmethod
    def get_active_work_orders():
        return execute_query("SELECT * FROM active_work_orders")
    
    @staticmethod
    def get_low_stock_parts():
        return execute_query("SELECT * FROM low_stock_parts")
    
    @staticmethod
    def get_assets_due_maintenance():
        return execute_query("SELECT * FROM asset_maintenance_due")
    
    @staticmethod
    def create_work_order(title, description, asset_id=None, priority='medium', requested_by=1):
        query = """
        INSERT INTO work_orders (title, description, asset_id, priority, requested_by) 
        VALUES (%s, %s, %s, %s, %s) 
        RETURNING id, work_order_number
        """
        result = execute_query(query, (title, description, asset_id, priority, requested_by))
        return result[0] if result else None
    
    @staticmethod
    def get_asset_by_tag(asset_tag):
        query = "SELECT * FROM assets WHERE asset_tag = %s"
        result = execute_query(query, (asset_tag,))
        return result[0] if result else None
    
    @staticmethod
    def update_part_quantity(part_id, quantity_used):
        query = """
        UPDATE parts_inventory 
        SET quantity_on_hand = quantity_on_hand - %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s
        """
        return execute_query(query, (quantity_used, part_id), fetch=False)

def test_connection():
    """Test database connection"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                logger.info(f"Connected to: {version}")
                return True
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return False

if __name__ == "__main__":
    if test_connection():
        print("✅ Database connection successful!")
        
        # Show some sample data
        work_orders = CMMSQueries.get_active_work_orders()
        print(f"\n📋 Active Work Orders: {len(work_orders)}")
        
        low_stock = CMMSQueries.get_low_stock_parts()
        print(f"📦 Low Stock Parts: {len(low_stock)}")
        
        maintenance_due = CMMSQueries.get_assets_due_maintenance()
        print(f"🔧 Assets Due Maintenance: {len(maintenance_due)}")
    else:
        print("❌ Database connection failed!")
EOF

echo ""
echo "🎯 CHATTERFIX DATABASE SETUP COMPLETE!"
echo "======================================"
echo ""
echo "✅ Created comprehensive CMMS schema with:"
echo "   • Assets & Equipment tracking"
echo "   • Parts Inventory management" 
echo "   • Work Order system"
echo "   • Maintenance Scheduling"
echo "   • User management"
echo "   • Location tracking"
echo ""
echo "📊 Database includes:"
echo "   • 11 main tables with relationships"
echo "   • Automated work order numbering"
echo "   • Useful views for common queries"
echo "   • Sample data for testing"
echo ""
echo "🔌 Connection Details:"
echo "   • Host: 35.225.244.14"
echo "   • Database: chatterfix_cmms" 
echo "   • User: postgres"
echo ""
echo "📄 Files created:"
echo "   • cmms_schema.sql - Database schema"
echo "   • database_config.py - Python connection module"
echo ""
echo "🚀 Next: Update your ChatterFix app to use this database!"
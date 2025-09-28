-- ChatterFix CMMS PostgreSQL Schema
-- Converted from SQLite to PostgreSQL format
-- Budget-optimized for Cloud SQL micro instance

-- Create database
-- This will be done via gcloud, not in this script

-- Enable required extensions
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) DEFAULT 'technician',
    department VARCHAR(50),
    phone VARCHAR(20),
    hire_date DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assets table
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    manufacturer VARCHAR(100),
    location_id INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    health_score INTEGER DEFAULT 100,
    last_maintenance DATE,
    next_maintenance DATE,
    purchase_date DATE,
    purchase_cost DECIMAL(10,2),
    notes TEXT,
    qr_code VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Work Orders table
CREATE TABLE IF NOT EXISTS work_orders (
    id SERIAL PRIMARY KEY,
    work_order_number VARCHAR(20) UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    asset_id INTEGER,
    priority VARCHAR(20) DEFAULT 'Medium',
    status VARCHAR(20) DEFAULT 'Open',
    work_type VARCHAR(50),
    assigned_to INTEGER,
    created_by INTEGER,
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    scheduled_start TIMESTAMP,
    scheduled_end TIMESTAMP,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP,
    completion_notes TEXT,
    safety_notes TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Parts table
CREATE TABLE IF NOT EXISTS parts (
    id SERIAL PRIMARY KEY,
    part_number VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    supplier_id INTEGER,
    unit_cost DECIMAL(10,2),
    stock_quantity INTEGER DEFAULT 0,
    min_stock_level INTEGER DEFAULT 0,
    max_stock_level INTEGER DEFAULT 100,
    location VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations table
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_location_id INTEGER,
    building VARCHAR(50),
    floor_level VARCHAR(20),
    room_number VARCHAR(20),
    coordinates VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_location_id) REFERENCES locations(id)
);

-- Suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_person VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    website VARCHAR(255),
    notes TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PM Templates table
CREATE TABLE IF NOT EXISTS pm_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    asset_type VARCHAR(50),
    frequency_days INTEGER,
    estimated_hours DECIMAL(5,2),
    instructions TEXT,
    safety_requirements TEXT,
    required_parts TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Maintenance Schedules table
CREATE TABLE IF NOT EXISTS maintenance_schedules (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    pm_template_id INTEGER,
    next_due_date DATE,
    frequency_days INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (pm_template_id) REFERENCES pm_templates(id)
);

-- Sensor Readings table
CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    sensor_type VARCHAR(50),
    reading_value DECIMAL(10,4),
    unit VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'normal',
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- AI Predictions table
CREATE TABLE IF NOT EXISTS ai_predictions (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    prediction_type VARCHAR(50),
    predicted_failure_date DATE,
    confidence_score DECIMAL(5,4),
    recommended_action TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id)
);

-- Purchase Orders table
CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    po_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_id INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    order_date DATE DEFAULT CURRENT_DATE,
    expected_delivery DATE,
    total_amount DECIMAL(12,2),
    notes TEXT,
    created_by INTEGER,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- PO Line Items table
CREATE TABLE IF NOT EXISTS po_line_items (
    id SERIAL PRIMARY KEY,
    po_id INTEGER NOT NULL,
    part_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    FOREIGN KEY (po_id) REFERENCES purchase_orders(id),
    FOREIGN KEY (part_id) REFERENCES parts(id)
);

-- Inventory Transactions table
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id SERIAL PRIMARY KEY,
    part_id INTEGER NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    reference_type VARCHAR(50),
    reference_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    FOREIGN KEY (part_id) REFERENCES parts(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Attachments table
CREATE TABLE IF NOT EXISTS attachments (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_size INTEGER,
    mime_type VARCHAR(100),
    reference_type VARCHAR(50),
    reference_id INTEGER,
    uploaded_by INTEGER,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

-- Audit Log table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_values TEXT,
    new_values TEXT,
    changed_by INTEGER,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (changed_by) REFERENCES users(id)
);

-- Media Files table
CREATE TABLE IF NOT EXISTS media_files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_type VARCHAR(50),
    file_size INTEGER,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    work_order_id INTEGER,
    asset_id INTEGER,
    uploaded_by INTEGER,
    FOREIGN KEY (work_order_id) REFERENCES work_orders(id),
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

-- OCR Results table
CREATE TABLE IF NOT EXISTS ocr_results (
    id SERIAL PRIMARY KEY,
    media_file_id INTEGER NOT NULL,
    extracted_text TEXT,
    confidence_score DECIMAL(5,4),
    processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_file_id) REFERENCES media_files(id)
);

-- Speech Transcriptions table
CREATE TABLE IF NOT EXISTS speech_transcriptions (
    id SERIAL PRIMARY KEY,
    media_file_id INTEGER NOT NULL,
    transcribed_text TEXT,
    confidence_score DECIMAL(5,4),
    processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (media_file_id) REFERENCES media_files(id)
);

-- AI Model Configs table
CREATE TABLE IF NOT EXISTS ai_model_configs (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50),
    configuration TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Request Logs table
CREATE TABLE IF NOT EXISTS ai_request_logs (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100),
    request_text TEXT,
    response_text TEXT,
    processing_time DECIMAL(8,4),
    cost DECIMAL(10,6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Model Fine Tuning table
CREATE TABLE IF NOT EXISTS model_fine_tuning (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    training_data TEXT,
    hyperparameters TEXT,
    performance_metrics TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model A/B Tests table
CREATE TABLE IF NOT EXISTS model_ab_tests (
    id SERIAL PRIMARY KEY,
    test_name VARCHAR(100) NOT NULL,
    model_a VARCHAR(100),
    model_b VARCHAR(100),
    metrics TEXT,
    winner VARCHAR(100),
    confidence_level DECIMAL(5,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Prompt Templates table
CREATE TABLE IF NOT EXISTS ai_prompt_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    template_text TEXT NOT NULL,
    category VARCHAR(50),
    variables TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Alerts table
CREATE TABLE IF NOT EXISTS ai_alerts (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    asset_id INTEGER,
    work_order_id INTEGER,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id),
    FOREIGN KEY (work_order_id) REFERENCES work_orders(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status);
CREATE INDEX IF NOT EXISTS idx_work_orders_priority ON work_orders(priority);
CREATE INDEX IF NOT EXISTS idx_work_orders_asset ON work_orders(asset_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_assigned ON work_orders(assigned_to);
CREATE INDEX IF NOT EXISTS idx_work_orders_scheduled ON work_orders(scheduled_start);
CREATE INDEX IF NOT EXISTS idx_assets_location ON assets(location_id);
CREATE INDEX IF NOT EXISTS idx_parts_supplier ON parts(supplier_id);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_asset ON sensor_readings(asset_id);
CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON sensor_readings(timestamp);

-- Insert default admin user (using provided credentials)
INSERT INTO users (username, email, password_hash, full_name, role, department, is_active) 
VALUES (
    'yoyofred', 
    'yoyofred@chatterfix.com', 
    '$2b$12$LQv3c1yqBwEHRqc4n8M3k.H5YQ5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y', -- This should be properly hashed
    'Fred Admin', 
    'admin', 
    'IT', 
    true
) ON CONFLICT (username) DO NOTHING;

-- Note: Password hash above is placeholder - will be properly hashed during migration
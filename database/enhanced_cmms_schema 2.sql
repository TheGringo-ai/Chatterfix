-- Enhanced CMMS Database Schema
-- ChatterFix Phase 7 - Forms, Uploads, Exports, Voice AI

-- Core Work Orders table (enhanced)
CREATE TABLE IF NOT EXISTS work_orders (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL, -- WO-2025-001
    title VARCHAR(255) NOT NULL,
    description TEXT,
    priority VARCHAR(20) DEFAULT 'Medium' CHECK (priority IN ('Low', 'Medium', 'High', 'Critical')),
    status VARCHAR(20) DEFAULT 'Open' CHECK (status IN ('Open', 'In Progress', 'On Hold', 'Completed', 'Cancelled')),
    requested_by VARCHAR(100),
    assigned_to VARCHAR(100),
    asset_id INTEGER REFERENCES assets(id),
    due_date TIMESTAMP,
    estimated_hours DECIMAL(6,2),
    actual_hours DECIMAL(6,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Work Order Activity Log
CREATE TABLE IF NOT EXISTS wo_activity (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id) ON DELETE CASCADE,
    actor VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL, -- 'created', 'status_changed', 'assigned', 'commented', 'completed'
    note TEXT,
    old_value VARCHAR(255),
    new_value VARCHAR(255),
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Work Order Parts Usage
CREATE TABLE IF NOT EXISTS wo_parts_used (
    id SERIAL PRIMARY KEY,
    work_order_id INTEGER REFERENCES work_orders(id) ON DELETE CASCADE,
    part_id INTEGER REFERENCES parts(id),
    qty INTEGER NOT NULL,
    unit_cost DECIMAL(10,2),
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checkout_by VARCHAR(100)
);

-- Enhanced Assets table
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    asset_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    asset_type VARCHAR(100),
    location VARCHAR(255),
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    serial_number VARCHAR(100),
    purchase_date DATE,
    warranty_expiry DATE,
    status VARCHAR(20) DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive', 'Maintenance', 'Retired')),
    criticality VARCHAR(20) DEFAULT 'Medium' CHECK (criticality IN ('Low', 'Medium', 'High', 'Critical')),
    installation_date DATE,
    last_maintenance DATE,
    next_maintenance DATE,
    replacement_cost DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced Parts table
CREATE TABLE IF NOT EXISTS parts (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(100) UNIQUE NOT NULL,
    part_number VARCHAR(100),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    uom VARCHAR(20) DEFAULT 'Each', -- Unit of Measure
    stock_qty INTEGER DEFAULT 0,
    min_qty INTEGER DEFAULT 0,
    max_qty INTEGER,
    location VARCHAR(100),
    bin_location VARCHAR(50),
    unit_cost DECIMAL(10,2),
    last_cost DECIMAL(10,2),
    supplier_id INTEGER,
    supplier_part_number VARCHAR(100),
    photo_uri TEXT,
    barcode VARCHAR(100),
    weight DECIMAL(8,3),
    dimensions VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers table
CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    website VARCHAR(255),
    payment_terms VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Universal Attachments table
CREATE TABLE IF NOT EXISTS attachments (
    id SERIAL PRIMARY KEY,
    module VARCHAR(20) NOT NULL CHECK (module IN ('work_order', 'asset', 'part', 'supplier')),
    ref_id INTEGER NOT NULL, -- Foreign key to the respective table
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    mime_type VARCHAR(100),
    file_size INTEGER,
    gcs_uri TEXT, -- gs://bucket/path/to/file
    download_url TEXT, -- Signed URL (temporary)
    uploaded_by VARCHAR(100),
    tags TEXT[], -- Array of tags for categorization
    is_primary BOOLEAN DEFAULT FALSE, -- For primary photo/document
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Maintenance Schedules
CREATE TABLE IF NOT EXISTS maintenance_schedules (
    id SERIAL PRIMARY KEY,
    asset_id INTEGER REFERENCES assets(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    frequency_type VARCHAR(20) CHECK (frequency_type IN ('Daily', 'Weekly', 'Monthly', 'Quarterly', 'Annually', 'Hours', 'Mileage')),
    frequency_value INTEGER, -- e.g., every 3 months, every 500 hours
    last_completed DATE,
    next_due DATE,
    estimated_hours DECIMAL(6,2),
    assigned_to VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'Medium',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inventory Transactions (for parts tracking)
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id SERIAL PRIMARY KEY,
    part_id INTEGER REFERENCES parts(id),
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('IN', 'OUT', 'ADJUST', 'TRANSFER')),
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(10,2),
    reference_type VARCHAR(20), -- 'work_order', 'purchase', 'adjustment', 'transfer'
    reference_id INTEGER,
    work_order_id INTEGER REFERENCES work_orders(id),
    notes TEXT,
    performed_by VARCHAR(100),
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User/Technician profiles
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'Technician' CHECK (role IN ('Admin', 'Manager', 'Supervisor', 'Technician', 'Viewer')),
    department VARCHAR(100),
    phone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    settings JSONB -- User preferences, notification settings, etc.
);

-- Voice AI Intent Log
CREATE TABLE IF NOT EXISTS voice_intents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    session_id VARCHAR(100),
    audio_file_uri TEXT,
    transcription TEXT,
    intent VARCHAR(100),
    confidence DECIMAL(3,2),
    parameters JSONB,
    action_taken JSONB,
    success BOOLEAN,
    error_message TEXT,
    processing_time_ms INTEGER,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key for parts.supplier_id
ALTER TABLE parts ADD CONSTRAINT fk_parts_supplier 
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders(status);
CREATE INDEX IF NOT EXISTS idx_work_orders_assigned_to ON work_orders(assigned_to);
CREATE INDEX IF NOT EXISTS idx_work_orders_asset_id ON work_orders(asset_id);
CREATE INDEX IF NOT EXISTS idx_work_orders_due_date ON work_orders(due_date);
CREATE INDEX IF NOT EXISTS idx_wo_activity_work_order_id ON wo_activity(work_order_id);
CREATE INDEX IF NOT EXISTS idx_wo_parts_used_work_order_id ON wo_parts_used(work_order_id);
CREATE INDEX IF NOT EXISTS idx_attachments_module_ref ON attachments(module, ref_id);
CREATE INDEX IF NOT EXISTS idx_parts_sku ON parts(sku);
CREATE INDEX IF NOT EXISTS idx_parts_stock_qty ON parts(stock_qty);
CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_part_id ON inventory_transactions(part_id);
CREATE INDEX IF NOT EXISTS idx_voice_intents_user_id ON voice_intents(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_intents_ts ON voice_intents(ts);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_work_orders_updated_at BEFORE UPDATE ON work_orders 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON assets 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();
CREATE TRIGGER update_parts_updated_at BEFORE UPDATE ON parts 
    FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

-- Trigger to auto-generate work order codes
CREATE OR REPLACE FUNCTION generate_work_order_code()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.code IS NULL OR NEW.code = '' THEN
        NEW.code := 'WO-' || TO_CHAR(CURRENT_DATE, 'YYYY') || '-' || 
                   LPAD(NEXTVAL('work_orders_id_seq')::text, 4, '0');
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER generate_work_order_code_trigger 
    BEFORE INSERT ON work_orders
    FOR EACH ROW EXECUTE PROCEDURE generate_work_order_code();

-- Sample data for development/testing
INSERT INTO suppliers (name, contact_person, email, phone) VALUES 
('Industrial Supply Co', 'John Smith', 'john@industrialsupply.com', '555-0101'),
('MRO Parts Direct', 'Sarah Johnson', 'sarah@mroparts.com', '555-0102'),
('Equipment Solutions', 'Mike Wilson', 'mike@equipmentsolutions.com', '555-0103')
ON CONFLICT DO NOTHING;

INSERT INTO users (username, email, full_name, role, department) VALUES 
('admin', 'admin@chatterfix.com', 'System Administrator', 'Admin', 'IT'),
('jsmith', 'john.smith@chatterfix.com', 'John Smith', 'Technician', 'Maintenance'),
('sjohnson', 'sarah.johnson@chatterfix.com', 'Sarah Johnson', 'Supervisor', 'Maintenance'),
('mwilson', 'mike.wilson@chatterfix.com', 'Mike Wilson', 'Manager', 'Operations')
ON CONFLICT DO NOTHING;
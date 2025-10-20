
-- ChatterFix Enterprise Database Schema
-- Multi-tenant CMMS with advanced analytics

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "timescaledb";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Set up row-level security
ALTER DATABASE chatterfix_enterprise SET row_security = on;

-- Tenants table - Foundation of multi-tenancy
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'basic',
    settings JSONB DEFAULT '{}',
    billing_email VARCHAR(255),
    max_users INTEGER DEFAULT 10,
    max_assets INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT true
);

-- Users with comprehensive RBAC
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    roles TEXT[] DEFAULT '{"user"}',
    permissions JSONB DEFAULT '{}',
    department VARCHAR(255),
    phone VARCHAR(50),
    active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, username),
    UNIQUE(tenant_id, email)
);

-- Assets with hierarchical structure and geospatial data
CREATE TABLE assets (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    parent_asset_id INTEGER REFERENCES assets(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    asset_type VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(255),
    model VARCHAR(255),
    serial_number VARCHAR(255),
    purchase_date DATE,
    warranty_expiry DATE,
    location_name VARCHAR(255),
    location_coordinates GEOMETRY(POINT, 4326),
    status VARCHAR(50) DEFAULT 'active',
    criticality VARCHAR(50) DEFAULT 'medium',
    specifications JSONB DEFAULT '{}',
    maintenance_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Work Orders with advanced tracking
CREATE TABLE work_orders (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    work_order_type VARCHAR(50) DEFAULT 'corrective',
    status VARCHAR(50) DEFAULT 'open',
    priority VARCHAR(50) DEFAULT 'medium',
    asset_id INTEGER REFERENCES assets(id),
    assigned_to UUID REFERENCES users(id),
    created_by UUID REFERENCES users(id),
    estimated_hours NUMERIC(6,2),
    actual_hours NUMERIC(6,2),
    estimated_cost NUMERIC(10,2),
    actual_cost NUMERIC(10,2),
    due_date TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    closed_at TIMESTAMP,
    closed_by UUID REFERENCES users(id),
    completion_notes TEXT,
    customer_rating INTEGER CHECK (customer_rating >= 1 AND customer_rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (created_at);

-- Create monthly partitions for work_orders (sample for current year)
CREATE TABLE work_orders_2025_01 PARTITION OF work_orders
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE work_orders_2025_02 PARTITION OF work_orders
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
-- Continue for all months...

-- Parts inventory with advanced tracking
CREATE TABLE parts (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    part_number VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    unit_of_measure VARCHAR(50),
    unit_cost NUMERIC(10,2),
    quantity_on_hand INTEGER DEFAULT 0,
    minimum_stock_level INTEGER DEFAULT 0,
    maximum_stock_level INTEGER,
    reorder_point INTEGER,
    supplier_id INTEGER,
    supplier_part_number VARCHAR(255),
    location VARCHAR(255),
    barcode VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, part_number)
);

-- IoT Sensor Data with TimescaleDB
CREATE TABLE sensor_data (
    timestamp TIMESTAMPTZ NOT NULL,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    sensor_id VARCHAR(255) NOT NULL,
    asset_id INTEGER REFERENCES assets(id),
    metric_type VARCHAR(100) NOT NULL,
    value NUMERIC(15,4),
    unit VARCHAR(50),
    quality_score NUMERIC(3,2), -- Data quality indicator 0-1
    metadata JSONB
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('sensor_data', 'timestamp', partitioning_column => 'tenant_id');

-- Maintenance Schedules for preventive maintenance
CREATE TABLE maintenance_schedules (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    asset_id INTEGER REFERENCES assets(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    schedule_type VARCHAR(50) NOT NULL, -- 'calendar', 'usage', 'condition'
    frequency_value INTEGER NOT NULL,
    frequency_unit VARCHAR(50) NOT NULL, -- 'days', 'weeks', 'months', 'hours', 'cycles'
    last_maintenance TIMESTAMP,
    next_due TIMESTAMP,
    estimated_duration NUMERIC(5,2),
    instructions TEXT,
    required_parts JSONB,
    required_skills TEXT[],
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Row Level Security Policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE work_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE parts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sensor_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE maintenance_schedules ENABLE ROW LEVEL SECURITY;

-- RLS Policies for tenant isolation
CREATE POLICY tenant_isolation_users ON users
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_assets ON assets
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_work_orders ON work_orders
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_parts ON parts
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_sensor_data ON sensor_data
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY tenant_isolation_maintenance_schedules ON maintenance_schedules
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

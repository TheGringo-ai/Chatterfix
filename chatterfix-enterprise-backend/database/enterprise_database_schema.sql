
-- Enterprise ChatterFix CMMS Database Schema with Security

-- Enable Row Level Security
ALTER DATABASE chatterfix_cmms SET row_security = on;

-- Tenants table for multi-tenancy
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users with RBAC
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    roles TEXT[] DEFAULT '{"user"}',
    active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, username),
    UNIQUE(tenant_id, email)
);

-- Work Orders with tenant isolation
CREATE TABLE work_orders (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'open',
    priority VARCHAR(50) DEFAULT 'medium',
    assigned_to UUID REFERENCES users(id),
    created_by UUID REFERENCES users(id),
    asset_id INTEGER,
    estimated_hours NUMERIC(5,2),
    actual_hours NUMERIC(5,2),
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Row Level Security Policies
ALTER TABLE work_orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_work_orders ON work_orders
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Audit logging table
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id),
    user_id UUID REFERENCES users(id),
    table_name VARCHAR(255) NOT NULL,
    record_id VARCHAR(255),
    action VARCHAR(50) NOT NULL, -- INSERT, UPDATE, DELETE, SELECT
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT
);

-- Indexes for performance
CREATE INDEX idx_work_orders_tenant_status ON work_orders(tenant_id, status);
CREATE INDEX idx_work_orders_assigned_to ON work_orders(assigned_to);
CREATE INDEX idx_audit_log_tenant_timestamp ON audit_log(tenant_id, timestamp);

-- Trigger for automatic audit logging
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (tenant_id, table_name, record_id, action, new_values)
        VALUES (NEW.tenant_id, TG_TABLE_NAME, NEW.id::TEXT, TG_OP, to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (tenant_id, table_name, record_id, action, old_values, new_values)
        VALUES (NEW.tenant_id, TG_TABLE_NAME, NEW.id::TEXT, TG_OP, to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (tenant_id, table_name, record_id, action, old_values)
        VALUES (OLD.tenant_id, TG_TABLE_NAME, OLD.id::TEXT, TG_OP, to_jsonb(OLD));
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to work_orders
CREATE TRIGGER work_orders_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON work_orders
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

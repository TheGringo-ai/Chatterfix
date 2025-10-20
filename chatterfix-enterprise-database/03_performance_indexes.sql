
-- Enterprise Performance Optimization Indexes

-- Tenants table indexes
CREATE INDEX idx_tenants_domain ON tenants(domain);
CREATE INDEX idx_tenants_active ON tenants(active) WHERE active = true;

-- Users table indexes
CREATE INDEX idx_users_tenant_username ON users(tenant_id, username);
CREATE INDEX idx_users_tenant_email ON users(tenant_id, email);
CREATE INDEX idx_users_active ON users(tenant_id, active) WHERE active = true;
CREATE INDEX idx_users_roles ON users USING GIN(roles);

-- Assets table indexes
CREATE INDEX idx_assets_tenant_type ON assets(tenant_id, asset_type);
CREATE INDEX idx_assets_parent ON assets(parent_asset_id) WHERE parent_asset_id IS NOT NULL;
CREATE INDEX idx_assets_status ON assets(tenant_id, status);
CREATE INDEX idx_assets_location_gis ON assets USING GIST(location_coordinates);

-- Work Orders table indexes (consider partitioning)
CREATE INDEX idx_work_orders_tenant_status ON work_orders(tenant_id, status);
CREATE INDEX idx_work_orders_assigned_to ON work_orders(assigned_to);
CREATE INDEX idx_work_orders_asset_id ON work_orders(asset_id);
CREATE INDEX idx_work_orders_created_by ON work_orders(created_by);
CREATE INDEX idx_work_orders_due_date ON work_orders(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_work_orders_priority ON work_orders(tenant_id, priority, status);
CREATE INDEX idx_work_orders_type ON work_orders(tenant_id, work_order_type);

-- Parts table indexes
CREATE INDEX idx_parts_tenant_category ON parts(tenant_id, category);
CREATE INDEX idx_parts_part_number ON parts(tenant_id, part_number);
CREATE INDEX idx_parts_low_stock ON parts(tenant_id) WHERE quantity_on_hand <= minimum_stock_level;
CREATE INDEX idx_parts_barcode ON parts(barcode) WHERE barcode IS NOT NULL;

-- Sensor Data indexes (TimescaleDB automatically creates time-based indexes)
CREATE INDEX idx_sensor_data_asset_metric ON sensor_data(asset_id, metric_type, timestamp DESC);
CREATE INDEX idx_sensor_data_tenant ON sensor_data(tenant_id, timestamp DESC);

-- Maintenance Schedules indexes
CREATE INDEX idx_maintenance_schedules_asset ON maintenance_schedules(asset_id);
CREATE INDEX idx_maintenance_schedules_next_due ON maintenance_schedules(tenant_id, next_due) WHERE active = true;
CREATE INDEX idx_maintenance_schedules_overdue ON maintenance_schedules(tenant_id) 
    WHERE next_due < CURRENT_TIMESTAMP AND active = true;

-- Composite indexes for common query patterns
CREATE INDEX idx_work_orders_dashboard ON work_orders(tenant_id, status, priority, created_at DESC);
CREATE INDEX idx_assets_maintenance ON assets(tenant_id, asset_type, status) 
    WHERE status = 'active';

-- Partial indexes for frequently filtered data
CREATE INDEX idx_work_orders_open ON work_orders(tenant_id, created_at DESC) 
    WHERE status IN ('open', 'in_progress');
CREATE INDEX idx_work_orders_high_priority ON work_orders(tenant_id, due_date) 
    WHERE priority = 'high' AND status NOT IN ('completed', 'closed');

-- JSONB indexes for configuration data
CREATE INDEX idx_tenant_settings ON tenants USING GIN(settings);
CREATE INDEX idx_user_permissions ON users USING GIN(permissions);
CREATE INDEX idx_asset_specifications ON assets USING GIN(specifications);


-- Enterprise Analytics Views and Materialized Views

-- Real-time KPI Dashboard View
CREATE OR REPLACE VIEW dashboard_kpis AS
SELECT 
    tenant_id,
    COUNT(*) FILTER (WHERE status = 'open') as open_work_orders,
    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_work_orders,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_work_orders,
    COUNT(*) FILTER (WHERE due_date < CURRENT_TIMESTAMP AND status NOT IN ('completed', 'closed')) as overdue_work_orders,
    AVG(actual_hours) FILTER (WHERE status = 'completed') as avg_completion_time,
    AVG(customer_rating) FILTER (WHERE customer_rating IS NOT NULL) as avg_customer_rating,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) as todays_work_orders
FROM work_orders
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY tenant_id;

-- Asset Performance Analytics
CREATE MATERIALIZED VIEW asset_performance_summary AS
SELECT 
    a.tenant_id,
    a.id as asset_id,
    a.name as asset_name,
    a.asset_type,
    COUNT(wo.id) as total_work_orders,
    COUNT(wo.id) FILTER (WHERE wo.work_order_type = 'corrective') as corrective_orders,
    COUNT(wo.id) FILTER (WHERE wo.work_order_type = 'preventive') as preventive_orders,
    SUM(wo.actual_cost) as total_maintenance_cost,
    AVG(wo.actual_hours) as avg_repair_time,
    -- MTBF calculation (simplified)
    CASE 
        WHEN COUNT(wo.id) FILTER (WHERE wo.work_order_type = 'corrective') > 1
        THEN EXTRACT(EPOCH FROM (MAX(wo.completed_at) - MIN(wo.completed_at))) / 
             (COUNT(wo.id) FILTER (WHERE wo.work_order_type = 'corrective') - 1) / 3600
        ELSE NULL
    END as mtbf_hours,
    MAX(wo.completed_at) as last_maintenance_date
FROM assets a
LEFT JOIN work_orders wo ON a.id = wo.asset_id AND wo.status = 'completed'
GROUP BY a.tenant_id, a.id, a.name, a.asset_type;

-- Create index for performance
CREATE INDEX idx_asset_performance_tenant ON asset_performance_summary(tenant_id);

-- Parts Usage Analytics
CREATE OR REPLACE VIEW parts_usage_analytics AS
SELECT 
    p.tenant_id,
    p.id as part_id,
    p.part_number,
    p.name as part_name,
    p.quantity_on_hand,
    p.minimum_stock_level,
    CASE 
        WHEN p.quantity_on_hand <= p.minimum_stock_level THEN 'LOW_STOCK'
        WHEN p.quantity_on_hand <= p.reorder_point THEN 'REORDER_NEEDED'
        ELSE 'ADEQUATE'
    END as stock_status,
    -- Could join with work_order_parts table for usage statistics
    p.unit_cost * p.quantity_on_hand as inventory_value
FROM parts p;

-- Maintenance Schedule Compliance
CREATE OR REPLACE VIEW maintenance_compliance AS
SELECT 
    ms.tenant_id,
    ms.asset_id,
    a.name as asset_name,
    ms.name as schedule_name,
    ms.next_due,
    CASE 
        WHEN ms.next_due < CURRENT_TIMESTAMP THEN 'OVERDUE'
        WHEN ms.next_due < CURRENT_TIMESTAMP + INTERVAL '7 days' THEN 'DUE_SOON'
        ELSE 'ON_TRACK'
    END as compliance_status,
    ms.last_maintenance,
    CURRENT_TIMESTAMP - ms.last_maintenance as time_since_last_maintenance
FROM maintenance_schedules ms
JOIN assets a ON ms.asset_id = a.id
WHERE ms.active = true;

-- Sensor Data Analytics (TimescaleDB)
CREATE OR REPLACE VIEW sensor_analytics_hourly AS
SELECT 
    time_bucket('1 hour', timestamp) as hour,
    tenant_id,
    asset_id,
    metric_type,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    COUNT(*) as reading_count
FROM sensor_data
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY hour, tenant_id, asset_id, metric_type
ORDER BY hour DESC;

-- Refresh materialized views function
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW asset_performance_summary;
    -- Add other materialized views here
END;
$$ LANGUAGE plpgsql;

-- Schedule regular refresh (would be set up in cron or scheduler)
-- SELECT cron.schedule('refresh-analytics', '0 2 * * *', 'SELECT refresh_analytics_views();');

#!/usr/bin/env python3
"""
PostgreSQL Database Initialization for ChatterFix CMMS
Converts SQLite operations to PostgreSQL-compatible format
"""

import psycopg2
import psycopg2.extras
import os
import logging
from datetime import datetime, date

logger = logging.getLogger(__name__)

def init_postgresql_database():
    """Initialize PostgreSQL database with ChatterFix schema and sample data"""
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL environment variable not set")
            return False
            
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Execute schema from file
        with open('postgresql_schema.sql', 'r') as f:
            schema_sql = f.read()
            cursor.execute(schema_sql)
        
        # Add sample data
        insert_sample_data(cursor)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ PostgreSQL database initialized successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL initialization failed: {e}")
        return False

def insert_sample_data(cursor):
    """Insert sample CMMS data compatible with PostgreSQL"""
    
    # Insert sample users
    users_data = [
        ('yoyofred', 'yoyofred@chatterfix.com', '$2b$12$LQv3c1yqBwEHRqc4n8M3k.H5YQ5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y5Y', 'Fred Admin', 'admin', 'IT'),
        ('johndoe', 'john@techflow.com', '$2b$12$hashedpassword', 'John Doe', 'technician', 'Maintenance'),
        ('maryjane', 'mary@techflow.com', '$2b$12$hashedpassword', 'Mary Jane', 'supervisor', 'Operations'),
        ('mikecool', 'mike@techflow.com', '$2b$12$hashedpassword', 'Mike Cool', 'manager', 'Engineering')
    ]
    
    for user in users_data:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, full_name, role, department, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (username) DO NOTHING
        """, (*user, True))
    
    # Insert sample locations
    locations_data = [
        ('Main Plant', 'Primary manufacturing facility', None, 'Building A', '1', None, '40.7128,-74.0060'),
        ('Warehouse', 'Parts and materials storage', None, 'Building B', '1', None, '40.7130,-74.0055'),
        ('Boiler Room', 'Steam generation area', 1, 'Building A', 'B1', 'B101', '40.7128,-74.0060'),
        ('Production Line 1', 'Main assembly line', 1, 'Building A', '1', '101', '40.7128,-74.0061'),
        ('Quality Control', 'Testing and inspection', 1, 'Building A', '2', '201', '40.7128,-74.0059')
    ]
    
    for loc in locations_data:
        cursor.execute("""
            INSERT INTO locations (name, description, parent_location_id, building, floor_level, room_number, coordinates)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, loc)
    
    # Insert sample suppliers
    suppliers_data = [
        ('ABC Industrial Supply', 'John Smith', 'john@abcindustrial.com', '+1-555-0101', '123 Industrial Blvd, City, ST 12345', 'www.abcindustrial.com', 'Primary parts supplier'),
        ('TechParts Direct', 'Sarah Johnson', 'sarah@techparts.com', '+1-555-0102', '456 Tech Ave, City, ST 12346', 'www.techparts.com', 'Electronic components'),
        ('Motor Works Inc', 'Bob Wilson', 'bob@motorworks.com', '+1-555-0103', '789 Motor St, City, ST 12347', 'www.motorworks.com', 'Motor and drive specialist')
    ]
    
    for supplier in suppliers_data:
        cursor.execute("""
            INSERT INTO suppliers (name, contact_person, email, phone, address, website, notes, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (*supplier, True))
    
    # Insert sample assets
    assets_data = [
        ('Motor A-001', 'Electric Motor', 'ABC-500', 'ABC500-2023-001', 'ABC Motors', 3, 'active', 85, '2024-01-15', '2024-07-15', '2023-06-01', 15000.00, 'Primary drive motor for production line'),
        ('Pump B-002', 'Centrifugal Pump', 'CP-300', 'CP300-2023-002', 'FlowTech', 3, 'active', 92, '2024-02-01', '2024-08-01', '2023-05-15', 8500.00, 'Coolant circulation pump'),
        ('Conveyor C-003', 'Belt Conveyor', 'BC-1000', 'BC1000-2023-003', 'ConveyPro', 4, 'active', 78, '2024-01-30', '2024-07-30', '2023-04-20', 25000.00, 'Main assembly line conveyor'),
        ('HVAC D-004', 'Air Handler', 'AH-2500', 'AH2500-2023-004', 'ClimateControl', 1, 'active', 88, '2024-03-01', '2024-09-01', '2023-03-10', 18000.00, 'Main facility air handling unit'),
        ('Generator E-005', 'Backup Generator', 'BG-750', 'BG750-2023-005', 'PowerGen', 1, 'standby', 95, '2024-01-01', '2024-07-01', '2023-02-01', 45000.00, 'Emergency backup power generator')
    ]
    
    for asset in assets_data:
        cursor.execute("""
            INSERT INTO assets (name, type, model, serial_number, manufacturer, location_id, status, health_score, 
                              last_maintenance, next_maintenance, purchase_date, purchase_cost, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, asset)
    
    # Insert sample parts
    parts_data = [
        ('BRG-001', 'Motor Bearing 6205', 'Replacement bearing for electric motors', 'Bearings', 1, 45.50, 25, 5, 50, 'Warehouse A1'),
        ('BELT-002', 'V-Belt A42', 'Drive belt for conveyor systems', 'Belts', 1, 32.00, 15, 3, 30, 'Warehouse A2'),
        ('SEAL-003', 'Pump Seal Kit', 'Complete seal kit for centrifugal pumps', 'Seals', 2, 125.00, 8, 2, 20, 'Warehouse B1'),
        ('FILT-004', 'Air Filter 20x25x4', 'HVAC air filter replacement', 'Filters', 3, 28.75, 12, 4, 25, 'Warehouse B2'),
        ('OIL-005', 'Hydraulic Oil ISO 46', 'Premium hydraulic fluid 5-gallon', 'Fluids', 2, 89.00, 6, 1, 10, 'Chemical Storage')
    ]
    
    for part in parts_data:
        cursor.execute("""
            INSERT INTO parts (part_number, name, description, category, supplier_id, unit_cost, 
                             stock_quantity, min_stock_level, max_stock_level, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, part)
    
    # Get user IDs for foreign key references
    cursor.execute("SELECT id FROM users WHERE username = 'johndoe'")
    johndoe_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users WHERE username = 'maryjane'")
    maryjane_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users WHERE username = 'mikecool'")
    mikecool_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM users WHERE username = 'yoyofred'")
    admin_id = cursor.fetchone()[0]
    
    # Insert sample work orders
    work_orders_data = [
        ('WO-001', 'Motor Bearing Replacement', 'Replace worn bearing in Motor A-001', 1, 'High', 'Open', 'Preventive', johndoe_id, admin_id, 4.0, None, '2024-03-15 08:00:00', '2024-03-15 12:00:00', None, None, '2024-03-01 10:30:00', '2024-03-15 17:00:00', None, 'Follow lockout/tagout procedures'),
        ('WO-002', 'Pump Seal Replacement', 'Replace leaking seals in Pump B-002', 2, 'Critical', 'In Progress', 'Corrective', johndoe_id, admin_id, 6.0, 2.5, '2024-03-10 09:00:00', '2024-03-10 15:00:00', '2024-03-10 09:15:00', None, '2024-03-01 14:20:00', '2024-03-10 16:00:00', None, 'System must be drained before work'),
        ('WO-003', 'Conveyor Belt Inspection', 'Quarterly inspection of conveyor belt', 3, 'Medium', 'Completed', 'Inspection', maryjane_id, admin_id, 2.0, 1.8, '2024-03-05 10:00:00', '2024-03-05 12:00:00', '2024-03-05 10:00:00', '2024-03-05 11:48:00', '2024-02-28 09:15:00', '2024-03-05 17:00:00', 'Belt condition good, no replacement needed', 'No safety concerns'),
        ('WO-004', 'HVAC Filter Replacement', 'Replace air filters in HVAC D-004', 4, 'Low', 'Scheduled', 'Preventive', johndoe_id, admin_id, 1.5, None, '2024-03-20 13:00:00', '2024-03-20 14:30:00', None, None, '2024-03-01 11:45:00', '2024-03-20 17:00:00', None, 'Standard PPE required'),
        ('WO-005', 'Generator Monthly Test', 'Monthly load test of backup generator', 5, 'Medium', 'Open', 'Testing', mikecool_id, admin_id, 3.0, None, '2024-03-25 08:00:00', '2024-03-25 11:00:00', None, None, '2024-03-01 16:30:00', '2024-03-25 17:00:00', None, 'Coordinate with facilities for power switching')
    ]
    
    for wo in work_orders_data:
        cursor.execute("""
            INSERT INTO work_orders (work_order_number, title, description, asset_id, priority, status, work_type,
                                   assigned_to, created_by, estimated_hours, actual_hours, scheduled_start, 
                                   scheduled_end, actual_start, actual_end, created_date, due_date, 
                                   completion_notes, safety_notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, wo)
    
    logger.info("✅ Sample data inserted successfully!")

if __name__ == "__main__":
    init_postgresql_database()
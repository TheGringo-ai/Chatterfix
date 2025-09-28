#!/usr/bin/env python3
"""
ChatterFix CMMS - Enhanced Database Schema
Based on multi-AI analysis for complete work order workflow
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)

def initialize_enhanced_database(db_path: str = "cmms.db"):
    """Initialize enhanced database schema with all required tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enhanced Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT,
            password_hash TEXT,
            role TEXT DEFAULT 'technician',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # Enhanced Assets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            asset_type TEXT,
            location TEXT,
            manufacturer TEXT,
            model TEXT,
            serial_number TEXT,
            status TEXT DEFAULT 'Active',
            criticality TEXT DEFAULT 'Medium',
            installation_date DATE,
            warranty_expiry DATE,
            last_maintenance TIMESTAMP,
            next_maintenance TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Enhanced Parts table with inventory tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parts (
            part_id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            quantity_available INTEGER DEFAULT 0,
            unit_cost DECIMAL(10,2),
            reorder_level INTEGER DEFAULT 5,
            max_stock_level INTEGER,
            supplier TEXT,
            location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Enhanced Work Orders table with scheduling and recurrence
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            work_order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            asset_id INTEGER,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Open',
            work_type TEXT DEFAULT 'Corrective',
            assigned_to INTEGER,
            created_by INTEGER,
            estimated_hours DECIMAL(5,2),
            actual_hours DECIMAL(5,2),
            scheduled_start TIMESTAMP,
            scheduled_end TIMESTAMP,
            actual_start TIMESTAMP,
            actual_end TIMESTAMP,
            completion_notes TEXT,
            is_recurring BOOLEAN DEFAULT 0,
            recurrence_pattern TEXT,
            parent_schedule_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets (asset_id),
            FOREIGN KEY (assigned_to) REFERENCES users (user_id),
            FOREIGN KEY (created_by) REFERENCES users (user_id),
            FOREIGN KEY (parent_schedule_id) REFERENCES pm_schedules (pm_schedule_id)
        )
    ''')
    
    # Work Order Parts junction table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_order_parts (
            wo_part_id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_order_id INTEGER NOT NULL,
            part_id INTEGER NOT NULL,
            quantity_requested INTEGER NOT NULL,
            quantity_used INTEGER DEFAULT 0,
            unit_cost DECIMAL(10,2),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (work_order_id) REFERENCES work_orders (work_order_id),
            FOREIGN KEY (part_id) REFERENCES parts (part_id)
        )
    ''')
    
    # Time Tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_tracking (
            time_tracking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_order_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration_minutes INTEGER,
            description TEXT,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (work_order_id) REFERENCES work_orders (work_order_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Preventive Maintenance Schedules
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pm_schedules (
            pm_schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            asset_id INTEGER NOT NULL,
            frequency_type TEXT NOT NULL,
            frequency_value INTEGER NOT NULL,
            estimated_hours DECIMAL(5,2),
            description TEXT,
            next_due_date DATE,
            last_completed DATE,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets (asset_id)
        )
    ''')
    
    # Parts Transactions for inventory tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parts_transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            work_order_id INTEGER,
            user_id INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (part_id) REFERENCES parts (part_id),
            FOREIGN KEY (work_order_id) REFERENCES work_orders (work_order_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Work Order Comments/Updates
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_order_updates (
            update_id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_order_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            update_type TEXT DEFAULT 'comment',
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (work_order_id) REFERENCES work_orders (work_order_id),
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders (status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_orders_priority ON work_orders (priority)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_orders_asset ON work_orders (asset_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_orders_assigned ON work_orders (assigned_to)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_work_orders_scheduled ON work_orders (scheduled_start)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_parts_availability ON parts (quantity_available)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_tracking_active ON time_tracking (is_active)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pm_schedules_due ON pm_schedules (next_due_date)')
    
    # Insert demo data if tables are empty
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        insert_demo_data(cursor)
    
    conn.commit()
    conn.close()
    logger.info("🗄️ Enhanced database schema initialized successfully")

def insert_demo_data(cursor):
    """Insert demo data for testing"""
    # Demo users
    demo_users = [
        ('admin', 'admin@chatterfix.com', 'admin_hash', 'admin'),
        ('john_tech', 'john@chatterfix.com', 'tech_hash', 'technician'),
        ('mary_super', 'mary@chatterfix.com', 'super_hash', 'supervisor'),
        ('mike_maint', 'mike@chatterfix.com', 'maint_hash', 'maintenance_lead')
    ]
    
    for user in demo_users:
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        ''', user)
    
    # Demo assets
    demo_assets = [
        ('HVAC Unit A1', 'HVAC', 'Building A - Floor 1', 'Carrier', '30GTN080', 'Active', 'Critical'),
        ('Generator G1', 'Generator', 'Utility Room', 'Caterpillar', 'C15-500KW', 'Active', 'Critical'),
        ('Conveyor Belt CB1', 'Conveyor', 'Production Floor', 'Flexco', 'CB-1200', 'Active', 'High'),
        ('Pump P1', 'Pump', 'Mechanical Room', 'Grundfos', 'CR64-3', 'Active', 'Medium'),
        ('Compressor C1', 'Compressor', 'Utility Room', 'Atlas Copco', 'GA30', 'Active', 'High')
    ]
    
    for asset in demo_assets:
        cursor.execute('''
            INSERT INTO assets (name, asset_type, location, manufacturer, model, status, criticality)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', asset)
    
    # Demo parts
    demo_parts = [
        ('FLT-001', 'HVAC Filter', 'High-efficiency air filter', 'Filters', 25, 45.99, 5, 50),
        ('BLT-V15', 'V-Belt 15"', '15 inch V-belt for conveyor', 'Belts', 12, 28.50, 3, 20),
        ('OIL-15W40', 'Motor Oil 15W-40', '15W-40 motor oil gallon', 'Lubricants', 8, 32.95, 2, 15),
        ('GKT-001', 'Gasket Kit', 'Universal gasket kit', 'Gaskets', 15, 67.25, 5, 25),
        ('BRG-6205', 'Bearing 6205', 'Deep groove ball bearing', 'Bearings', 20, 18.75, 8, 40)
    ]
    
    for part in demo_parts:
        cursor.execute('''
            INSERT INTO parts (part_number, name, description, category, quantity_available, unit_cost, reorder_level, max_stock_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', part)
    
    # Demo work orders
    demo_work_orders = [
        ('HVAC Filter Replacement', 'Replace filters in HVAC Unit A1', 1, 'Medium', 'Open', 'Preventive', 2, 1, 2.0),
        ('Generator Maintenance', 'Quarterly maintenance check', 2, 'High', 'In Progress', 'Preventive', 4, 1, 4.0),
        ('Conveyor Belt Inspection', 'Weekly belt tension check', 3, 'Low', 'Open', 'Preventive', 2, 1, 1.0),
        ('Pump Seal Replacement', 'Replace damaged pump seal', 4, 'Critical', 'Open', 'Corrective', 3, 1, 3.0)
    ]
    
    for wo in demo_work_orders:
        cursor.execute('''
            INSERT INTO work_orders (title, description, asset_id, priority, status, work_type, assigned_to, created_by, estimated_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', wo)
    
    # Demo PM schedules
    demo_pm_schedules = [
        ('HVAC Filter Change', 1, 'monthly', 1, 2.0, 'Monthly filter replacement'),
        ('Generator Service', 2, 'quarterly', 3, 8.0, 'Quarterly generator maintenance'),
        ('Conveyor Inspection', 3, 'weekly', 7, 0.5, 'Weekly conveyor belt inspection'),
        ('Pump Lubrication', 4, 'monthly', 1, 1.0, 'Monthly pump lubrication')
    ]
    
    for pm in demo_pm_schedules:
        cursor.execute('''
            INSERT INTO pm_schedules (name, asset_id, frequency_type, frequency_value, estimated_hours, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', pm)

if __name__ == "__main__":
    initialize_enhanced_database()
    print("✅ Enhanced database schema initialized successfully!")
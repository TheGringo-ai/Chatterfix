#!/usr/bin/env python3
"""
ChatterFix CMMS - Database Migration Script
Safely adds new columns and tables for enhanced work order functionality
"""

import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def migrate_database(db_path: str = "cmms.db"):
    """Migrate existing database to enhanced schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔄 Starting database migration...")
        
        # Check existing schema and add missing columns to work_orders
        cursor.execute("PRAGMA table_info(work_orders)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        work_order_additions = [
            ("work_type", "TEXT DEFAULT 'Corrective'"),
            ("estimated_hours", "DECIMAL(5,2)"),
            ("actual_hours", "DECIMAL(5,2)"),
            ("scheduled_start", "TIMESTAMP"),
            ("scheduled_end", "TIMESTAMP"),
            ("actual_start", "TIMESTAMP"),
            ("actual_end", "TIMESTAMP"),
            ("completion_notes", "TEXT"),
            ("is_recurring", "BOOLEAN DEFAULT 0"),
            ("recurrence_pattern", "TEXT"),
            ("parent_schedule_id", "INTEGER")
        ]
        
        for column_name, column_def in work_order_additions:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE work_orders ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Added column {column_name} to work_orders")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"⚠️  Could not add column {column_name}: {e}")
        
        # Check and add missing columns to assets
        cursor.execute("PRAGMA table_info(assets)")
        existing_asset_columns = [column[1] for column in cursor.fetchall()]
        
        asset_additions = [
            ("serial_number", "TEXT"),
            ("installation_date", "DATE"),
            ("warranty_expiry", "DATE"),
            ("next_maintenance", "TIMESTAMP")
        ]
        
        for column_name, column_def in asset_additions:
            if column_name not in existing_asset_columns:
                try:
                    cursor.execute(f"ALTER TABLE assets ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Added column {column_name} to assets")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"⚠️  Could not add column {column_name}: {e}")
        
        # Check and add missing columns to parts
        cursor.execute("PRAGMA table_info(parts)")
        existing_parts_columns = [column[1] for column in cursor.fetchall()]
        
        parts_additions = [
            ("part_number", "TEXT"),
            ("category", "TEXT"),
            ("reorder_level", "INTEGER DEFAULT 5"),
            ("max_stock_level", "INTEGER"),
            ("supplier", "TEXT"),
            ("location", "TEXT")
        ]
        
        for column_name, column_def in parts_additions:
            if column_name not in existing_parts_columns:
                try:
                    cursor.execute(f"ALTER TABLE parts ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Added column {column_name} to parts")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e).lower():
                        print(f"⚠️  Could not add column {column_name}: {e}")
        
        # Create new tables if they don't exist
        new_tables = {
            "work_order_parts": '''
                CREATE TABLE IF NOT EXISTS work_order_parts (
                    wo_part_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_order_id INTEGER NOT NULL,
                    part_id INTEGER NOT NULL,
                    quantity_requested INTEGER NOT NULL,
                    quantity_used INTEGER DEFAULT 0,
                    unit_cost DECIMAL(10,2),
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (work_order_id) REFERENCES work_orders (id),
                    FOREIGN KEY (part_id) REFERENCES parts (id)
                )
            ''',
            "time_tracking": '''
                CREATE TABLE IF NOT EXISTS time_tracking (
                    time_tracking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_order_id INTEGER NOT NULL,
                    user_id INTEGER DEFAULT 1,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    duration_minutes INTEGER,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (work_order_id) REFERENCES work_orders (id)
                )
            ''',
            "pm_schedules": '''
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
                    FOREIGN KEY (asset_id) REFERENCES assets (id)
                )
            ''',
            "parts_transactions": '''
                CREATE TABLE IF NOT EXISTS parts_transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    part_id INTEGER NOT NULL,
                    transaction_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    work_order_id INTEGER,
                    user_id INTEGER DEFAULT 1,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (part_id) REFERENCES parts (id),
                    FOREIGN KEY (work_order_id) REFERENCES work_orders (id)
                )
            ''',
            "work_order_updates": '''
                CREATE TABLE IF NOT EXISTS work_order_updates (
                    update_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_order_id INTEGER NOT NULL,
                    user_id INTEGER DEFAULT 1,
                    update_type TEXT DEFAULT 'comment',
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (work_order_id) REFERENCES work_orders (id)
                )
            '''
        }
        
        for table_name, create_sql in new_tables.items():
            cursor.execute(create_sql)
            print(f"✅ Created table {table_name}")
        
        # Create indexes safely
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_work_orders_status ON work_orders (status)",
            "CREATE INDEX IF NOT EXISTS idx_work_orders_priority ON work_orders (priority)",
            "CREATE INDEX IF NOT EXISTS idx_work_orders_asset_id ON work_orders (asset_id)",
            "CREATE INDEX IF NOT EXISTS idx_time_tracking_active ON time_tracking (is_active)",
            "CREATE INDEX IF NOT EXISTS idx_pm_schedules_due ON pm_schedules (next_due_date)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.OperationalError as e:
                if "already exists" not in str(e).lower():
                    print(f"⚠️  Could not create index: {e}")
        
        # Add demo data for new tables if empty
        cursor.execute("SELECT COUNT(*) FROM pm_schedules")
        if cursor.fetchone()[0] == 0:
            add_demo_schedules(cursor)
        
        conn.commit()
        print("✅ Database migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

def add_demo_schedules(cursor):
    """Add demo PM schedules"""
    demo_schedules = [
        ('Monthly HVAC Filter Change', 1, 'monthly', 1, 2.0, 'Replace HVAC filters monthly'),
        ('Quarterly Generator Service', 2, 'quarterly', 3, 8.0, 'Quarterly generator maintenance'),
        ('Weekly Conveyor Inspection', 3, 'weekly', 7, 0.5, 'Weekly conveyor belt inspection'),
        ('Bi-weekly Pump Check', 4, 'weekly', 14, 1.0, 'Bi-weekly pump inspection')
    ]
    
    for schedule in demo_schedules:
        cursor.execute('''
            INSERT INTO pm_schedules (name, asset_id, frequency_type, frequency_value, estimated_hours, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', schedule)
    
    print("✅ Added demo PM schedules")

if __name__ == "__main__":
    migrate_database()
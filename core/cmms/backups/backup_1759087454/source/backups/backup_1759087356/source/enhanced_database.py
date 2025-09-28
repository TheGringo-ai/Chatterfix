#!/usr/bin/env python3
"""
ChatterFix CMMS Enterprise - Enhanced Database Schema
Designed to outclass Maximo, Fiix, and UpKeep with AI-powered features
"""

import sqlite3
import os
from datetime import datetime, timedelta
import json

DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/cmms_enhanced.db")

def init_enhanced_database():
    """Initialize comprehensive enterprise database with AI-powered features"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Enhanced Users table with RBAC
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'technician',
            permissions TEXT DEFAULT '{}',
            is_active BOOLEAN DEFAULT TRUE,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME,
            department TEXT,
            full_name TEXT,
            phone TEXT,
            employee_id TEXT,
            certification_level TEXT,
            hourly_rate DECIMAL(10,2),
            avatar_url TEXT,
            timezone TEXT DEFAULT 'UTC',
            language TEXT DEFAULT 'en',
            notification_preferences TEXT DEFAULT '{}'
        )
    ''')
    
    # Enhanced Assets table with IoT integration
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_tag TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            subcategory TEXT,
            location_id INTEGER,
            parent_asset_id INTEGER,
            manufacturer TEXT,
            model TEXT,
            serial_number TEXT,
            purchase_date DATE,
            installation_date DATE,
            warranty_expiry DATE,
            purchase_cost DECIMAL(12,2),
            current_value DECIMAL(12,2),
            depreciation_rate DECIMAL(5,2),
            status TEXT DEFAULT 'Active',
            condition_rating INTEGER DEFAULT 5,
            criticality TEXT DEFAULT 'Medium',
            last_maintenance_date DATETIME,
            next_maintenance_due DATETIME,
            maintenance_frequency_days INTEGER,
            operating_hours DECIMAL(10,2) DEFAULT 0,
            max_operating_hours DECIMAL(10,2),
            energy_consumption DECIMAL(10,2),
            specifications TEXT,
            documentation_url TEXT,
            qr_code TEXT,
            iot_device_id TEXT,
            sensor_data TEXT DEFAULT '{}',
            ai_health_score DECIMAL(3,2) DEFAULT 1.0,
            failure_predictions TEXT DEFAULT '{}',
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (location_id) REFERENCES locations (id),
            FOREIGN KEY (parent_asset_id) REFERENCES assets (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Enhanced Work Orders with AI automation
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wo_number TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            work_type TEXT NOT NULL,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Open',
            asset_id INTEGER,
            location_id INTEGER,
            assigned_to INTEGER,
            assigned_team TEXT,
            requested_by INTEGER,
            created_by INTEGER,
            estimated_hours DECIMAL(5,2),
            actual_hours DECIMAL(5,2),
            estimated_cost DECIMAL(10,2),
            actual_cost DECIMAL(10,2),
            scheduled_start DATETIME,
            scheduled_end DATETIME,
            actual_start DATETIME,
            actual_end DATETIME,
            due_date DATETIME,
            completion_date DATETIME,
            completion_notes TEXT,
            completion_rating INTEGER,
            safety_notes TEXT,
            permit_required BOOLEAN DEFAULT FALSE,
            permit_number TEXT,
            downtime_hours DECIMAL(5,2),
            parts_used TEXT DEFAULT '[]',
            labor_entries TEXT DEFAULT '[]',
            attachments TEXT DEFAULT '[]',
            ai_generated BOOLEAN DEFAULT FALSE,
            ai_urgency_score DECIMAL(3,2),
            ai_completion_prediction DATETIME,
            parent_wo_id INTEGER,
            recurrence_pattern TEXT,
            failure_code TEXT,
            failure_cause TEXT,
            corrective_action TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets (id),
            FOREIGN KEY (location_id) REFERENCES locations (id),
            FOREIGN KEY (assigned_to) REFERENCES users (id),
            FOREIGN KEY (requested_by) REFERENCES users (id),
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (parent_wo_id) REFERENCES work_orders (id)
        )
    ''')
    
    # Enhanced Parts/Inventory with smart forecasting
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_number TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            subcategory TEXT,
            manufacturer TEXT,
            manufacturer_part_number TEXT,
            supplier_id INTEGER,
            unit_of_measure TEXT DEFAULT 'EA',
            unit_cost DECIMAL(10,2),
            stock_quantity INTEGER DEFAULT 0,
            reserved_quantity INTEGER DEFAULT 0,
            available_quantity INTEGER GENERATED ALWAYS AS (stock_quantity - reserved_quantity) STORED,
            min_stock_level INTEGER DEFAULT 5,
            max_stock_level INTEGER DEFAULT 100,
            reorder_point INTEGER DEFAULT 10,
            reorder_quantity INTEGER DEFAULT 20,
            lead_time_days INTEGER DEFAULT 7,
            storage_location TEXT,
            bin_location TEXT,
            barcode TEXT,
            weight DECIMAL(8,3),
            dimensions TEXT,
            hazmat_classification TEXT,
            shelf_life_days INTEGER,
            warranty_period_days INTEGER,
            last_counted_date DATE,
            abc_classification TEXT,
            usage_rate_monthly DECIMAL(8,2),
            ai_demand_forecast TEXT DEFAULT '{}',
            ai_optimal_stock DECIMAL(8,2),
            price_history TEXT DEFAULT '[]',
            supplier_alternates TEXT DEFAULT '[]',
            compatible_assets TEXT DEFAULT '[]',
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
        )
    ''')
    
    # Locations hierarchy
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            location_type TEXT,
            parent_location_id INTEGER,
            building TEXT,
            floor TEXT,
            room TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            country TEXT,
            gps_coordinates TEXT,
            contact_person TEXT,
            contact_phone TEXT,
            contact_email TEXT,
            operating_hours TEXT,
            timezone TEXT,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_location_id) REFERENCES locations (id)
        )
    ''')
    
    # Suppliers management
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            country TEXT,
            payment_terms TEXT,
            lead_time_days INTEGER DEFAULT 7,
            rating DECIMAL(2,1),
            notes TEXT,
            is_preferred BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Preventive Maintenance Templates
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pm_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            template_name TEXT NOT NULL,
            description TEXT,
            asset_category TEXT,
            frequency_type TEXT,
            frequency_value INTEGER,
            estimated_duration DECIMAL(5,2),
            required_skills TEXT DEFAULT '[]',
            required_parts TEXT DEFAULT '[]',
            required_tools TEXT DEFAULT '[]',
            safety_requirements TEXT,
            instructions TEXT,
            checklist_items TEXT DEFAULT '[]',
            is_active BOOLEAN DEFAULT TRUE,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Maintenance Schedules (AI-generated)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            pm_template_id INTEGER NOT NULL,
            schedule_type TEXT DEFAULT 'Calendar',
            frequency_days INTEGER,
            next_due_date DATETIME,
            last_completed_date DATETIME,
            total_completions INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            ai_optimized BOOLEAN DEFAULT FALSE,
            ai_recommended_frequency INTEGER,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asset_id) REFERENCES assets (id),
            FOREIGN KEY (pm_template_id) REFERENCES pm_templates (id)
        )
    ''')
    
    # IoT Sensor Data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL,
            sensor_type TEXT NOT NULL,
            sensor_value DECIMAL(12,4),
            unit TEXT,
            reading_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            alert_triggered BOOLEAN DEFAULT FALSE,
            alert_level TEXT,
            processed_by_ai BOOLEAN DEFAULT FALSE,
            anomaly_score DECIMAL(3,2),
            FOREIGN KEY (asset_id) REFERENCES assets (id)
        )
    ''')
    
    # AI Predictions and Analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_type TEXT NOT NULL,
            target_id INTEGER NOT NULL,
            target_type TEXT NOT NULL,
            prediction_data TEXT NOT NULL,
            confidence_score DECIMAL(3,2),
            prediction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            expiry_date DATETIME,
            accuracy_score DECIMAL(3,2),
            model_version TEXT,
            provider TEXT
        )
    ''')
    
    # Purchase Orders
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE NOT NULL,
            supplier_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Draft',
            order_date DATE,
            expected_delivery_date DATE,
            actual_delivery_date DATE,
            total_amount DECIMAL(12,2),
            notes TEXT,
            created_by INTEGER,
            approved_by INTEGER,
            approval_date DATETIME,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (approved_by) REFERENCES users (id)
        )
    ''')
    
    # Purchase Order Line Items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS po_line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL,
            part_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price DECIMAL(10,2),
            line_total DECIMAL(12,2),
            received_quantity INTEGER DEFAULT 0,
            FOREIGN KEY (po_id) REFERENCES purchase_orders (id),
            FOREIGN KEY (part_id) REFERENCES parts (id)
        )
    ''')
    
    # Inventory Transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            quantity_change INTEGER NOT NULL,
            reference_id INTEGER,
            reference_type TEXT,
            unit_cost DECIMAL(10,2),
            notes TEXT,
            created_by INTEGER,
            created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (part_id) REFERENCES parts (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # File Attachments
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER,
            mime_type TEXT,
            uploaded_by INTEGER,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            reference_id INTEGER,
            reference_type TEXT,
            description TEXT,
            FOREIGN KEY (uploaded_by) REFERENCES users (id)
        )
    ''')
    
    # Audit Log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            table_name TEXT,
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_assets_location ON assets(location_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_assets_category ON assets(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_workorders_asset ON work_orders(asset_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_workorders_assigned ON work_orders(assigned_to)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_workorders_status ON work_orders(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_workorders_priority ON work_orders(priority)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_parts_category ON parts(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_readings_asset ON sensor_readings(asset_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_readings_timestamp ON sensor_readings(reading_timestamp)')
    
    conn.commit()
    conn.close()
    print("✅ Enhanced database schema created successfully!")

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    init_enhanced_database()
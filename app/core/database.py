import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

# Database Configuration
DATABASE_PATH = os.getenv("CMMS_DB_PATH", "./data/cmms.db")

def init_database():
    """Initialize the SQLite database with required tables"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        
        # Work Orders Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS work_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                title TEXT NOT NULL, 
                description TEXT,
                status TEXT DEFAULT 'Open',
                priority TEXT DEFAULT 'Medium',
                assigned_to TEXT,
                asset_id INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                due_date TIMESTAMP,
                FOREIGN KEY(asset_id) REFERENCES assets(id)
            )
        """)
        
        
        # Comprehensive Assets Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                -- Basic Information
                name TEXT NOT NULL,
                description TEXT,
                asset_tag TEXT UNIQUE,
                serial_number TEXT,
                model TEXT,
                manufacturer TEXT,
                image_url TEXT,
                
                -- Location & Hierarchy
                location TEXT,
                department TEXT,
                parent_asset_id INTEGER,
                
                -- Status & Condition
                status TEXT DEFAULT 'Active', -- Active, Inactive, Maintenance, Retired
                condition_rating INTEGER DEFAULT 5, -- 1-10 scale
                criticality TEXT DEFAULT 'Medium', -- Low, Medium, High, Critical
                
                -- Warranty & Purchase
                purchase_date DATE,
                warranty_expiry DATE,
                purchase_cost REAL,
                
                -- Operational Dates
                installation_date DATE,
                
                -- Maintenance Stats (Cached/Calculated)
                last_maintenance_date DATE,
                next_maintenance_due DATE,
                total_maintenance_cost REAL DEFAULT 0,
                total_downtime_hours REAL DEFAULT 0,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(parent_asset_id) REFERENCES assets(id)
            )
        """)

        # Migration: Check for image_url column in assets table and add if missing
        try:
            cur.execute("PRAGMA table_info(assets)")
            columns = [info[1] for info in cur.fetchall()]
            if 'image_url' not in columns:
                logger.info("Adding image_url column to assets table")
                cur.execute("ALTER TABLE assets ADD COLUMN image_url TEXT")
        except Exception as e:
            logger.error(f"Error checking/adding image_url column: {e}")
        
        # Asset Media Table (photos, videos, documents)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS asset_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT, -- image, video, document, manual
                title TEXT,
                description TEXT,
                uploaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(asset_id) REFERENCES assets(id)
            )
        """)

        # Work Order Media Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS work_order_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT, -- image, video, document
                title TEXT,
                description TEXT,
                uploaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(work_order_id) REFERENCES work_orders(id)
            )
        """)

        # Part Media Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS part_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT, -- image, video, document
                title TEXT,
                description TEXT,
                uploaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(part_id) REFERENCES parts(id)
            )
        """)
        
        # Asset Parts Association (many-to-many)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS asset_parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                part_id INTEGER NOT NULL,
                quantity_used INTEGER DEFAULT 1,
                last_replaced DATE,
                replacement_interval_days INTEGER,
                notes TEXT,
                FOREIGN KEY(asset_id) REFERENCES assets(id),
                FOREIGN KEY(part_id) REFERENCES parts(id)
            )
        """)
        
        # Maintenance History Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS maintenance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                work_order_id INTEGER,
                maintenance_type TEXT, -- Preventive, Corrective, Predictive, Emergency
                description TEXT,
                technician TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                downtime_hours REAL,
                labor_cost REAL,
                parts_cost REAL,
                total_cost REAL,
                notes TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(asset_id) REFERENCES assets(id),
                FOREIGN KEY(work_order_id) REFERENCES work_orders(id)
            )
        """)
        
        # Asset Metrics (for AI analysis)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS asset_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id INTEGER NOT NULL,
                metric_type TEXT, -- temperature, vibration, pressure, runtime, etc.
                value REAL,
                unit TEXT,
                recorded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(asset_id) REFERENCES assets(id)
            )
        """)
        
        # AI Interactions Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ai_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_message TEXT, 
                ai_response TEXT
            )
        """)

        # ========== TEAM COLLABORATION TABLES ==========
        
        # Users Table with Authentication
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'technician', -- requestor, technician, planner, supervisor, parts_manager, manager
                phone TEXT,
                avatar_url TEXT,
                status TEXT DEFAULT 'available', -- available, busy, offline
                is_active BOOLEAN DEFAULT 1,
                last_seen TIMESTAMP,
                last_password_change TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                locked_until TIMESTAMP,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User Skills Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                skill_name TEXT, -- HVAC, Electrical, Plumbing, Welding, etc.
                proficiency_level INTEGER, -- 1-5 scale
                certified BOOLEAN DEFAULT 0,
                certification_date DATE,
                certification_expiry DATE,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # User Performance Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                period TEXT, -- weekly, monthly, quarterly
                work_orders_completed INTEGER DEFAULT 0,
                avg_completion_time REAL,
                quality_score REAL, -- 0-100 based on feedback
                safety_incidents INTEGER DEFAULT 0,
                training_hours REAL DEFAULT 0,
                period_start DATE,
                period_end DATE,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Team Messages Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS team_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                recipient_id INTEGER, -- NULL for broadcast
                work_order_id INTEGER, -- NULL for general messages
                asset_id INTEGER, -- NULL if not asset-related
                message_type TEXT, -- chat, parts_request, status_update, alert
                message TEXT NOT NULL,
                priority TEXT DEFAULT 'normal', -- low, normal, high, urgent
                read BOOLEAN DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(sender_id) REFERENCES users(id),
                FOREIGN KEY(recipient_id) REFERENCES users(id),
                FOREIGN KEY(work_order_id) REFERENCES work_orders(id),
                FOREIGN KEY(asset_id) REFERENCES assets(id)
            )
        """)
        
        # Notifications Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                notification_type TEXT, -- work_order_assigned, parts_arrived, training_due, etc.
                title TEXT NOT NULL,
                message TEXT,
                link TEXT, -- URL to relevant page
                read BOOLEAN DEFAULT 0,
                priority TEXT DEFAULT 'normal',
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Work Order Feedback Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS work_order_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_order_id INTEGER NOT NULL,
                asset_id INTEGER NOT NULL,
                technician_id INTEGER NOT NULL,
                feedback_type TEXT, -- immediate_failure, recurring_issue, quality_concern
                description TEXT,
                time_to_failure_hours REAL, -- Hours between completion and failure
                root_cause TEXT,
                ai_analysis TEXT, -- AI-generated insights
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(work_order_id) REFERENCES work_orders(id),
                FOREIGN KEY(asset_id) REFERENCES assets(id),
                FOREIGN KEY(technician_id) REFERENCES users(id)
            )
        """)
        
        # Training Modules Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS training_modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                content_type TEXT, -- manual, video, ai_generated, interactive
                asset_type TEXT, -- Links to specific equipment types
                skill_category TEXT,
                difficulty_level INTEGER, -- 1-5
                estimated_duration_minutes INTEGER,
                content_path TEXT, -- Path to training materials
                ai_generated BOOLEAN DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User Training Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_training (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                training_module_id INTEGER NOT NULL,
                status TEXT DEFAULT 'assigned', -- assigned, in_progress, completed
                score REAL, -- 0-100 if there's a quiz
                started_date TIMESTAMP,
                completed_date TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(training_module_id) REFERENCES training_modules(id)
            )
        """)
        
        # Parts Requests Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS parts_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requester_id INTEGER NOT NULL,
                work_order_id INTEGER,
                part_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                priority TEXT DEFAULT 'normal',
                status TEXT DEFAULT 'pending', -- pending, approved, ordered, arrived, delivered
                notes TEXT,
                requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                fulfilled_date TIMESTAMP,
                FOREIGN KEY(requester_id) REFERENCES users(id),
                FOREIGN KEY(work_order_id) REFERENCES work_orders(id),
                FOREIGN KEY(part_id) REFERENCES parts(id)
            )
        """)

        # Parts Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS parts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                part_number TEXT UNIQUE,
                category TEXT,
                current_stock INTEGER DEFAULT 0,
                minimum_stock INTEGER DEFAULT 5,
                location TEXT,
                unit_cost REAL,
                vendor_id INTEGER,
                image_url TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Vendors Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS vendors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_name TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                website TEXT
            )
        """)

        # Purchase Orders Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vendor_id INTEGER,
                status TEXT DEFAULT 'Draft', -- Draft, Ordered, Received, Cancelled
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expected_date TIMESTAMP,
                total_cost REAL,
                notes TEXT,
                FOREIGN KEY(vendor_id) REFERENCES vendors(id)
            )
        """)

        # PO Items Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS po_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_id INTEGER,
                part_id INTEGER,
                quantity INTEGER,
                unit_cost REAL,
                FOREIGN KEY(po_id) REFERENCES purchase_orders(id),
                FOREIGN KEY(part_id) REFERENCES parts(id)
            )
        """)

        # Manuals Table (for RAG)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS manuals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT, -- Full text content for searching
                file_path TEXT,
                asset_type TEXT,
                uploaded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ========== AUTHENTICATION & SETTINGS TABLES ==========
        
        # User Sessions Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # User API Settings Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_api_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                setting_key TEXT NOT NULL,
                setting_value TEXT,
                is_encrypted BOOLEAN DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(user_id, setting_key)
            )
        """)
        
        # System Settings Table (for managers)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                setting_type TEXT, -- api_key, endpoint, config
                is_encrypted BOOLEAN DEFAULT 1,
                updated_by INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(updated_by) REFERENCES users(id)
            )
        """)
        
        # ========== ADVANCED DASHBOARD TABLES ==========
        
        # Dashboard Widgets Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS dashboard_widgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                widget_type TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT,
                default_roles TEXT,
                is_system BOOLEAN DEFAULT 0,
                config_schema TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User Dashboard Configuration Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_dashboard_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                widget_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                size TEXT DEFAULT 'medium',
                config TEXT,
                is_visible BOOLEAN DEFAULT 1,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(widget_id) REFERENCES dashboard_widgets(id)
            )
        """)
        
        # Insert default widgets
        cur.execute("""
            INSERT OR IGNORE INTO dashboard_widgets (widget_type, title, description, default_roles, is_system)
            VALUES 
                ('workload', 'My Workload', 'Today''s assigned work orders with timeline', '["technician", "supervisor"]', 1),
                ('parts_status', 'Parts Status', 'Parts arriving, pending requests, low stock alerts', '["technician", "parts_manager"]', 1),
                ('messages', 'Team Messages', 'Unread messages and mentions', '["technician", "supervisor", "parts_manager"]', 1),
                ('performance', 'My Performance', 'Today''s stats and trends', '["technician"]', 1),
                ('equipment', 'My Equipment', 'Assigned assets and health status', '["technician"]', 1),
                ('notifications', 'Notifications', 'Priority alerts and reminders', '["technician", "supervisor", "parts_manager", "manager"]', 1),
                ('team_status', 'Team Status', 'Team availability and shift info', '["supervisor", "manager"]', 1),
                ('training', 'Training', 'Due training and recommendations', '["technician"]', 1),
                ('quick_actions', 'Quick Actions', 'Common tasks and shortcuts', '["technician", "supervisor"]', 1),
                ('ai_insights', 'AI Insights', 'Predictive alerts and recommendations', '["technician", "supervisor", "manager"]', 1),
                ('quality_alerts', 'Quality Alerts', 'Quality concerns and recurring issues', '["supervisor", "manager"]', 1),
                ('inventory_overview', 'Inventory Overview', 'Stock levels and orders', '["parts_manager"]', 1),
                ('approval_queue', 'Approval Queue', 'Pending approvals', '["supervisor", "manager"]', 1),
                ('analytics', 'Analytics', 'Performance metrics and trends', '["manager"]', 1)
        """)
        
        # Update users table with dashboard preferences (if columns don't exist)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN dashboard_layout TEXT DEFAULT 'grid'")
        except:
            pass
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'dark'")
        except:
            pass
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN refresh_interval INTEGER DEFAULT 30")
        except:
            pass
        
        # Update work_orders table with assignment and scheduling
        try:
            cur.execute("ALTER TABLE work_orders ADD COLUMN assigned_to INTEGER")
        except:
            pass
        
        try:
            cur.execute("ALTER TABLE work_orders ADD COLUMN estimated_duration INTEGER")
        except:
            pass
        
        try:
            cur.execute("ALTER TABLE work_orders ADD COLUMN actual_start_time TIMESTAMP")
        except:
            pass
        
        try:
            cur.execute("ALTER TABLE work_orders ADD COLUMN actual_start TIMESTAMP")
        except:
            pass
        
        try:
            cur.execute("ALTER TABLE work_orders ADD COLUMN actual_end TIMESTAMP")
        except:
            pass
        
        try:
            cur.execute("ALTER TABLE work_orders ADD COLUMN blocked_reason TEXT")
        except:
            pass
        
        try:
            cur.execute("ALTER TABLE work_orders ADD COLUMN location TEXT")
        except:
            pass
        
        # ========== GEOLOCATION & PWA TABLES ==========
        
        # Property Boundaries Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS property_boundaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                boundary_type TEXT DEFAULT 'polygon',
                coordinates TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User Location History Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_location_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                accuracy REAL,
                work_order_id INTEGER,
                within_property BOOLEAN DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(work_order_id) REFERENCES work_orders(id)
            )
        """)
        
        # User Privacy Settings Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_privacy_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                location_tracking_enabled BOOLEAN DEFAULT 1,
                share_location_with_team BOOLEAN DEFAULT 1,
                track_only_on_shift BOOLEAN DEFAULT 1,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # PWA Installation Table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pwa_installations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_type TEXT,
                platform TEXT,
                installed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        
        # Update users table with geolocation preferences
        try:
            cur.execute("ALTER TABLE users ADD COLUMN current_latitude REAL")
        except:
            pass
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN current_longitude REAL")
        except:
            pass
        
        try:
            cur.execute("ALTER TABLE users ADD COLUMN last_location_update TIMESTAMP")
        except:
            pass

        # Company Information Table for Landing Page Signups
        cur.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                industry TEXT,
                company_size TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {DATABASE_PATH}")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

def get_db_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

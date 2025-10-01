#!/usr/bin/env python3
"""
ChatterFix CMMS Data Toggle System
Comprehensive system for managing demo/production data modes with:
- Database routing and connection management
- Mode switching with validation and backup
- Data migration and synchronization
- AI Brain integration for smart recommendations
- Company setup wizard integration
"""

import sqlite3
import os
import json
import shutil
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from contextlib import contextmanager
import asyncio
try:
    import aiosqlite
    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False

try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Import admin manager
from admin import admin_manager, get_system_mode, get_database_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_postgresql():
    """Check if we're using PostgreSQL or SQLite"""
    db_url = os.getenv("DATABASE_URL")
    return db_url is not None and POSTGRES_AVAILABLE

def get_all_tables_query():
    """Get database-agnostic query to list all tables"""
    if is_postgresql():
        return """
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """, ()
    else:
        return "SELECT name FROM sqlite_master WHERE type='table'", ()

class DataToggleSystem:
    """Main data toggle system for managing demo/production modes"""
    
    def __init__(self):
        self.admin = admin_manager
        self.demo_db_initialized = False
        self.production_db_initialized = False
        
        # Initialize databases
        self._ensure_databases_exist()
    
    def _ensure_databases_exist(self):
        """Ensure both demo and production databases exist"""
        demo_path = self.admin.get_database_path("demo")
        prod_path = self.admin.get_database_path("production")
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(demo_path), exist_ok=True)
        os.makedirs(os.path.dirname(prod_path), exist_ok=True)
        
        # Initialize demo database with mock data if it doesn't exist
        if not os.path.exists(demo_path):
            self._initialize_demo_database()
        
        # Initialize production database if it doesn't exist
        if not os.path.exists(prod_path):
            self._initialize_production_database()
    
    def _initialize_demo_database(self):
        """Initialize demo database with TechFlow Manufacturing Corp data"""
        try:
            from enhanced_database import init_enhanced_database
            from enterprise_mock_data_generator import TechFlowDataGenerator
            
            demo_path = self.admin.get_database_path("demo")
            
            # Remove existing demo database to avoid conflicts
            if os.path.exists(demo_path):
                os.remove(demo_path)
                logger.info(f"🗑️ Removed existing demo database: {demo_path}")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(demo_path), exist_ok=True)
            
            # Temporarily set database path for demo initialization
            original_db_path = os.environ.get("DATABASE_PATH")
            os.environ["DATABASE_PATH"] = demo_path
            
            # Initialize enhanced database schema
            init_enhanced_database()
            
            # Generate TechFlow Manufacturing Corp mock data
            generator = TechFlowDataGenerator()
            generator.DATABASE_PATH = demo_path
            generator.run_generation()
            
            # Restore original database path
            if original_db_path:
                os.environ["DATABASE_PATH"] = original_db_path
            
            self.demo_db_initialized = True
            logger.info(f"✅ Demo database initialized with TechFlow Manufacturing Corp data: {demo_path}")
            
        except Exception as e:
            logger.error(f"❌ Error initializing demo database: {e}")
            # Don't raise to allow system to continue
            self.demo_db_initialized = False
    
    def _initialize_production_database(self):
        """Initialize production database with basic schema"""
        try:
            from enhanced_database import init_enhanced_database
            
            prod_path = self.admin.get_database_path("production")
            
            # Temporarily set database path for production initialization
            original_db_path = os.environ.get("DATABASE_PATH")
            os.environ["DATABASE_PATH"] = prod_path
            
            # Initialize enhanced database schema only (no mock data)
            init_enhanced_database()
            
            # Restore original database path
            if original_db_path:
                os.environ["DATABASE_PATH"] = original_db_path
            
            self.production_db_initialized = True
            logger.info(f"✅ Production database initialized with schema: {prod_path}")
            
        except Exception as e:
            logger.error(f"❌ Error initializing production database: {e}")
            raise
    
    @contextmanager
    def get_database_connection(self, mode: Optional[str] = None):
        """Get database connection for specified mode"""
        if mode is None:
            mode = get_system_mode()
        
        db_path = get_database_path(mode)
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Enable row access by column name
            yield conn
        finally:
            conn.close()
    
    async def get_async_database_connection(self, mode: Optional[str] = None):
        """Get async database connection for specified mode"""
        if not AIOSQLITE_AVAILABLE:
            raise ImportError("aiosqlite is required for async database connections")
            
        if mode is None:
            mode = get_system_mode()
        
        db_path = get_database_path(mode)
        return await aiosqlite.connect(db_path)
    
    def switch_data_mode(self, new_mode: str, user_id: int, user_role: str, backup: bool = True) -> Dict[str, Any]:
        """
        Switch between demo and production data modes
        
        Args:
            new_mode: Target mode ('demo' or 'production')
            user_id: ID of user requesting switch
            user_role: Role of user requesting switch
            backup: Whether to create backup before switch
        
        Returns:
            Dict with switch result and details
        """
        try:
            # Validate user permissions
            if not self.admin.can_switch_mode(user_role):
                return {
                    "success": False,
                    "error": "Insufficient permissions to switch data mode",
                    "required_roles": self.admin.get_security_settings()["mode_switch_permissions"]
                }
            
            # Validate mode
            if new_mode not in ["demo", "production"]:
                return {
                    "success": False,
                    "error": "Invalid mode. Must be 'demo' or 'production'"
                }
            
            current_mode = get_system_mode()
            
            # Check if already in target mode
            if current_mode == new_mode:
                return {
                    "success": True,
                    "message": f"System is already in {new_mode} mode",
                    "mode": new_mode,
                    "changed": False
                }
            
            # Create backup if requested
            backup_success = True
            if backup:
                backup_success = self.admin.backup_database(current_mode, "mode_switch")
                if not backup_success:
                    logger.warning("⚠️ Backup failed, continuing with mode switch")
            
            # Perform the mode switch
            switch_result = self.admin.set_system_mode(new_mode, user_id)
            
            if switch_result["success"]:
                # Ensure target database exists and is ready
                self._ensure_target_database_ready(new_mode)
                
                # Update environment variable for immediate effect
                os.environ["DATABASE_PATH"] = get_database_path(new_mode)
                
                # Log success
                logger.info(f"🔄 Data mode switched from {current_mode} to {new_mode} by user {user_id}")
                
                # Get additional info about the switch
                mode_info = self._get_mode_info(new_mode)
                
                return {
                    "success": True,
                    "message": f"Successfully switched to {new_mode} mode",
                    "mode": new_mode,
                    "previous_mode": current_mode,
                    "changed": True,
                    "backup_created": backup_success,
                    "timestamp": switch_result["timestamp"],
                    "mode_info": mode_info
                }
            else:
                return switch_result
                
        except Exception as e:
            logger.error(f"❌ Error switching data mode: {e}")
            return {
                "success": False,
                "error": f"Failed to switch data mode: {str(e)}"
            }
    
    def _ensure_target_database_ready(self, mode: str):
        """Ensure target database exists and is properly initialized"""
        db_path = get_database_path(mode)
        
        if not os.path.exists(db_path):
            if mode == "demo":
                self._initialize_demo_database()
            else:
                self._initialize_production_database()
        
        # Verify database integrity
        try:
            with self.get_database_connection(mode) as conn:
                # Basic integrity check using database-agnostic query
                query, params = get_all_tables_query()
                conn.execute(query, params)
                tables = conn.fetchall()
                
                if len(tables) == 0:
                    raise Exception(f"Database {mode} appears to be empty")
                
                logger.info(f"✅ Database {mode} ready with {len(tables)} tables")
                
        except Exception as e:
            logger.error(f"❌ Database integrity check failed for {mode}: {e}")
            raise
    
    def _get_mode_info(self, mode: str) -> Dict[str, Any]:
        """Get detailed information about a data mode"""
        try:
            db_path = get_database_path(mode)
            db_exists = os.path.exists(db_path)
            db_size = os.path.getsize(db_path) if db_exists else 0
            
            # Get record counts if database exists
            record_counts = {}
            if db_exists:
                try:
                    with self.get_database_connection(mode) as conn:
                        tables = ["users", "assets", "work_orders", "parts", "locations", "suppliers"]
                        for table in tables:
                            try:
                                result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                                record_counts[table] = result[0] if result else 0
                            except sqlite3.OperationalError:
                                record_counts[table] = 0
                except Exception as e:
                    logger.warning(f"Could not get record counts for {mode}: {e}")
            
            return {
                "mode": mode,
                "database_path": db_path,
                "database_exists": db_exists,
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / (1024 * 1024), 2),
                "record_counts": record_counts,
                "features": self._get_mode_features(mode)
            }
            
        except Exception as e:
            logger.error(f"Error getting mode info for {mode}: {e}")
            return {"mode": mode, "error": str(e)}
    
    def _get_mode_features(self, mode: str) -> Dict[str, Any]:
        """Get features available in specified mode"""
        if mode == "demo":
            return {
                "company_name": "TechFlow Manufacturing Corp",
                "sample_data": True,
                "full_crud_operations": True,
                "workflow_testing": True,
                "report_generation": True,
                "ai_features": True,
                "mock_notifications": True,
                "training_mode": True,
                "data_reset_option": True,
                "watermarks": True
            }
        else:
            return {
                "company_name": "Production Company",
                "real_data": True,
                "full_crud_operations": True,
                "live_notifications": True,
                "data_persistence": True,
                "backup_systems": True,
                "audit_trails": True,
                "security_features": True,
                "integration_apis": True,
                "custom_workflows": True
            }
    
    def reset_demo_data(self, user_id: int, confirm: bool = False) -> Dict[str, Any]:
        """Reset demo database to original TechFlow Manufacturing Corp data"""
        try:
            if not confirm:
                return {
                    "success": False,
                    "error": "Confirmation required to reset demo data",
                    "confirmation_required": True
                }
            
            current_mode = get_system_mode()
            if current_mode != "demo":
                return {
                    "success": False,
                    "error": "Can only reset data in demo mode"
                }
            
            # Create backup before reset
            backup_success = self.admin.backup_database("demo", "data_reset")
            
            # Remove existing demo database
            demo_path = get_database_path("demo")
            if os.path.exists(demo_path):
                os.remove(demo_path)
            
            # Reinitialize with fresh mock data
            self._initialize_demo_database()
            
            logger.info(f"🔄 Demo data reset completed by user {user_id}")
            
            return {
                "success": True,
                "message": "Demo data reset to TechFlow Manufacturing Corp defaults",
                "backup_created": backup_success,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error resetting demo data: {e}")
            return {
                "success": False,
                "error": f"Failed to reset demo data: {str(e)}"
            }
    
    def migrate_data(self, source_mode: str, target_mode: str, migration_type: str = "copy") -> Dict[str, Any]:
        """
        Migrate data between demo and production databases
        
        Args:
            source_mode: Source database mode
            target_mode: Target database mode
            migration_type: 'copy', 'move', or 'merge'
        """
        try:
            if migration_type not in ["copy", "move", "merge"]:
                return {
                    "success": False,
                    "error": "Invalid migration type. Must be 'copy', 'move', or 'merge'"
                }
            
            # Create backups before migration
            source_backup = self.admin.backup_database(source_mode, "pre_migration")
            target_backup = self.admin.backup_database(target_mode, "pre_migration")
            
            # Perform migration based on type
            if migration_type == "copy":
                result = self._copy_database(source_mode, target_mode)
            elif migration_type == "move":
                result = self._move_database(source_mode, target_mode)
            else:  # merge
                result = self._merge_databases(source_mode, target_mode)
            
            if result["success"]:
                logger.info(f"📊 Data migration completed: {source_mode} -> {target_mode} ({migration_type})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in data migration: {e}")
            return {
                "success": False,
                "error": f"Data migration failed: {str(e)}"
            }
    
    def _copy_database(self, source_mode: str, target_mode: str) -> Dict[str, Any]:
        """Copy entire database from source to target"""
        try:
            source_path = get_database_path(source_mode)
            target_path = get_database_path(target_mode)
            
            if not os.path.exists(source_path):
                return {
                    "success": False,
                    "error": f"Source database does not exist: {source_path}"
                }
            
            # Copy database file
            shutil.copy2(source_path, target_path)
            
            return {
                "success": True,
                "message": f"Database copied from {source_mode} to {target_mode}",
                "migration_type": "copy"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to copy database: {str(e)}"
            }
    
    def _move_database(self, source_mode: str, target_mode: str) -> Dict[str, Any]:
        """Move database from source to target (copy + clear source)"""
        # First copy
        copy_result = self._copy_database(source_mode, target_mode)
        if not copy_result["success"]:
            return copy_result
        
        # Then reinitialize source
        try:
            if source_mode == "demo":
                self._initialize_demo_database()
            else:
                self._initialize_production_database()
            
            return {
                "success": True,
                "message": f"Database moved from {source_mode} to {target_mode}",
                "migration_type": "move"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to reinitialize source database: {str(e)}"
            }
    
    def _merge_databases(self, source_mode: str, target_mode: str) -> Dict[str, Any]:
        """Merge data from source into target (advanced operation)"""
        # This is a complex operation that would require careful handling
        # of primary keys, relationships, and potential conflicts
        return {
            "success": False,
            "error": "Database merge functionality not yet implemented",
            "note": "This feature requires careful design to handle data conflicts and relationships"
        }
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview including both modes"""
        try:
            current_mode = get_system_mode()
            demo_info = self._get_mode_info("demo")
            production_info = self._get_mode_info("production")
            
            # Get recent mode switches
            mode_history = self.admin.get_mode_switch_history(10)
            
            # Get system settings
            demo_features = self.admin.get_demo_features()
            ai_settings = self.admin.get_ai_brain_settings()
            ui_settings = self.admin.get_ui_settings()
            company_setup = self.admin.get_company_setup()
            
            return {
                "current_mode": current_mode,
                "demo_mode": demo_info,
                "production_mode": production_info,
                "mode_switch_history": mode_history,
                "settings": {
                    "demo_features": demo_features,
                    "ai_brain": ai_settings,
                    "ui_settings": ui_settings,
                    "company_setup": company_setup
                },
                "capabilities": {
                    "mode_switching": True,
                    "data_migration": True,
                    "backup_system": True,
                    "demo_reset": True,
                    "ai_integration": True,
                    "company_wizard": True
                },
                "recommendations": self._get_ai_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Error getting system overview: {e}")
            return {
                "error": str(e),
                "current_mode": get_system_mode()
            }
    
    def _get_ai_recommendations(self) -> List[Dict[str, Any]]:
        """Get AI-powered recommendations for system optimization"""
        recommendations = []
        
        try:
            current_mode = get_system_mode()
            demo_info = self._get_mode_info("demo")
            production_info = self._get_mode_info("production")
            company_setup = self.admin.get_company_setup()
            
            # Recommend switching to production if company setup is complete
            if current_mode == "demo" and company_setup.get("completed", False):
                recommendations.append({
                    "type": "mode_switch",
                    "priority": "high",
                    "title": "Ready for Production Mode",
                    "description": "Your company setup is complete. Consider switching to production mode for real operations.",
                    "action": "switch_to_production",
                    "icon": "🚀"
                })
            
            # Recommend demo mode for testing
            if current_mode == "production" and not company_setup.get("completed", False):
                recommendations.append({
                    "type": "mode_switch",
                    "priority": "medium",
                    "title": "Try Demo Mode First",
                    "description": "Complete company setup and test features in demo mode before production use.",
                    "action": "switch_to_demo",
                    "icon": "🧪"
                })
            
            # Recommend data backup
            last_backup = self.admin.get_mode_switch_history(1)
            if not last_backup or (datetime.now() - datetime.fromisoformat(last_backup[0]["timestamp"])).days > 7:
                recommendations.append({
                    "type": "backup",
                    "priority": "medium",
                    "title": "Create Data Backup",
                    "description": "Consider creating a backup of your current data for safety.",
                    "action": "create_backup",
                    "icon": "💾"
                })
            
            # Recommend demo reset if demo data is old or modified significantly
            if current_mode == "demo":
                recommendations.append({
                    "type": "demo_reset",
                    "priority": "low",
                    "title": "Reset Demo Data",
                    "description": "Reset to fresh TechFlow Manufacturing Corp data for clean testing.",
                    "action": "reset_demo_data",
                    "icon": "🔄"
                })
            
        except Exception as e:
            logger.error(f"Error generating AI recommendations: {e}")
        
        return recommendations
    
    def get_company_setup_wizard_data(self) -> Dict[str, Any]:
        """Get data for company setup wizard"""
        try:
            current_setup = self.admin.get_company_setup()
            
            # Industry options
            industries = [
                "Manufacturing", "Healthcare", "Education", "Retail", "Food Service",
                "Automotive", "Aerospace", "Pharmaceuticals", "Chemical Processing",
                "Energy & Utilities", "Transportation", "Technology", "Other"
            ]
            
            # Employee count ranges
            employee_ranges = [
                {"label": "1-10 employees", "value": "1-10"},
                {"label": "11-50 employees", "value": "11-50"},
                {"label": "51-200 employees", "value": "51-200"},
                {"label": "201-500 employees", "value": "201-500"},
                {"label": "501+ employees", "value": "501+"}
            ]
            
            # Facility types
            facility_types = [
                "Manufacturing Plant", "Warehouse", "Office Building", "Hospital",
                "School Campus", "Retail Store", "Restaurant", "Hotel", "Other"
            ]
            
            return {
                "current_setup": current_setup,
                "options": {
                    "industries": industries,
                    "employee_ranges": employee_ranges,
                    "facility_types": facility_types
                },
                "steps": [
                    {
                        "id": "company_info",
                        "title": "Company Information",
                        "description": "Basic company details and industry",
                        "fields": ["company_name", "industry", "employee_count"]
                    },
                    {
                        "id": "facilities",
                        "title": "Facilities & Locations",
                        "description": "Add your facilities and locations",
                        "fields": ["facilities"]
                    },
                    {
                        "id": "preferences",
                        "title": "System Preferences",
                        "description": "Configure system settings and preferences",
                        "fields": ["timezone", "currency", "units"]
                    },
                    {
                        "id": "review",
                        "title": "Review & Complete",
                        "description": "Review your setup and complete configuration",
                        "fields": []
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting company setup wizard data: {e}")
            return {"error": str(e)}

# Global data toggle system instance
data_toggle_system = DataToggleSystem()

# Convenience functions for easy access
def switch_data_mode(new_mode: str, user_id: int, user_role: str, backup: bool = True) -> Dict[str, Any]:
    """Switch data mode"""
    return data_toggle_system.switch_data_mode(new_mode, user_id, user_role, backup)

def reset_demo_data(user_id: int, confirm: bool = False) -> Dict[str, Any]:
    """Reset demo data"""
    return data_toggle_system.reset_demo_data(user_id, confirm)

def get_system_overview() -> Dict[str, Any]:
    """Get system overview"""
    return data_toggle_system.get_system_overview()

def get_database_connection(mode: Optional[str] = None):
    """Get database connection"""
    return data_toggle_system.get_database_connection(mode)

def migrate_data(source_mode: str, target_mode: str, migration_type: str = "copy") -> Dict[str, Any]:
    """Migrate data between modes"""
    return data_toggle_system.migrate_data(source_mode, target_mode, migration_type)

if __name__ == "__main__":
    # Test the data toggle system
    print("🔄 ChatterFix CMMS Data Toggle System")
    print("=" * 50)
    
    system = DataToggleSystem()
    overview = system.get_system_overview()
    
    print(f"Current mode: {overview['current_mode']}")
    print(f"Demo DB size: {overview['demo_mode']['database_size_mb']} MB")
    print(f"Production DB size: {overview['production_mode']['database_size_mb']} MB")
    print(f"AI recommendations: {len(overview['recommendations'])}")
    
    for rec in overview['recommendations']:
        print(f"  {rec['icon']} {rec['title']} ({rec['priority']})")
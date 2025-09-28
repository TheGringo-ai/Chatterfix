#!/usr/bin/env python3
"""
ChatterFix CMMS Admin Module
Manages system configuration including data mode (demo/production)
Provides centralized admin controls and settings management
"""

import sqlite3
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdminManager:
    """Centralized admin configuration manager"""
    
    def __init__(self):
        self.config_file = "./data/admin_config.json"
        self.config_lock_file = "./data/.admin_config.lock"
        self.default_config = {
            "system_mode": "production",  # demo or production
            "demo_features": {
                "show_sample_data": True,
                "limited_functionality": False,
                "demo_watermark": True,
                "auto_reset_data": False,
                "mock_ai_responses": True,
                "restrict_user_creation": True,
                "disable_email_notifications": True
            },
            "company_setup": {
                "completed": False,
                "company_name": "",
                "industry": "",
                "employee_count": 0,
                "facilities": []
            },
            "database_settings": {
                "demo_db_path": "./data/cmms_demo.db",
                "production_db_path": "./data/cmms_production.db",
                "auto_backup_on_switch": True,
                "backup_retention_days": 30
            },
            "ai_brain_settings": {
                "smart_mode_detection": True,
                "auto_recommendations": True,
                "performance_monitoring": True,
                "adaptive_learning": True
            },
            "security_settings": {
                "require_admin_approval": True,
                "mode_switch_permissions": ["Administrator", "Manager"],
                "audit_mode_switches": True
            },
            "ui_settings": {
                "show_mode_indicator": True,
                "show_toggle_button": True,
                "toggle_position": "header",
                "confirmation_dialogs": True
            },
            "created_date": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "last_mode_switch": None,
            "mode_switch_count": 0
        }
        
        # Ensure data directory exists
        os.makedirs("./data", exist_ok=True)
        
        # Initialize config if it doesn't exist
        self._init_config()
    
    def _init_config(self):
        """Initialize admin configuration file"""
        if not os.path.exists(self.config_file):
            self._save_config(self.default_config)
            logger.info("🔧 Admin configuration initialized with default settings")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load admin configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged_config = self.default_config.copy()
                    merged_config.update(config)
                    return merged_config
            return self.default_config.copy()
        except Exception as e:
            logger.error(f"Error loading admin config: {e}")
            return self.default_config.copy()
    
    def _save_config(self, config: Dict[str, Any]):
        """Save admin configuration to file"""
        try:
            config["last_modified"] = datetime.now().isoformat()
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("💾 Admin configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving admin config: {e}")
            raise
    
    def get_system_mode(self) -> str:
        """Get current system mode (demo/production)"""
        config = self._load_config()
        return config.get("system_mode", "production")
    
    def set_system_mode(self, mode: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Set system mode with validation and logging"""
        if mode not in ["demo", "production"]:
            raise ValueError("Mode must be 'demo' or 'production'")
        
        config = self._load_config()
        old_mode = config.get("system_mode", "production")
        
        if old_mode == mode:
            return {
                "success": True,
                "message": f"System already in {mode} mode",
                "mode": mode,
                "changed": False
            }
        
        # Update configuration
        config["system_mode"] = mode
        config["last_mode_switch"] = datetime.now().isoformat()
        config["mode_switch_count"] += 1
        
        # Log the change
        if user_id:
            self._log_mode_switch(old_mode, mode, user_id)
        
        # Save configuration
        self._save_config(config)
        
        logger.info(f"🔄 System mode changed from {old_mode} to {mode}")
        
        return {
            "success": True,
            "message": f"System mode changed to {mode}",
            "mode": mode,
            "previous_mode": old_mode,
            "changed": True,
            "timestamp": config["last_mode_switch"]
        }
    
    def get_demo_features(self) -> Dict[str, Any]:
        """Get demo features configuration"""
        config = self._load_config()
        return config.get("demo_features", self.default_config["demo_features"])
    
    def update_demo_features(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Update demo features configuration"""
        config = self._load_config()
        config["demo_features"].update(features)
        self._save_config(config)
        
        return {
            "success": True,
            "message": "Demo features updated successfully",
            "features": config["demo_features"]
        }
    
    def get_company_setup(self) -> Dict[str, Any]:
        """Get company setup configuration"""
        config = self._load_config()
        return config.get("company_setup", self.default_config["company_setup"])
    
    def update_company_setup(self, setup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update company setup configuration"""
        config = self._load_config()
        config["company_setup"].update(setup_data)
        
        # Mark setup as completed if basic info is provided
        if setup_data.get("company_name") and setup_data.get("industry"):
            config["company_setup"]["completed"] = True
        
        self._save_config(config)
        
        return {
            "success": True,
            "message": "Company setup updated successfully",
            "setup": config["company_setup"]
        }
    
    def get_database_path(self, mode: Optional[str] = None) -> str:
        """Get database path for specified mode (or current mode)"""
        if mode is None:
            mode = self.get_system_mode()
        
        config = self._load_config()
        db_settings = config.get("database_settings", self.default_config["database_settings"])
        
        if mode == "demo":
            return db_settings.get("demo_db_path", "./data/cmms_demo.db")
        else:
            return db_settings.get("production_db_path", "./data/cmms_production.db")
    
    def get_ai_brain_settings(self) -> Dict[str, Any]:
        """Get AI brain configuration"""
        config = self._load_config()
        return config.get("ai_brain_settings", self.default_config["ai_brain_settings"])
    
    def update_ai_brain_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update AI brain settings"""
        config = self._load_config()
        config["ai_brain_settings"].update(settings)
        self._save_config(config)
        
        return {
            "success": True,
            "message": "AI brain settings updated successfully",
            "settings": config["ai_brain_settings"]
        }
    
    def get_security_settings(self) -> Dict[str, Any]:
        """Get security settings"""
        config = self._load_config()
        return config.get("security_settings", self.default_config["security_settings"])
    
    def can_switch_mode(self, user_role: str) -> bool:
        """Check if user role can switch data mode"""
        security_settings = self.get_security_settings()
        allowed_roles = security_settings.get("mode_switch_permissions", ["Administrator"])
        return user_role in allowed_roles
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """Get UI settings for data mode toggle"""
        config = self._load_config()
        return config.get("ui_settings", self.default_config["ui_settings"])
    
    def update_ui_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update UI settings"""
        config = self._load_config()
        config["ui_settings"].update(settings)
        self._save_config(config)
        
        return {
            "success": True,
            "message": "UI settings updated successfully",
            "settings": config["ui_settings"]
        }
    
    def _log_mode_switch(self, old_mode: str, new_mode: str, user_id: int):
        """Log mode switch for audit purposes"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "old_mode": old_mode,
                "new_mode": new_mode,
                "action": "mode_switch"
            }
            
            audit_log_file = "./data/mode_switch_audit.log"
            with open(audit_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
            
            logger.info(f"📝 Mode switch logged: {old_mode} -> {new_mode} by user {user_id}")
        except Exception as e:
            logger.error(f"Error logging mode switch: {e}")
    
    def get_mode_switch_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent mode switch history"""
        try:
            audit_log_file = "./data/mode_switch_audit.log"
            if not os.path.exists(audit_log_file):
                return []
            
            history = []
            with open(audit_log_file, 'r') as f:
                lines = f.readlines()
                for line in reversed(lines[-limit:]):
                    try:
                        history.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            
            return history
        except Exception as e:
            logger.error(f"Error reading mode switch history: {e}")
            return []
    
    def backup_database(self, source_mode: str, backup_reason: str = "mode_switch") -> bool:
        """Create backup of database before mode switch"""
        try:
            source_db = self.get_database_path(source_mode)
            if not os.path.exists(source_db):
                logger.warning(f"Source database not found: {source_db}")
                return True  # No backup needed if source doesn't exist
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{source_mode}_{backup_reason}_{timestamp}.db"
            backup_path = f"./data/backups/{backup_name}"
            
            # Ensure backup directory exists
            os.makedirs("./data/backups", exist_ok=True)
            
            # Copy database file
            import shutil
            shutil.copy2(source_db, backup_path)
            
            logger.info(f"💾 Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        config = self._load_config()
        
        # Check database files
        demo_db_exists = os.path.exists(self.get_database_path("demo"))
        prod_db_exists = os.path.exists(self.get_database_path("production"))
        
        # Get database sizes
        demo_db_size = 0
        prod_db_size = 0
        
        if demo_db_exists:
            demo_db_size = os.path.getsize(self.get_database_path("demo"))
        if prod_db_exists:
            prod_db_size = os.path.getsize(self.get_database_path("production"))
        
        return {
            "system_mode": config.get("system_mode"),
            "demo_features": config.get("demo_features"),
            "company_setup": config.get("company_setup"),
            "ai_brain_settings": config.get("ai_brain_settings"),
            "ui_settings": config.get("ui_settings"),
            "database_status": {
                "demo_db_exists": demo_db_exists,
                "production_db_exists": prod_db_exists,
                "demo_db_size": demo_db_size,
                "production_db_size": prod_db_size,
                "demo_db_path": self.get_database_path("demo"),
                "production_db_path": self.get_database_path("production")
            },
            "mode_switch_count": config.get("mode_switch_count", 0),
            "last_mode_switch": config.get("last_mode_switch"),
            "created_date": config.get("created_date"),
            "last_modified": config.get("last_modified")
        }

# Global admin manager instance
admin_manager = AdminManager()

# Convenience functions for backward compatibility with system_mode.py
def get_system_mode() -> str:
    """Get current system mode"""
    return admin_manager.get_system_mode()

def get_demo_features() -> Dict[str, Any]:
    """Get demo features configuration"""
    return admin_manager.get_demo_features()

def set_system_mode(mode: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Set system mode"""
    return admin_manager.set_system_mode(mode, user_id)

def get_database_path(mode: Optional[str] = None) -> str:
    """Get database path for mode"""
    return admin_manager.get_database_path(mode)

def can_switch_mode(user_role: str) -> bool:
    """Check if user can switch mode"""
    return admin_manager.can_switch_mode(user_role)

def get_system_status() -> Dict[str, Any]:
    """Get system status"""
    return admin_manager.get_system_status()

if __name__ == "__main__":
    # Test the admin manager
    admin = AdminManager()
    print("🔧 ChatterFix CMMS Admin Manager")
    print("=" * 40)
    
    status = admin.get_system_status()
    print(f"Current mode: {status['system_mode']}")
    print(f"Demo DB exists: {status['database_status']['demo_db_exists']}")
    print(f"Production DB exists: {status['database_status']['production_db_exists']}")
    print(f"Company setup completed: {status['company_setup']['completed']}")
    print(f"Mode switches: {status['mode_switch_count']}")
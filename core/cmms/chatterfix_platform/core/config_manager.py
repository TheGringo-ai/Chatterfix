#!/usr/bin/env python3
"""
ChatterFix AI Development Platform - Configuration Manager
Centralized configuration management for all platform components
"""

import os
import json
import logging
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class ConfigSection:
    """Configuration section metadata"""
    name: str
    description: str
    schema: Dict[str, Any]
    required: bool = False
    default_values: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.default_values is None:
            self.default_values = {}

class ConfigManager:
    """Centralized configuration management system"""
    
    def __init__(self, config_dir: str = "platform/config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config: Dict[str, Any] = {}
        self.schemas: Dict[str, ConfigSection] = {}
        self.watchers: Dict[str, list] = {}
        
        # Register core configuration sections
        self._register_core_schemas()
        
        # Load configuration
        self.load_all_configs()
    
    def _register_core_schemas(self):
        """Register core configuration schemas"""
        
        # Platform core configuration
        self.register_schema(ConfigSection(
            name="platform",
            description="Core platform configuration",
            required=True,
            schema={
                "name": {"type": "string", "required": True},
                "version": {"type": "string", "required": True},
                "debug": {"type": "boolean", "default": False},
                "max_plugins": {"type": "integer", "default": 50},
                "plugin_timeout": {"type": "integer", "default": 30}
            },
            default_values={
                "name": "ChatterFix AI Development Platform",
                "version": "1.0.0",
                "debug": False,
                "max_plugins": 50,
                "plugin_timeout": 30
            }
        ))
        
        # Database configuration
        self.register_schema(ConfigSection(
            name="database",
            description="Database connection and pooling settings",
            required=True,
            schema={
                "type": {"type": "string", "enum": ["sqlite", "postgresql"], "default": "sqlite"},
                "url": {"type": "string"},
                "pool_size": {"type": "integer", "default": 10},
                "timeout": {"type": "integer", "default": 30},
                "retry_attempts": {"type": "integer", "default": 3}
            },
            default_values={
                "type": "sqlite",
                "pool_size": 10,
                "timeout": 30,
                "retry_attempts": 3
            }
        ))
        
        # Service discovery configuration
        self.register_schema(ConfigSection(
            name="service_discovery",
            description="Service discovery and health monitoring",
            required=True,
            schema={
                "enabled": {"type": "boolean", "default": True},
                "check_interval": {"type": "integer", "default": 30},
                "timeout": {"type": "integer", "default": 5},
                "retry_attempts": {"type": "integer", "default": 3}
            },
            default_values={
                "enabled": True,
                "check_interval": 30,
                "timeout": 5,
                "retry_attempts": 3
            }
        ))
        
        # API Gateway configuration
        self.register_schema(ConfigSection(
            name="api_gateway",
            description="API Gateway routing and middleware settings",
            required=True,
            schema={
                "host": {"type": "string", "default": "0.0.0.0"},
                "port": {"type": "integer", "default": 8000},
                "cors_enabled": {"type": "boolean", "default": True},
                "rate_limiting": {"type": "boolean", "default": True},
                "rate_limit_requests": {"type": "integer", "default": 100},
                "rate_limit_window": {"type": "integer", "default": 60}
            },
            default_values={
                "host": "0.0.0.0",
                "port": 8000,
                "cors_enabled": True,
                "rate_limiting": True,
                "rate_limit_requests": 100,
                "rate_limit_window": 60
            }
        ))
        
        # Security configuration
        self.register_schema(ConfigSection(
            name="security",
            description="Security and authentication settings",
            required=True,
            schema={
                "jwt_secret": {"type": "string", "required": True},
                "token_expiry_hours": {"type": "integer", "default": 24},
                "max_login_attempts": {"type": "integer", "default": 5},
                "password_min_length": {"type": "integer", "default": 8},
                "require_2fa": {"type": "boolean", "default": False}
            },
            default_values={
                "token_expiry_hours": 24,
                "max_login_attempts": 5,
                "password_min_length": 8,
                "require_2fa": False
            }
        ))
        
        # Logging configuration
        self.register_schema(ConfigSection(
            name="logging",
            description="Logging configuration for all services",
            required=True,
            schema={
                "level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR"], "default": "INFO"},
                "format": {"type": "string", "default": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
                "file_enabled": {"type": "boolean", "default": True},
                "file_path": {"type": "string", "default": "logs/platform.log"},
                "max_file_size": {"type": "integer", "default": 10485760},  # 10MB
                "backup_count": {"type": "integer", "default": 5}
            },
            default_values={
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_enabled": True,
                "file_path": "logs/platform.log",
                "max_file_size": 10485760,
                "backup_count": 5
            }
        ))
    
    def register_schema(self, section: ConfigSection):
        """Register a configuration schema"""
        self.schemas[section.name] = section
        
        # Set default values if section doesn't exist
        if section.name not in self.config:
            self.config[section.name] = section.default_values.copy()
            
        logger.debug(f"Registered config schema: {section.name}")
    
    def load_all_configs(self):
        """Load all configuration files"""
        config_files = [
            self.config_dir / "platform.json",
            self.config_dir / "platform.yaml",
            self.config_dir / "platform.yml"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                self.load_config_file(config_file)
                break
        else:
            # No config file found, create default
            self.create_default_config()
    
    def load_config_file(self, file_path: Union[str, Path]):
        """Load configuration from file"""
        file_path = Path(file_path)
        
        try:
            with open(file_path, 'r') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            # Merge with existing config
            self._deep_merge(self.config, data)
            
            logger.info(f"Loaded configuration from {file_path}")
            
            # Validate configuration
            self.validate_config()
            
        except Exception as e:
            logger.error(f"Failed to load config file {file_path}: {e}")
    
    def save_config(self, file_format: str = "json"):
        """Save current configuration to file"""
        if file_format.lower() == "yaml":
            config_file = self.config_dir / "platform.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
        else:
            config_file = self.config_dir / "platform.json"
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        
        logger.info(f"Saved configuration to {config_file}")
    
    def create_default_config(self):
        """Create default configuration file"""
        # Use default values from all registered schemas
        for name, schema in self.schemas.items():
            self.config[name] = schema.default_values.copy()
        
        # Add metadata
        self.config["_metadata"] = {
            "created_at": datetime.now().isoformat(),
            "created_by": "ChatterFix AI Development Platform",
            "version": "1.0.0"
        }
        
        # Save default config
        self.save_config()
        
        logger.info("Created default configuration")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        
        # Navigate to parent
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set value
        config[keys[-1]] = value
        
        # Notify watchers
        self._notify_watchers(key, value)
        
        logger.debug(f"Set config {key} = {value}")
    
    def get_section(self, section_name: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.config.get(section_name, {})
    
    def set_section(self, section_name: str, values: Dict[str, Any]):
        """Set entire configuration section"""
        self.config[section_name] = values
        
        # Notify watchers for all keys in section
        for key, value in values.items():
            self._notify_watchers(f"{section_name}.{key}", value)
        
        logger.debug(f"Set config section: {section_name}")
    
    def validate_config(self) -> Dict[str, list]:
        """Validate configuration against schemas"""
        errors = {}
        
        for section_name, schema in self.schemas.items():
            section_errors = []
            section_config = self.config.get(section_name, {})
            
            # Check required section
            if schema.required and not section_config:
                section_errors.append(f"Required section '{section_name}' is missing")
                continue
            
            # Validate each field in schema
            for field_name, field_schema in schema.schema.items():
                field_value = section_config.get(field_name)
                
                # Check required fields
                if field_schema.get("required", False) and field_value is None:
                    section_errors.append(f"Required field '{field_name}' is missing")
                    continue
                
                # Skip validation if field is not set and not required
                if field_value is None:
                    continue
                
                # Type validation
                expected_type = field_schema.get("type")
                if expected_type and not self._validate_type(field_value, expected_type):
                    section_errors.append(f"Field '{field_name}' has invalid type, expected {expected_type}")
                
                # Enum validation
                if "enum" in field_schema and field_value not in field_schema["enum"]:
                    section_errors.append(f"Field '{field_name}' must be one of {field_schema['enum']}")
            
            if section_errors:
                errors[section_name] = section_errors
        
        if errors:
            logger.warning(f"Configuration validation errors: {errors}")
        
        return errors
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type"""
        type_map = {
            "string": str,
            "integer": int,
            "boolean": bool,
            "number": (int, float),
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            return True  # Unknown type, skip validation
        
        return isinstance(value, expected_python_type)
    
    def watch(self, key: str, callback: callable):
        """Watch for changes to a configuration key"""
        if key not in self.watchers:
            self.watchers[key] = []
        
        self.watchers[key].append(callback)
        logger.debug(f"Added watcher for config key: {key}")
    
    def unwatch(self, key: str, callback: callable):
        """Remove watcher for configuration key"""
        if key in self.watchers:
            try:
                self.watchers[key].remove(callback)
                if not self.watchers[key]:
                    del self.watchers[key]
                logger.debug(f"Removed watcher for config key: {key}")
            except ValueError:
                pass
    
    def _notify_watchers(self, key: str, value: Any):
        """Notify watchers of configuration changes"""
        if key in self.watchers:
            for callback in self.watchers[key]:
                try:
                    callback(key, value)
                except Exception as e:
                    logger.error(f"Error in config watcher for {key}: {e}")
    
    def _deep_merge(self, base: dict, overlay: dict):
        """Deep merge two dictionaries"""
        for key, value in overlay.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def export_config(self) -> Dict[str, Any]:
        """Export current configuration"""
        return {
            "config": self.config,
            "schemas": {name: asdict(schema) for name, schema in self.schemas.items()},
            "exported_at": datetime.now().isoformat()
        }
    
    def import_config(self, config_data: Dict[str, Any]):
        """Import configuration data"""
        try:
            if "config" in config_data:
                self.config = config_data["config"]
            
            if "schemas" in config_data:
                for name, schema_data in config_data["schemas"].items():
                    schema = ConfigSection(**schema_data)
                    self.schemas[name] = schema
            
            # Validate imported config
            errors = self.validate_config()
            if errors:
                logger.warning(f"Imported config has validation errors: {errors}")
            
            logger.info("Successfully imported configuration")
            
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            raise

# Global configuration manager instance
config_manager = ConfigManager()
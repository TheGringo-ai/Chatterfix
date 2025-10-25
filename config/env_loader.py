#!/usr/bin/env python3
"""
ChatterFix CMMS - Secure Environment Variable Loader
Handles loading environment variables from various sources securely
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class EnvironmentLoader:
    """Secure environment variable loader for ChatterFix CMMS"""
    
    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file
        self.config: Dict[str, Any] = {}
        self.load_environment()
    
    def load_environment(self):
        """Load environment variables from file and system"""
        # Try to load from .env file if specified
        if self.env_file:
            self._load_from_file(self.env_file)
        else:
            # Auto-detect environment file
            self._auto_load_env_file()
        
        # Load system environment variables (these override file values)
        self._load_from_system()
        
        # Validate required variables
        self._validate_required_variables()
    
    def _auto_load_env_file(self):
        """Auto-detect and load the appropriate .env file"""
        base_dir = Path(__file__).parent.parent
        
        # Priority order for env files
        env_files = [
            '.env.local',
            '.env.production', 
            '.env',
            '.env.template'
        ]
        
        for env_file in env_files:
            env_path = base_dir / env_file
            if env_path.exists():
                logger.info(f"Loading environment from: {env_file}")
                self._load_from_file(str(env_path))
                break
        else:
            logger.warning("No environment file found")
    
    def _load_from_file(self, file_path: str):
        """Load environment variables from file"""
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        self.config[key] = value
        except FileNotFoundError:
            logger.warning(f"Environment file not found: {file_path}")
        except Exception as e:
            logger.error(f"Error loading environment file {file_path}: {e}")
    
    def _load_from_system(self):
        """Load environment variables from system (Cloud Run, etc.)"""
        system_vars = [
            'OPENAI_API_KEY',
            'DATABASE_URL',
            'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD',
            'PYTHON_ENV', 'NODE_ENV',
            'PORT', 'HOST',
            'LOG_LEVEL',
            'WORK_ORDERS_URL', 'ASSETS_URL', 'PARTS_URL',
            'AI_BRAIN_URL', 'CUSTOMER_SUCCESS_URL',
            'GOOGLE_CLOUD_PROJECT'
        ]
        
        for var in system_vars:
            value = os.environ.get(var)
            if value:
                self.config[var] = value
    
    def _validate_required_variables(self):
        """Validate that required environment variables are present"""
        required_vars = [
            'OPENAI_API_KEY',
            'DATABASE_URL'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not self.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get environment variable value"""
        return self.config.get(key, default)
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration"""
        return {
            'url': self.get('DATABASE_URL'),
            'host': self.get('DB_HOST'),
            'port': self.get('DB_PORT', '5432'),
            'name': self.get('DB_NAME'),
            'user': self.get('DB_USER'),
            'password': self.get('DB_PASSWORD'),
            'ssl_mode': self.get('DB_SSL_MODE', 'require')
        }
    
    def get_openai_config(self) -> Dict[str, str]:
        """Get OpenAI configuration"""
        return {
            'api_key': self.get('OPENAI_API_KEY'),
            'model': self.get('OPENAI_MODEL', 'gpt-4-turbo-preview'),
            'max_tokens': int(self.get('OPENAI_MAX_TOKENS', '4000'))
        }
    
    def get_service_urls(self) -> Dict[str, str]:
        """Get microservice URLs"""
        return {
            'work_orders': self.get('WORK_ORDERS_URL'),
            'assets': self.get('ASSETS_URL'),
            'parts': self.get('PARTS_URL'),
            'ai_brain': self.get('AI_BRAIN_URL'),
            'customer_success': self.get('CUSTOMER_SUCCESS_URL'),
            'voice_ai': self.get('VOICE_AI_URL'),
            'revenue_intelligence': self.get('REVENUE_INTELLIGENCE_URL'),
            'data_room': self.get('DATA_ROOM_URL')
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        env = self.get('PYTHON_ENV', self.get('NODE_ENV', 'development'))
        return env.lower() == 'production'
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get('DEBUG', 'false').lower() in ('true', '1', 'yes')

# Global environment loader instance
env = EnvironmentLoader()

# Helper functions for easy access
def get_env(key: str, default: Any = None) -> Any:
    """Get environment variable value"""
    return env.get(key, default)

def get_database_config() -> Dict[str, str]:
    """Get database configuration"""
    return env.get_database_config()

def get_openai_config() -> Dict[str, str]:
    """Get OpenAI configuration"""  
    return env.get_openai_config()

def get_service_urls() -> Dict[str, str]:
    """Get microservice URLs"""
    return env.get_service_urls()

def is_production() -> bool:
    """Check if running in production"""
    return env.is_production()

def is_debug() -> bool:
    """Check if debug mode is enabled"""
    return env.is_debug()

if __name__ == "__main__":
    # Test the environment loader
    print("🔧 ChatterFix Environment Configuration")
    print("=" * 50)
    print(f"Environment: {'Production' if is_production() else 'Development'}")
    print(f"Debug Mode: {is_debug()}")
    print(f"Database Host: {get_database_config()['host']}")
    print(f"OpenAI Model: {get_openai_config()['model']}")
    print(f"Work Orders URL: {get_service_urls()['work_orders']}")
    print("=" * 50)
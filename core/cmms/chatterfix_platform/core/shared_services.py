#!/usr/bin/env python3
"""
ChatterFix AI Development Platform - Shared Services Framework
Provides common services that all apps can use
"""

import os
import logging
import httpx
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import json
from contextlib import asynccontextmanager

# Import ChatterFix database utilities
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database_utils import get_db_connection, execute_query, check_database_health

logger = logging.getLogger(__name__)

class DatabaseService:
    """Shared database access layer for all plugins"""
    
    def __init__(self):
        self.connection_pool = {}
    
    async def execute_query(self, query: str, params: Union[List, Dict] = None, fetch: str = "one"):
        """Execute database query with connection pooling"""
        return await execute_query(query, params, fetch)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database health"""
        return await check_database_health()
    
    @asynccontextmanager
    async def get_connection(self):
        """Get database connection context manager"""
        connection = await get_db_connection()
        try:
            yield connection
        finally:
            if hasattr(connection, 'close'):
                connection.close()

class AuthenticationService:
    """Shared authentication and authorization service"""
    
    def __init__(self, backend_url: str = None):
        self.backend_url = backend_url or os.getenv("BACKEND_SERVICE_URL", "http://localhost:8088")
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify an authentication token"""
        try:
            response = await self.client.post(
                f"{self.backend_url}/auth/verify",
                json={"token": token}
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        try:
            response = await self.client.post(
                f"{self.backend_url}/users",
                json=user_data
            )
            
            if response.status_code == 201:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"User creation failed: {e}")
            return None
    
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """Get user permissions"""
        try:
            response = await self.client.get(
                f"{self.backend_url}/users/{user_id}/permissions"
            )
            
            if response.status_code == 200:
                return response.json().get("permissions", [])
            return []
            
        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            return []
    
    async def check_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has specific permission"""
        permissions = await self.get_user_permissions(user_id)
        return permission in permissions

class ConfigurationService:
    """Shared configuration management"""
    
    def __init__(self, config_file: str = "platform/config/shared_config.json"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                # Create default config
                self.config = {
                    "database": {
                        "pool_size": 10,
                        "timeout": 30
                    },
                    "ai_providers": {
                        "default": "openai",
                        "retry_attempts": 3,
                        "timeout": 30
                    },
                    "logging": {
                        "level": "INFO",
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    },
                    "security": {
                        "token_expiry_hours": 24,
                        "max_login_attempts": 5
                    }
                }
                self.save_config()
                
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config = {}
    
    def save_config(self):
        """Save configuration to file"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        self.save_config()

class AIProviderService:
    """Shared AI provider access"""
    
    def __init__(self, ai_service_url: str = None):
        self.ai_service_url = ai_service_url or os.getenv("AI_SERVICE_URL", "http://localhost:8089")
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def generate_text(self, prompt: str, provider: str = "openai", model: str = None) -> Optional[str]:
        """Generate text using AI provider"""
        try:
            request_data = {
                "prompt": prompt,
                "providers": [provider]
            }
            
            if model:
                request_data["model"] = model
            
            response = await self.client.post(
                f"{self.ai_service_url}/ai/multi-ai",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response")
            return None
            
        except Exception as e:
            logger.error(f"AI text generation failed: {e}")
            return None
    
    async def analyze_image(self, image_description: str, analysis_type: str = "condition_assessment") -> Optional[Dict[str, Any]]:
        """Analyze image using computer vision"""
        try:
            response = await self.client.post(
                f"{self.ai_service_url}/ai/computer-vision",
                json={
                    "image_description": image_description,
                    "analysis_type": analysis_type
                }
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return None
    
    async def process_voice_to_text(self, voice_text: str) -> Optional[Dict[str, Any]]:
        """Process voice input to create work orders"""
        try:
            response = await self.client.post(
                f"{self.ai_service_url}/ai/voice-to-work-order",
                json={"voice_text": voice_text}
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"Voice processing failed: {e}")
            return None

class LoggingService:
    """Centralized logging service for all plugins"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(f"platform.{service_name}")
        
        # Configure logging format
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def info(self, message: str, extra: Dict[str, Any] = None):
        """Log info message"""
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, extra: Dict[str, Any] = None):
        """Log warning message"""
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, extra: Dict[str, Any] = None):
        """Log error message"""
        self.logger.error(message, extra=extra)
    
    def debug(self, message: str, extra: Dict[str, Any] = None):
        """Log debug message"""
        self.logger.debug(message, extra=extra)

class SharedServices:
    """Main shared services container"""
    
    def __init__(self):
        self.database = DatabaseService()
        self.auth = AuthenticationService()
        self.config = ConfigurationService()
        self.ai = AIProviderService()
        self._loggers = {}
    
    def get_logger(self, service_name: str) -> LoggingService:
        """Get or create logger for service"""
        if service_name not in self._loggers:
            self._loggers[service_name] = LoggingService(service_name)
        return self._loggers[service_name]
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all shared services"""
        health = {
            "database": {"status": "unknown"},
            "auth": {"status": "unknown"},
            "ai": {"status": "unknown"},
            "config": {"status": "healthy"},
            "timestamp": datetime.now().isoformat()
        }
        
        # Check database
        try:
            db_health = await self.database.health_check()
            health["database"] = db_health
        except Exception as e:
            health["database"] = {"status": "unhealthy", "error": str(e)}
        
        # Check auth service
        try:
            response = await self.auth.client.get(f"{self.auth.backend_url}/health")
            health["auth"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            health["auth"] = {"status": "unhealthy", "error": str(e)}
        
        # Check AI service
        try:
            response = await self.ai.client.get(f"{self.ai.ai_service_url}/health")
            health["ai"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            health["ai"] = {"status": "unhealthy", "error": str(e)}
        
        return health

# Global shared services instance
shared_services = SharedServices()
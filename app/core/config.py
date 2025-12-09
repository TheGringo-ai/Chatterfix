"""
Secure Configuration Management
Centralized, validated configuration using Pydantic Settings
Handles API keys, database connections, and environment-specific settings
"""

import os
import logging
from typing import Optional, List
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, validator
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings, Field, validator
from functools import lru_cache

logger = logging.getLogger(__name__)


class AIServiceConfig(BaseSettings):
    """AI Service API Keys and Configuration"""
    
    # Primary AI Services
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")  
    grok_api_key: Optional[str] = Field(None, env="XAI_API_KEY")
    
    # Extended AI Services
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    ollama_host: str = Field("http://localhost:11434", env="OLLAMA_HOST")
    
    # AI Service Preferences
    default_ai_model: str = Field("gemini", env="DEFAULT_AI_MODEL")
    enable_multi_ai_consensus: bool = Field(True, env="ENABLE_MULTI_AI_CONSENSUS")
    ai_request_timeout: int = Field(30, env="AI_REQUEST_TIMEOUT")
    
    @validator('gemini_api_key')
    def validate_gemini_key(cls, v):
        if v and not v.startswith('AIza'):
            logger.warning("⚠️ Gemini API key format looks suspicious")
        return v
    
    @validator('openai_api_key')  
    def validate_openai_key(cls, v):
        if v and not v.startswith('sk-'):
            logger.warning("⚠️ OpenAI API key should start with 'sk-'")
        return v
    
    @validator('grok_api_key')
    def validate_grok_key(cls, v):
        if v and len(v) < 10:
            logger.warning("⚠️ Grok API key seems too short")
        return v
    
    def has_ai_capability(self, service: str) -> bool:
        """Check if a specific AI service is configured"""
        key_map = {
            "gemini": self.gemini_api_key,
            "openai": self.openai_api_key,
            "grok": self.grok_api_key,
            "anthropic": self.anthropic_api_key
        }
        return key_map.get(service.lower()) is not None
    
    def get_available_services(self) -> List[str]:
        """Get list of configured AI services"""
        services = []
        if self.gemini_api_key:
            services.append("gemini")
        if self.openai_api_key:
            services.append("openai") 
        if self.grok_api_key:
            services.append("grok")
        if self.anthropic_api_key:
            services.append("anthropic")
        return services


class DatabaseConfig(BaseSettings):
    """Database Configuration"""
    
    # Firestore (Primary)
    use_firestore: bool = Field(True, env="USE_FIRESTORE")
    google_cloud_project: Optional[str] = Field(None, env="GOOGLE_CLOUD_PROJECT")
    google_application_credentials: Optional[str] = Field(None, env="GOOGLE_APPLICATION_CREDENTIALS")
    firebase_database_url: Optional[str] = Field(None, env="FIREBASE_DATABASE_URL")
    
    # SQLite (Fallback)
    sqlite_db_path: str = Field("./data/cmms.db", env="CMMS_DB_PATH")
    
    @validator('google_application_credentials')
    def validate_credentials_file(cls, v):
        if v and not os.path.exists(v):
            logger.warning(f"⚠️ Google credentials file not found: {v}")
        return v


class SecurityConfig(BaseSettings):
    """Security and Authentication Configuration"""
    
    secret_key: str = Field(..., env="SECRET_KEY")
    session_expire_hours: int = Field(24, env="SESSION_EXPIRE_HOURS")
    
    # Security Headers
    enable_https_only: bool = Field(True, env="ENABLE_HTTPS_ONLY") 
    allowed_hosts: List[str] = Field(["chatterfix.com", "*.chatterfix.com"], env="ALLOWED_HOSTS")
    
    # Rate Limiting
    rate_limit_requests: int = Field(100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(60, env="RATE_LIMIT_WINDOW")  # seconds
    
    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            logger.error("❌ SECRET_KEY must be at least 32 characters long")
            raise ValueError("SECRET_KEY too short for production use")
        return v


class ApplicationConfig(BaseSettings):
    """Main Application Configuration"""
    
    # Application Info
    app_name: str = Field("ChatterFix CMMS", env="APP_NAME")
    app_version: str = Field("2.1.0-enterprise-planner", env="APP_VERSION")
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    
    # Server Configuration  
    host: str = Field("0.0.0.0", env="CMMS_HOST")
    port: int = Field(8000, env="CMMS_PORT")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field("logs/chatterfix.log", env="LOG_FILE")
    
    @validator('environment')
    def validate_environment(cls, v):
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            logger.warning(f"⚠️ Environment '{v}' not in {valid_envs}")
        return v
    
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


class Settings(BaseSettings):
    """Complete Application Settings"""
    
    # Configuration Sections
    ai: AIServiceConfig = AIServiceConfig()
    database: DatabaseConfig = DatabaseConfig()
    security: SecurityConfig = SecurityConfig()
    app: ApplicationConfig = ApplicationConfig()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_ai_config(self) -> AIServiceConfig:
        """Get AI service configuration"""
        return self.ai
    
    def get_db_config(self) -> DatabaseConfig:
        """Get database configuration"""
        return self.database
    
    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        return self.security
    
    def get_app_config(self) -> ApplicationConfig:
        """Get application configuration"""
        return self.app
    
    def validate_configuration(self) -> bool:
        """Validate that critical configuration is present"""
        
        issues = []
        
        # Check AI services
        if not any([self.ai.gemini_api_key, self.ai.openai_api_key]):
            issues.append("No AI service API keys configured")
        
        # Check database
        if self.database.use_firestore and not self.database.google_cloud_project:
            issues.append("Firestore enabled but GOOGLE_CLOUD_PROJECT not set")
            
        # Check security
        if not self.security.secret_key:
            issues.append("SECRET_KEY not configured")
            
        if issues:
            logger.error("❌ Configuration validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
            
        logger.info("✅ Configuration validation passed")
        return True
    
    def get_configuration_summary(self) -> dict:
        """Get sanitized configuration summary for logging"""
        return {
            "app_name": self.app.app_name,
            "app_version": self.app.app_version,
            "environment": self.app.environment,
            "ai_services_configured": self.ai.get_available_services(),
            "database_type": "firestore" if self.database.use_firestore else "sqlite",
            "security_enabled": bool(self.security.secret_key),
            "debug_mode": self.app.debug
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings
    Uses LRU cache to avoid reloading configuration multiple times
    """
    return Settings()


# Global settings instance for easy import
settings = get_settings()


# Configuration validation at startup
if __name__ == "__main__":
    config = get_settings()
    if config.validate_configuration():
        print("✅ Configuration is valid")
        print("📋 Configuration Summary:")
        summary = config.get_configuration_summary()
        for key, value in summary.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Configuration validation failed")
        exit(1)
"""
Configuration settings for AI Team Service
"""

import os
from typing import List

class Settings:
    """Application settings"""
    
    # Service configuration
    SERVICE_NAME: str = "AI Team Service"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # API configuration
    API_V1_STR: str = "/api/v1"
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "ai-team-service-key-change-me")
    
    # AI model configuration
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    XAI_API_KEY: str = os.getenv("XAI_API_KEY", "")
    
    # Memory and database configuration
    FIRESTORE_PROJECT_ID: str = os.getenv("FIRESTORE_PROJECT_ID", "fredfix")
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "fredfix")
    
    # Performance configuration
    MAX_CONCURRENT_TASKS: int = int(os.getenv("MAX_CONCURRENT_TASKS", "10"))
    TASK_TIMEOUT_SECONDS: int = int(os.getenv("TASK_TIMEOUT_SECONDS", "300"))  # 5 minutes
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS configuration
    ALLOWED_ORIGINS: List[str] = [
        "https://chatterfix.com",
        "https://www.chatterfix.com",
        "https://gringo-core-psycl7nhha-uc.a.run.app",
        "http://localhost:8000",  # Local development
    ]
    
    def __init__(self):
        # Validate required API keys
        if not any([self.ANTHROPIC_API_KEY, self.OPENAI_API_KEY, self.GEMINI_API_KEY, self.XAI_API_KEY]):
            raise ValueError("At least one AI model API key must be configured")

settings = Settings()
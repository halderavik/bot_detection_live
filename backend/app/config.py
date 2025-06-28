"""
Configuration settings for the Bot Detection API.

This module uses Pydantic Settings to manage environment variables
and application configuration with validation and type safety.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    APP_NAME: str = "Bot Detection API"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/bot_detection"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Bot Detection API"
    BASE_URL: str = "http://localhost:8000"
    
    # Redis settings (for caching and session storage)
    REDIS_URL: str = "redis://localhost:6379"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Bot detection settings
    DETECTION_THRESHOLD: float = 0.7
    SESSION_TIMEOUT_MINUTES: int = 30
    MAX_EVENTS_PER_SESSION: int = 10000
    
    # Integration settings
    QUALTRICS_API_TOKEN: Optional[str] = None
    DECIPHER_API_KEY: Optional[str] = None
    
    # Monitoring settings
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate required settings
def validate_settings():
    """Validate critical settings on startup."""
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-here":
        raise ValueError("SECRET_KEY must be set in environment variables")
    
    if settings.DEBUG:
        print("⚠️  Running in DEBUG mode - not suitable for production")

# Validate on import
validate_settings() 
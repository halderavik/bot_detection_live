"""
Configuration settings for the Bot Detection API.

This module uses Pydantic Settings to manage environment variables
and application configuration with validation and type safety.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator
from typing import List, Optional
import os
import json

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    APP_NAME: str = "Bot Detection API"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database settings
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/bot_detection"
    
    @field_validator('DATABASE_URL')
    @classmethod
    def strip_database_url(cls, v: str) -> str:
        """Strip whitespace and carriage returns from DATABASE_URL."""
        if v:
            # Remove all whitespace including \r, \n, and spaces from ends
            return v.strip().replace('\r', '').replace('\n', '')
        return v
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here"
    # Shared with the survey builder; when set, surveys created with a token are protected.
    TRACKING_TOKEN_SECRET: Optional[str] = None
    # Public API base the survey tracker calls (https://.../api/v1). When empty, the
    # Decipher XML upload uses the origin of the upload request.
    TRACKER_API_BASE: Optional[str] = None
    # Required to change settings from the dashboard's Settings page (sent as X-Admin-Token).
    # Environment only: it can never be changed from the page itself. Unset means the page is read-only.
    ADMIN_TOKEN: Optional[str] = None
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: str = '["http://localhost:3000", "http://localhost:5173"]'
    
    def get_allowed_origins(self) -> List[str]:
        """Parse ALLOWED_ORIGINS from JSON string."""
        try:
            return json.loads(self.ALLOWED_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            # Fallback to default if parsing fails
            return ["http://localhost:3000", "http://localhost:5173"]
    
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
    # Decipher REST API used to upload tracked survey XML.
    DECIPHER_API_BASE: str = "https://selfserve.decipherinc.com/api/v1"
    DECIPHER_COMPANY: str = "self"
    
    # Monitoring settings
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_TOKENS: int = 500
    OPENAI_TEMPERATURE: float = 0.3
    OPENAI_TIMEOUT: int = 30
    OPENAI_MAX_RETRIES: int = 3
    # Open-end checks: OpenAI calls allowed per minute on one server, and how long an
    # answer waits for a free slot before it is stored as not checked.
    # Database connections kept open per server (PostgreSQL), and extra ones allowed in a burst.
    # 0 turns the pool off (a new connection per request).
    DB_POOL_SIZE: int = 4
    DB_MAX_OVERFLOW: int = 4
    OPENAI_REQUESTS_PER_MINUTE: int = 300
    OPENAI_RATE_WAIT_SECONDS: float = 20.0
    # Model for "Fix with AI" on survey XML; empty uses gpt-4o (services/decipher_ai_fix.py).
    OPENAI_FIX_MODEL: Optional[str] = None

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def strip_openai_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Strip whitespace and carriage returns from OPENAI_API_KEY.

        Reason:
            Secrets from some systems (including Secret Manager via CLI piping)
            can include a trailing newline/CRLF, which breaks HTTP header parsing
            in the OpenAI client ("Illegal header value ... \\r\\n").

        Args:
            v (Optional[str]): Raw API key string.

        Returns:
            Optional[str]: Sanitized API key.
        """
        if v is None:
            return None
        # Remove leading/trailing whitespace and embedded CR/LF characters.
        return v.strip().replace("\r", "").replace("\n", "")
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True
    )

# Create settings instance
settings = Settings()

# Validate required settings
def validate_settings():
    """Validate critical settings on startup."""
    if not settings.SECRET_KEY or settings.SECRET_KEY == "your-secret-key-here":
        raise ValueError("SECRET_KEY must be set in environment variables")
    
    if settings.DEBUG:
        print("WARNING: Running in DEBUG mode - not suitable for production")

# Validate on import
validate_settings() 
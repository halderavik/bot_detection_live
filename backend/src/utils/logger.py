"""
Logging utility for the Bot Detection API.

This module provides centralized logging configuration and utilities
for consistent logging across the application.
"""

import logging
import sys
from typing import Optional

from config.config import settings


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (optional, uses config default if not provided)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set log level
    log_level = level or settings.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Avoid adding handlers if they already exist
    if logger.handlers:
        return logger
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def setup_logging():
    """Setup root logging configuration."""
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format=settings.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Create application logger
    app_logger = get_logger("bot_detection_api")
    app_logger.info("Logging system initialized")


class RequestLogger:
    """Request logging middleware helper."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(self, method: str, url: str, status_code: int, 
                   processing_time: float, user_agent: str = None, 
                   ip_address: str = None):
        """Log HTTP request details."""
        self.logger.info(
            f"Request: {method} {url} - Status: {status_code} - "
            f"Time: {processing_time:.2f}ms - "
            f"User-Agent: {user_agent or 'Unknown'} - "
            f"IP: {ip_address or 'Unknown'}"
        )
    
    def log_error(self, method: str, url: str, error: Exception, 
                  user_agent: str = None, ip_address: str = None):
        """Log request errors."""
        self.logger.error(
            f"Request Error: {method} {url} - "
            f"Error: {str(error)} - "
            f"User-Agent: {user_agent or 'Unknown'} - "
            f"IP: {ip_address or 'Unknown'}"
        ) 
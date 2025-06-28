"""
Logging configuration and utilities.

This module provides centralized logging configuration with consistent
formatting and log levels across the application.
"""

import logging
import sys
from typing import Optional
from app.config import settings

def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Setup a logger with consistent configuration.
    
    Args:
        name: Logger name (usually __name__)
        level: Log level (optional, defaults to settings.LOG_LEVEL)
        
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

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

# Create default logger
default_logger = setup_logger("bot_detection") 
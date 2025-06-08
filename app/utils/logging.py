"""Logging configuration and utilities."""

import logging
import sys
from typing import Optional

from app.core.config import settings


def setup_logging(logger_name: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration."""
    
    # Create logger
    logger = logging.getLogger(logger_name or __name__)
    
    # Set level
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Avoid adding multiple handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logging("ai_chat_agent") 
"""Centralized logging configuration for PixelPilot.

Provides consistent logging setup across all modules with configurable
levels, formats, and output destinations.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from .config import get_config


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_to_file: Optional[bool] = None,
    log_file_path: Optional[str] = None
) -> logging.Logger:
    """
    Setup and configure a logger with consistent formatting.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, reads from config.
        log_to_file: Whether to log to file. If None, reads from config.
        log_file_path: Path to log file. If None, reads from config.
        
    Returns:
        Configured logger instance
        
    Example:
        >>> from src.utils.logger import setup_logger
        >>> logger = setup_logger(__name__)
        >>> logger.info("Application started")
    """
    # Get configuration
    config = get_config()
    
    if level is None:
        level = config.get('logging.level', 'INFO')
    if log_to_file is None:
        log_to_file = config.get('logging.file', False)
    if log_file_path is None:
        log_file_path = config.get('logging.file_path', 'pixelpilot.log')
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    log_format = config.get(
        'logging.format',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    formatter = logging.Formatter(log_format)
    
    # Console handler
    if config.get('logging.console', True):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
        
    Example:
        >>> from src.utils.logger import get_logger
        >>> logger = get_logger(__name__)
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger

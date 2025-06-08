"""
Logging Configuration Module

This module provides logging configuration and utilities for the GitHub
Project Manager MCP Server. It supports environment-based configuration and
provides standardized logging across the application.
"""

import logging
import os
import sys
from typing import Optional

# Default configuration constants
DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Logger instance cache
_loggers = {}


def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None,
    date_format: Optional[str] = None,
    stream: Optional[object] = None,
) -> None:
    """
    Set up logging configuration for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, uses LOG_LEVEL environment variable or DEFAULT_LOG_LEVEL.
        format_string: Custom log format string. If None, uses LOG_FORMAT.
        date_format: Custom date format string. If None, uses DATE_FORMAT.
        stream: Output stream for logging. If None, uses sys.stdout.
    """
    # Determine log level
    if level is None:
        level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Use default format if not provided
    if format_string is None:
        format_string = LOG_FORMAT

    if date_format is None:
        date_format = DATE_FORMAT

    # Use stdout if no stream provided
    if stream is None:
        stream = sys.stdout

    # Create formatter
    formatter = logging.Formatter(format_string, date_format)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create and configure stream handler
    handler = logging.StreamHandler(stream)  # type: ignore
    handler.setLevel(numeric_level)
    handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger.addHandler(handler)

    # Log the configuration
    logger = get_logger(__name__)
    logger.info(f"Logging configured with level: {level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.

    This function caches logger instances to avoid creating duplicates
    and ensures consistent configuration across the application.

    Args:
        name: Name for the logger, typically __name__ of the calling module.

    Returns:
        Configured Logger instance.
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        _loggers[name] = logger

    return _loggers[name]


def set_log_level(level: str) -> None:
    """
    Change the log level for all configured loggers.

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Update root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Update all handlers
    for handler in root_logger.handlers:
        handler.setLevel(numeric_level)

    logger = get_logger(__name__)
    logger.info(f"Log level changed to: {level}")


def configure_third_party_logging() -> None:
    """
    Configure logging for third-party libraries to reduce noise.

    This function sets higher log levels for common third-party libraries
    to prevent them from cluttering the application logs.
    """
    # Reduce noise from common libraries
    third_party_loggers = [
        "httpx",
        "httpcore",
        "urllib3",
        "requests",
        "asyncio",
    ]

    for logger_name in third_party_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)


def log_environment_info() -> None:
    """
    Log relevant environment information for debugging purposes.
    """
    logger = get_logger(__name__)

    # Log Python version
    logger.info(f"Python version: {sys.version}")

    # Log relevant environment variables
    env_vars = ["LOG_LEVEL", "GITHUB_TOKEN", "MCP_SERVER_HOST", "MCP_SERVER_PORT"]
    for var in env_vars:
        value = os.getenv(var)
        if var == "GITHUB_TOKEN" and value:
            # Don't log the actual token, just indicate it's set
            logger.info(f"{var}: {'SET' if value else 'NOT SET'}")
        else:
            logger.info(f"{var}: {value}")


# Initialize logging on module import if in production
if __name__ != "__main__" and not sys.argv[0].endswith("pytest"):
    setup_logging()
    configure_third_party_logging()

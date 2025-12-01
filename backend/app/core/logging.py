"""
Structured logging configuration using structlog.
"""
import sys
import structlog
from typing import Any
from datetime import datetime

from app.core.config import settings


def configure_logging() -> None:
    """Configure structured logging for the application."""
    
    # Determine processors based on format
    processors = [
        structlog.stdlib.add_log_level,

        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    # Add JSON or console rendering
    if settings.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True if sys.stderr.isatty() else False
            )
        )
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)


# Initialize logging on module import
configure_logging()

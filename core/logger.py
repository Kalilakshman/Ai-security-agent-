"""
Structured logging module for AI Security Orchestrator CLI.

Provides rich colored console logging for CLI interactivity
and JSON structured logs for security auditing / CI/CD pipelines.
"""

import sys
import logging
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler

_console = Console()
_initialized = False


def get_console() -> Console:
    """Return shared Rich Console instance."""
    return _console


def setup_logger(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Initialize and configure global application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_format: If True, output logs in structured JSON format.
        log_file: Optional path to append log file output.

    Returns:
        Configured standard logging.Logger instance for 'security_ai'.
    """
    global _initialized
    logger = logging.getLogger("security_ai")
    
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Avoid duplicate handlers if re-initialized
    if logger.hasHandlers():
        logger.handlers.clear()

    handlers: list[logging.Handler] = []

    if json_format:
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"module": "%(module)s", "message": "%(message)s"}'
        )
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        handlers.append(stream_handler)
    else:
        rich_handler = RichHandler(
            console=_console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        rich_handler.setFormatter(logging.Formatter("%(message)s"))
        handlers.append(rich_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s standard: %(message)s")
        )
        handlers.append(file_handler)

    for h in handlers:
        logger.addHandler(h)

    _initialized = True
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a child logger instance under 'security_ai' domain hierarchy."""
    base_logger = logging.getLogger("security_ai")
    if not base_logger.handlers:
        setup_logger()
    if name:
        return logging.getLogger(f"security_ai.{name}")
    return base_logger

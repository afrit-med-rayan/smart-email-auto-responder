import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pythonjsonlogger import jsonlogger
import os
from pathlib import Path
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive data from logs."""
    
    SENSITIVE_KEYS = [
        'password', 'token', 'secret', 'api_key', 'client_secret',
        'refresh_token', 'access_token', 'authorization'
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Redact sensitive data from log messages."""
        if hasattr(record, 'msg'):
            msg = str(record.msg).lower()
            for key in self.SENSITIVE_KEYS:
                if key in msg:
                    record.msg = record.msg.replace(
                        record.msg[msg.find(key):msg.find(key) + 50],
                        f"{key}=***REDACTED***"
                    )
        return True


def setup_logging(
    service_name: str,
    log_level: Optional[str] = None,
    log_dir: str = "logs",
    environment: Optional[str] = None
) -> None:
    """
    Configure structured logging for the service with environment-based formatting.
    
    Args:
        service_name: Name of the service (e.g., "API", "ModelServer")
        log_level: Logging level (default: from env LOG_LEVEL or INFO)
        log_dir: Directory to store log files
        environment: Environment (development, staging, production). Auto-detected from env.
    """
    # Get configuration from environment
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True, parents=True)
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates during reloads
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add sensitive data filter
    sensitive_filter = SensitiveDataFilter()
    
    # Choose formatter based on environment
    if environment == "production":
        # JSON formatter for production (machine-readable)
        formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d %(funcName)s',
            timestamp=True
        )
    else:
        # Human-readable formatter for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(sensitive_filter)
    logger.addHandler(console_handler)
    
    # File Handler (Daily rotation, keep 7 days)
    file_handler = TimedRotatingFileHandler(
        filename=log_path / f"{service_name.lower()}.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    
    # Always use JSON format for file logs (easier to parse)
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d %(funcName)s',
        timestamp=True
    )
    file_handler.setFormatter(json_formatter)
    file_handler.addFilter(sensitive_filter)
    logger.addHandler(file_handler)
    
    # Create a startup log entry
    service_logger = logging.getLogger(service_name)
    service_logger.info(
        f"Logging initialized for {service_name}",
        extra={
            "environment": environment,
            "log_level": log_level,
            "service": service_name
        }
    )


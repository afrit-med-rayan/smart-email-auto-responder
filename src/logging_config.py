import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pythonjsonlogger import jsonlogger
import os
from pathlib import Path

def setup_logging(service_name: str, log_level: str = "INFO", log_dir: str = "logs"):
    """
    Configure structured JSON logging for the service.
    
    Args:
        service_name: Name of the service (e.g., "API", "ModelServer")
        log_level: Logging level (default: INFO)
        log_dir: Directory to store log files
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True, parents=True)
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates during reloads
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # JSON Formatter
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler (Daily rotation, keep 7 days)
    file_handler = TimedRotatingFileHandler(
        filename=log_path / f"{service_name.lower()}.log",
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Create a startup log entry
    logging.getLogger(service_name).info(f"Logging initialized for {service_name}")

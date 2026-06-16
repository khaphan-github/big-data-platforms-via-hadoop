import logging
from logging.handlers import RotatingFileHandler
from config.settings import settings
from pathlib import Path

# Create logs directory if it doesn't exist
logs_dir = Path(settings.LOG_FILE).parent
logs_dir.mkdir(parents=True, exist_ok=True)


def setup_logger(name: str) -> logging.Logger:
    """Setup logger with both file and console handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(settings.LOG_LEVEL)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10485760,  # 10MB
        backupCount=5,
    )
    file_handler.setLevel(settings.LOG_LEVEL)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.LOG_LEVEL)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

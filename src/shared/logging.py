"""
logging.py
Structured JSON logging shared across all microservices.
"""
import logging
import sys


def setup_logger(service_name: str, level: int = logging.INFO) -> logging.Logger:
    """Configure and return a JSON-structured logger for a microservice."""
    fmt = (
        '{"time": "%(asctime)s", "level": "%(levelname)s", '
        f'"service": "{service_name}", '
        '"module": "%(module)s", "message": "%(message)s"}'
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))

    logger = logging.getLogger(service_name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.propagate = False
    return logger

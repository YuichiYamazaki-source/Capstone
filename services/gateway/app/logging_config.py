"""Structured JSON logging configuration for Gateway service."""

import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging(service_name: str = "gateway", level: str = "INFO") -> None:
    """Configure structured JSON logging for the service."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    )
    formatter.json_ensure_ascii = False
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.getLogger(service_name).info(
        "Logging initialized", extra={"service": service_name, "log_level": level}
    )

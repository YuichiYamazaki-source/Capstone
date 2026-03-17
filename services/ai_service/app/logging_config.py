import logging
import sys

from pythonjsonlogger import jsonlogger


def setup_logging(service_name: str = "ai-service", level: str = "INFO") -> None:
    """Configure structured JSON logging for the service.

    Args:
        service_name: Logger name used as the root namespace.
        level: Logging level string (e.g. "INFO", "DEBUG").
    """
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={
            "asctime": "timestamp",
            "levelname": "level",
            "name": "logger",
        },
    )
    formatter.json_ensure_ascii = False
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.getLogger(service_name).info(
        "Logging initialized",
        extra={"service": service_name, "log_level": level},
    )

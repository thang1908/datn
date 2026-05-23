"""Structured logging setup."""

import logging
import logging.config

from .config import settings


class OpenTelemetryContextFilter(logging.Filter):
    """Filter to suppress spurious OpenTelemetry context detach errors.

    These errors occur when async tasks create context in one context and
    detach in another. They don't affect functionality and are safe to ignore.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Suppress OpenTelemetry context detach errors."""
        if record.name == "opentelemetry.context":
            # Suppress the "Failed to detach context" error
            if "Failed to detach context" in record.getMessage():
                # Check if it's the specific ValueError we want to suppress
                if record.exc_info and record.exc_info[0] is ValueError:
                    exc_text = str(record.exc_info[1])
                    if "was created in a different Context" in exc_text:
                        return False
        return True


def setup_logging() -> None:
    """Configure structured logging for the application."""
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
            },
        },
        "handlers": {
            "default": {
                "level": settings.log_level,
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": settings.log_level,
                "propagate": True,
            },
            "urllib3": {
                "level": "WARNING",
            },
            "httpcore": {
                "level": "WARNING",
            },
            "google.generativeai": {
                "level": "WARNING",
            },
        },
    }

    logging.config.dictConfig(logging_config)

    # Add filter to suppress OpenTelemetry context errors
    opentelemetry_logger = logging.getLogger("opentelemetry.context")
    opentelemetry_logger.addFilter(OpenTelemetryContextFilter())

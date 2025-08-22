import logging
import json
from datetime import datetime, timezone
from logging.config import dictConfig
from contextvars import ContextVar

_correlation_id_var: ContextVar[str | None] = ContextVar(
    "_correlation_id_var", default=None
)


class CorrelationIdFilter(logging.Filter):
    """Фильтр для добавления correlation ID в лог-записи."""

    def filter(self, record):
        record.correlation_id = _correlation_id_var.get() or "N/A"
        return True


class JsonFormatter(logging.Formatter):
    """Форматтер для structured logging в JSON."""

    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "correlation_id": record.correlation_id,
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_logging():
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {"()": JsonFormatter},
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(asctime)s - %(name)s - %(message)s",
            },
        },
        "filters": {
            "correlation_id": {"()": CorrelationIdFilter},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["correlation_id"],
                "stream": "ext://sys.stderr",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filters": ["correlation_id"],
                "filename": "app.log",
                "maxBytes": 10485760,  # 10 MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {"handlers": ["console", "file"], "level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
    dictConfig(config)


logger = logging.getLogger(__name__)


def set_correlation_id(correlation_id: str) -> None:
    """Устанавливает correlation ID в контексте."""
    _correlation_id_var.set(correlation_id)

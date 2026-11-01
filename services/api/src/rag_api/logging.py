"""JSON-lines logging: ts, level, service, msg (+ run_id, stage when bound)."""

import logging
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog

from rag_api.ids import to_iso, utcnow


def _add_ts(_: Any, __: str, event: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    event["ts"] = to_iso(utcnow())
    return event


def _rename_event(_: Any, __: str, event: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    event["msg"] = event.pop("event", "")
    return event


def configure_logging(level: str = "INFO", service: str = "api") -> None:
    logging.basicConfig(stream=sys.stdout, level=level, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            _add_ts,
            structlog.processors.format_exc_info,
            _rename_event,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level)),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    structlog.contextvars.bind_contextvars(service=service)

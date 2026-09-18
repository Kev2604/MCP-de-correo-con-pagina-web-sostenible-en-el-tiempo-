from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from typing import Any


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }
        if hasattr(record, "request_id"):
            payload["request_id"] = getattr(record, "request_id")
        if hasattr(record, "tool_name"):
            payload["tool_name"] = getattr(record, "tool_name")
        if hasattr(record, "result"):
            payload["result"] = getattr(record, "result")
        if hasattr(record, "error_code"):
            payload["error_code"] = getattr(record, "error_code")
        if hasattr(record, "duration_ms"):
            payload["duration_ms"] = getattr(record, "duration_ms")
        if hasattr(record, "recipients_count"):
            payload["recipients_count"] = getattr(record, "recipients_count")
        if hasattr(record, "attachments_count"):
            payload["attachments_count"] = getattr(record, "attachments_count")
        return str(payload)


def configure_logging(level: str = "INFO") -> logging.Logger:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO), format="%(message)s", stream=sys.stdout, force=True)
    logger = logging.getLogger("email_mcp")
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.propagate = False
    return logger

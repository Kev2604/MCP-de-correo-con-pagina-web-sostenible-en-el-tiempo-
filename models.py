from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class EmailRequest:
    to: list[str]
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    subject: str = ""
    body: str = ""
    html: str | None = None
    attachments: list[str] = field(default_factory=list)
    reply_to: str | None = None
    sender_name: str | None = None
    priority: str = "normal"
    headers: dict[str, str] = field(default_factory=dict)
    request_id: str | None = None
    dry_run: bool = False


@dataclass(slots=True)
class EmailResult:
    success: bool
    message: str
    request_id: str
    recipients_count: int
    attachments_count: int
    dry_run: bool
    error_code: str | None = None
    preview: dict[str, Any] | None = None

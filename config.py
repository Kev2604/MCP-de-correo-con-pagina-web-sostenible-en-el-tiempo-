from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from exceptions import SMTPConfigurationError


@dataclass(slots=True)
class EmailServerConfig:
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_tls: bool = True
    smtp_ssl: bool = False
    smtp_timeout: int = 30
    max_body_size: int = 1024 * 1024
    max_html_size: int = 1024 * 1024
    max_attachment_size: int = 5 * 1024 * 1024
    max_total_size: int = 10 * 1024 * 1024
    max_attachments: int = 5
    max_recipients: int = 50
    allowed_extensions: tuple[str, ...] = ("pdf", "docx", "txt", "png", "jpg", "jpeg", "gif")
    allowed_domains: tuple[str, ...] = ()
    allowed_recipients: tuple[str, ...] = ()
    dry_run: bool = False
    log_level: str = "INFO"
    environment: str = "development"
    template_dir: str = "templates"
    retries: int = 2
    retry_backoff_seconds: float = 1.0
    require_tls: bool = False
    privacy_mode: bool = False
    upload_dir: str = "uploads"

    def validate(self, *, require_credentials: bool = True) -> None:
        if not self.smtp_host:
            raise SMTPConfigurationError("SMTP_HOST es obligatorio.", "SMTP_CONFIGURATION_ERROR")
        if self.smtp_port <= 0 or self.smtp_port > 65535:
            raise SMTPConfigurationError("SMTP_PORT debe estar entre 1 y 65535.", "SMTP_CONFIGURATION_ERROR")
        if self.max_body_size <= 0 or self.max_html_size <= 0 or self.max_attachment_size <= 0 or self.max_total_size <= 0:
            raise SMTPConfigurationError("Los límites de tamaño deben ser mayores que cero.", "SMTP_CONFIGURATION_ERROR")
        if self.max_recipients <= 0 or self.max_attachments <= 0:
            raise SMTPConfigurationError("Los límites de destinatarios y adjuntos deben ser mayores que cero.", "SMTP_CONFIGURATION_ERROR")
        if require_credentials:
            if not self.smtp_user:
                raise SMTPConfigurationError("SMTP_USER es obligatorio.", "SMTP_CONFIGURATION_ERROR")
            if not self.smtp_password:
                raise SMTPConfigurationError("SMTP_PASSWORD es obligatorio.", "SMTP_CONFIGURATION_ERROR")
        if not self.smtp_from:
            self.smtp_from = self.smtp_user


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "on"}:
            return True
        if lowered in {"0", "false", "no", "off"}:
            return False
    return default


def _coerce_int(value: Any, default: int) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return default


def _coerce_list(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        return tuple(item.strip() for item in value.split(",") if item.strip())
    if isinstance(value, (list, tuple, set)):
        return tuple(str(item).strip() for item in value if str(item).strip())
    return ()


def load_config(*, env: dict[str, str] | None = None, require_credentials: bool = False) -> EmailServerConfig:
    values = env if env is not None else os.environ
    environment = values.get("APP_ENV", "development")
    config = EmailServerConfig(
        smtp_host=values.get("SMTP_HOST", "").strip(),
        smtp_port=_coerce_int(values.get("SMTP_PORT"), 587),
        smtp_user=values.get("SMTP_USER", "").strip(),
        smtp_password=values.get("SMTP_PASSWORD", "").strip(),
        smtp_from=values.get("SMTP_FROM", "").strip(),
        smtp_tls=_coerce_bool(values.get("SMTP_TLS"), True),
        smtp_ssl=_coerce_bool(values.get("SMTP_SSL"), False),
        smtp_timeout=_coerce_int(values.get("SMTP_TIMEOUT"), 30),
        max_body_size=_coerce_int(values.get("MAX_BODY_SIZE"), 1024 * 1024),
        max_html_size=_coerce_int(values.get("MAX_HTML_SIZE"), 1024 * 1024),
        max_attachment_size=_coerce_int(values.get("MAX_ATTACHMENT_SIZE"), 5 * 1024 * 1024),
        max_total_size=_coerce_int(values.get("MAX_TOTAL_SIZE"), 10 * 1024 * 1024),
        max_attachments=_coerce_int(values.get("MAX_ATTACHMENTS"), 5),
        max_recipients=_coerce_int(values.get("MAX_RECIPIENTS"), 50),
        allowed_extensions=_coerce_list(values.get("ALLOWED_EXTENSIONS")),
        allowed_domains=_coerce_list(values.get("ALLOWED_DOMAINS")),
        allowed_recipients=_coerce_list(values.get("ALLOWED_RECIPIENTS")),
        dry_run=_coerce_bool(values.get("DRY_RUN"), False),
        log_level=values.get("LOG_LEVEL", "INFO").strip().upper() or "INFO",
        environment=environment,
        template_dir=values.get("TEMPLATE_DIR", "templates").strip() or "templates",
        retries=_coerce_int(values.get("SMTP_RETRIES"), 2),
        retry_backoff_seconds=float(values.get("SMTP_RETRY_BACKOFF_SECONDS", "1.0")) if values.get("SMTP_RETRY_BACKOFF_SECONDS") else 1.0,
        require_tls=_coerce_bool(values.get("REQUIRE_TLS"), False),
        privacy_mode=_coerce_bool(values.get("PRIVACY_MODE"), False),
        upload_dir=values.get("UPLOAD_DIR", "uploads").strip() or "uploads",
    )
    should_validate = require_credentials or bool(values.get("SMTP_HOST")) or bool(values.get("SMTP_USER")) or bool(values.get("SMTP_PASSWORD"))
    if should_validate:
        config.validate(require_credentials=require_credentials)
    return config

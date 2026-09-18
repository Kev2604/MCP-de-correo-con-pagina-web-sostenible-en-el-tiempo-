from __future__ import annotations

import mimetypes
import os
import uuid
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from config import EmailServerConfig, load_config
from exceptions import EmailSendError, EmailSizeLimitError, EmailValidationError, SMTPAuthenticationError, SMTPConfigurationError
from models import EmailRequest, EmailResult
from smtp_client import SMTPClient
from validators import validate_attachment_metadata, validate_headers, validate_recipients


class EmailService:
    def __init__(self, config: EmailServerConfig | None = None) -> None:
        self.config = config or load_config(require_credentials=False)
        self.smtp_client = SMTPClient(self.config)

    def _sanitize_header_value(self, value: str) -> str:
        return value.replace("\r", "").replace("\n", "")

    def _build_message(self, request: EmailRequest) -> EmailMessage:
        recipients = request.to + request.cc + request.bcc
        if len(recipients) > self.config.max_recipients:
            raise EmailSizeLimitError("Se excede el número máximo de destinatarios.", "EMAIL_SIZE_LIMIT_ERROR")
        if len(request.attachments) > self.config.max_attachments:
            raise EmailSizeLimitError("Se excede el número máximo de adjuntos.", "EMAIL_SIZE_LIMIT_ERROR")
        if request.body and len(request.body.encode("utf-8")) > self.config.max_body_size:
            raise EmailSizeLimitError("El cuerpo del correo excede el tamaño máximo configurado.", "EMAIL_SIZE_LIMIT_ERROR")
        if request.html and len(request.html.encode("utf-8")) > self.config.max_html_size:
            raise EmailSizeLimitError("El HTML del correo excede el tamaño máximo configurado.", "EMAIL_SIZE_LIMIT_ERROR")
        total_size = len(request.body.encode("utf-8")) + len((request.html or "").encode("utf-8"))
        if total_size > self.config.max_total_size:
            raise EmailSizeLimitError("El correo excede el tamaño total permitido.", "EMAIL_SIZE_LIMIT_ERROR")

        message = EmailMessage()
        message["From"] = self._build_sender(request.sender_name)
        if request.reply_to:
            message["Reply-To"] = self._sanitize_header_value(request.reply_to)
        message["To"] = ", ".join(request.to)
        if request.cc:
            message["Cc"] = ", ".join(request.cc)
        if request.bcc:
            message["Bcc"] = ", ".join(request.bcc)
        message["Subject"] = self._sanitize_header_value(request.subject or "Sin asunto")
        message.set_content(request.body or "")
        if request.html:
            message.add_alternative(request.html, subtype="html")
        for header_name, header_value in validate_headers(request.headers).items():
            if header_name.lower() == "x-priority":
                allowed_priorities = {"1", "2", "3", "4", "5"}
                if header_value not in allowed_priorities:
                    raise EmailValidationError("X-Priority debe ser un valor entre 1 y 5.", "VALIDATION_ERROR")
            message[header_name] = self._sanitize_header_value(header_value)
        if request.priority:
            priority_value = request.priority.lower()
            if priority_value not in {"low", "normal", "high"}:
                raise EmailValidationError("priority debe ser low, normal o high.", "VALIDATION_ERROR")
            message["X-Priority"] = {"low": "3", "normal": "3", "high": "1"}[priority_value]
        for attachment in request.attachments:
            metadata = validate_attachment_metadata(
                attachment,
                size_bytes=os.path.getsize(attachment),
                allowed_extensions=self.config.allowed_extensions,
                max_size_bytes=self.config.max_attachment_size,
                allowed_base_dir=self.config.upload_dir,
            )
            path = Path(metadata["path"])
            mime_type, _ = mimetypes.guess_type(str(path))
            if mime_type is None:
                mime_type = "application/octet-stream"
            maintype, subtype = mime_type.split("/", 1)
            with path.open("rb") as handle:
                message.add_attachment(handle.read(), maintype=maintype, subtype=subtype, filename=path.name)
            total_size += len(path.read_bytes())
        if total_size > self.config.max_total_size:
            raise EmailSizeLimitError("El correo excede el tamaño total permitido.", "EMAIL_SIZE_LIMIT_ERROR")
        return message

    def _build_sender(self, sender_name: str | None) -> str:
        if sender_name:
            safe_name = self._sanitize_header_value(sender_name)
            if "<" in safe_name or ">" in safe_name or "\n" in safe_name or "\r" in safe_name:
                raise EmailValidationError("El nombre del remitente no es válido.", "VALIDATION_ERROR")
            return f"{safe_name} <{self.config.smtp_from or self.config.smtp_user}>"
        return self.config.smtp_from or self.config.smtp_user

    def _validate_allowed_domains(self, recipients: list[str]) -> None:
        if not self.config.allowed_domains:
            return
        for address in recipients:
            domain = address.split("@", 1)[-1].lower()
            if domain not in self.config.allowed_domains:
                raise EmailValidationError(f"El dominio no está autorizado: {domain}", "VALIDATION_ERROR")

    def _validate_allowed_recipients(self, recipients: list[str]) -> None:
        if not self.config.allowed_recipients:
            return
        for address in recipients:
            if address not in self.config.allowed_recipients:
                raise EmailValidationError(f"El destinatario no está autorizado: {address}", "VALIDATION_ERROR")

    def send_email(self, request: EmailRequest) -> EmailResult:
        request_id = request.request_id or str(uuid.uuid4())
        normalized_to = validate_recipients(request.to)
        normalized_cc = validate_recipients(request.cc) if request.cc else []
        normalized_bcc = validate_recipients(request.bcc) if request.bcc else []
        recipients = normalized_to + normalized_cc + normalized_bcc
        self._validate_allowed_domains(recipients)
        self._validate_allowed_recipients(recipients)
        request.to = normalized_to
        request.cc = normalized_cc
        request.bcc = normalized_bcc
        message = self._build_message(request)
        if request.dry_run or self.config.dry_run:
            return EmailResult(
                success=True,
                message="Correo validado en modo simulación",
                request_id=request_id,
                recipients_count=len(recipients),
                attachments_count=len(request.attachments),
                dry_run=True,
                preview={"subject": request.subject or "Sin asunto", "to": request.to, "cc": request.cc, "bcc": request.bcc, "has_html": bool(request.html)},
            )
        try:
            self.smtp_client.send_message(message)
        except (SMTPAuthenticationError, SMTPConfigurationError, EmailSendError) as exc:
            raise exc
        except Exception as exc:  # pragma: no cover - defensive guard
            raise EmailSendError(f"Error inesperado durante el envío: {exc}", "EMAIL_SEND_ERROR") from exc
        return EmailResult(
            success=True,
            message="Correo enviado correctamente",
            request_id=request_id,
            recipients_count=len(recipients),
            attachments_count=len(request.attachments),
            dry_run=False,
        )

    def preview_email(self, request: EmailRequest) -> dict[str, Any]:
        request_id = request.request_id or str(uuid.uuid4())
        _ = self._build_message(request)
        preview = {
            "request_id": request_id,
            "subject": request.subject or "Sin asunto",
            "to": request.to,
            "cc": request.cc,
            "bcc": request.bcc,
            "has_html": bool(request.html),
            "attachments": [Path(attachment).name for attachment in request.attachments],
            "privacy_mode": self.config.privacy_mode,
        }
        if self.config.privacy_mode:
            preview["body"] = "[contenido oculto por privacidad]"
        else:
            preview["body"] = request.body or ""
        return preview

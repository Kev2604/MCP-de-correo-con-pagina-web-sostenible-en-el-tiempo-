from __future__ import annotations

import os
from typing import Any, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from config import load_config
from email_service import EmailService
from exceptions import EmailSendError, EmailValidationError, SMTPAuthenticationError, SMTPConfigurationError, SMTPConnectionError
from logging_config import configure_logging
from models import EmailRequest

load_dotenv()
logger = configure_logging(os.getenv("LOG_LEVEL", "INFO"))

mcp = FastMCP("Correo-MCP")
config = load_config(require_credentials=False)
service = EmailService(config)


def enviar_correo_impl(destinatario: str, asunto: str, cuerpo: str, html: Optional[str] = None, adjuntos: Optional[list[str]] = None, *, request_id: Optional[str] = None) -> str:
    try:
        request = EmailRequest(
            to=[destinatario] if destinatario else [],
            subject=asunto or "",
            body=cuerpo or "",
            html=html,
            attachments=adjuntos or [],
            request_id=request_id,
            dry_run=False,
        )
        result = service.send_email(request)
        return result.message
    except (EmailValidationError, SMTPConfigurationError, SMTPConnectionError, SMTPAuthenticationError, EmailSendError) as exc:
        return str(exc)


def _safe_response(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in {"smtp_password", "password", "token", "secret"}}


def _build_error_response(error: Exception, request_id: str | None = None) -> dict[str, Any]:
    error_code = getattr(error, "error_code", "UNKNOWN_ERROR")
    return {
        "success": False,
        "message": str(error),
        "request_id": request_id or "",
        "recipients_count": 0,
        "attachments_count": 0,
        "dry_run": False,
        "error_code": error_code,
    }


@mcp.tool()
def enviar_correo(
    destinatario: str | None = None,
    asunto: str | None = None,
    cuerpo: str | None = None,
    html: Optional[str] = None,
    adjuntos: Optional[list[str]] = None,
    to: Optional[list[str] | str] = None,
    cc: Optional[list[str] | str] = None,
    bcc: Optional[list[str] | str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    attachments: Optional[list[str]] = None,
    reply_to: Optional[str] = None,
    sender_name: Optional[str] = None,
    priority: Optional[str] = None,
    headers: Optional[dict[str, str]] = None,
    request_id: Optional[str] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    tool_request_id = request_id or ""
    try:
        recipients = []
        if destinatario:
            recipients.append(destinatario)
        if to:
            recipients.extend(to if isinstance(to, list) else [to])
        request = EmailRequest(
            to=recipients,
            cc=cc if isinstance(cc, list) else ([cc] if isinstance(cc, str) and cc else []),
            bcc=bcc if isinstance(bcc, list) else ([bcc] if isinstance(bcc, str) and bcc else []),
            subject=subject or asunto or "",
            body=body or cuerpo or "",
            html=html,
            attachments=attachments or adjuntos or [],
            reply_to=reply_to,
            sender_name=sender_name,
            priority=priority or "normal",
            headers=headers or {},
            request_id=tool_request_id,
            dry_run=dry_run,
        )
        result = service.send_email(request)
        response = {
            "success": result.success,
            "message": result.message,
            "request_id": result.request_id,
            "recipients_count": result.recipients_count,
            "attachments_count": result.attachments_count,
            "dry_run": result.dry_run,
            "error_code": result.error_code,
        }
        if result.preview:
            response["preview"] = result.preview
        logger.info("tool=enviar_correo success", extra={"tool_name": "enviar_correo", "request_id": tool_request_id, "result": "success", "recipients_count": result.recipients_count, "attachments_count": result.attachments_count})
        return _safe_response(response)
    except EmailValidationError as exc:
        logger.warning("tool=enviar_correo validation_error", extra={"tool_name": "enviar_correo", "request_id": tool_request_id, "error_code": exc.error_code})
        return _safe_response(_build_error_response(exc, tool_request_id))
    except (SMTPConfigurationError, SMTPConnectionError, SMTPAuthenticationError, EmailSendError) as exc:
        logger.error("tool=enviar_correo failure", extra={"tool_name": "enviar_correo", "request_id": tool_request_id, "error_code": getattr(exc, "error_code", "UNKNOWN_ERROR")})
        return _safe_response(_build_error_response(exc, tool_request_id))


@mcp.tool()
def validar_configuracion_smtp() -> dict[str, Any]:
    try:
        config.validate(require_credentials=True)
        return _safe_response({"success": True, "message": "Configuración SMTP válida", "smtp_host": config.smtp_host, "smtp_port": config.smtp_port, "smtp_tls": config.smtp_tls, "smtp_ssl": config.smtp_ssl, "environment": config.environment})
    except SMTPConfigurationError as exc:
        return _safe_response({"success": False, "message": str(exc), "error_code": exc.error_code})


@mcp.tool()
def probar_conexion_smtp() -> dict[str, Any]:
    try:
        result = service.smtp_client.test_connection()
        return _safe_response({"success": True, "message": result["message"], "smtp_host": config.smtp_host, "smtp_port": config.smtp_port, "tls": result.get("tls"), "ssl": result.get("ssl")})
    except (SMTPConfigurationError, SMTPConnectionError) as exc:
        return _safe_response({"success": False, "message": str(exc), "error_code": getattr(exc, "error_code", "SMTP_CONNECTION_ERROR")})


@mcp.tool()
def previsualizar_correo(
    destinatario: str | None = None,
    asunto: str | None = None,
    cuerpo: str | None = None,
    html: Optional[str] = None,
    adjuntos: Optional[list[str]] = None,
    to: Optional[list[str] | str] = None,
    cc: Optional[list[str] | str] = None,
    bcc: Optional[list[str] | str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    attachments: Optional[list[str]] = None,
    reply_to: Optional[str] = None,
    sender_name: Optional[str] = None,
    priority: Optional[str] = None,
    headers: Optional[dict[str, str]] = None,
    request_id: Optional[str] = None,
) -> dict[str, Any]:
    try:
        recipients = []
        if destinatario:
            recipients.append(destinatario)
        if to:
            recipients.extend(to if isinstance(to, list) else [to])
        request = EmailRequest(
            to=recipients,
            cc=cc if isinstance(cc, list) else ([cc] if isinstance(cc, str) and cc else []),
            bcc=bcc if isinstance(bcc, list) else ([bcc] if isinstance(bcc, str) and bcc else []),
            subject=subject or asunto or "",
            body=body or cuerpo or "",
            html=html,
            attachments=attachments or adjuntos or [],
            reply_to=reply_to,
            sender_name=sender_name,
            priority=priority or "normal",
            headers=headers or {},
            request_id=request_id,
            dry_run=True,
        )
        preview = service.preview_email(request)
        return _safe_response(preview)
    except EmailValidationError as exc:
        return _safe_response({"success": False, "message": str(exc), "error_code": exc.error_code})


@mcp.tool()
def listar_proveedores_smtp() -> dict[str, Any]:
    return {
        "success": True,
        "providers": {
            "gmail": {"host": "smtp.gmail.com", "port": 587, "tls": True, "ssl": False, "notes": "Usa una contraseña de aplicación"},
            "outlook": {"host": "smtp.office365.com", "port": 587, "tls": True, "ssl": False, "notes": "Microsoft 365"},
            "yahoo": {"host": "smtp.mail.yahoo.com", "port": 587, "tls": True, "ssl": False, "notes": "Requiere credenciales de aplicación"},
            "ses": {"host": "email-smtp.<region>.amazonaws.com", "port": 587, "tls": True, "ssl": False, "notes": "AWS SES"},
            "mailgun": {"host": "smtp.mailgun.org", "port": 587, "tls": True, "ssl": False, "notes": "Mailgun SMTP"},
            "sendgrid": {"host": "smtp.sendgrid.net", "port": 587, "tls": True, "ssl": False, "notes": "SendGrid SMTP"},
        },
    }


if __name__ == "__main__":
    mcp.run()
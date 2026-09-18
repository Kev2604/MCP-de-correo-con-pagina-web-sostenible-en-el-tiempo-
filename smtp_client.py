from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from typing import Any

from config import EmailServerConfig
from exceptions import SMTPAuthenticationError, SMTPConnectionError, SMTPConfigurationError, EmailSendError


class SMTPClient:
    def __init__(self, config: EmailServerConfig) -> None:
        self.config = config

    def build_connection(self) -> smtplib.SMTP:
        if not self.config.smtp_host:
            raise SMTPConfigurationError("SMTP_HOST es obligatorio.", "SMTP_CONFIGURATION_ERROR")
        if self.config.smtp_ssl:
            return smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port, timeout=self.config.smtp_timeout)
        if self.config.smtp_tls:
            client = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=self.config.smtp_timeout)
            client.starttls(context=ssl.create_default_context())
            return client
        if self.config.require_tls:
            raise SMTPConfigurationError("TLS es requerido pero no se pudo negociar.", "SMTP_CONFIGURATION_ERROR")
        return smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=self.config.smtp_timeout)

    def connect(self) -> smtplib.SMTP:
        try:
            client = self.build_connection()
        except (smtplib.SMTPException, OSError) as exc:
            raise SMTPConnectionError(f"No se pudo conectar al servidor SMTP: {exc}", "SMTP_CONNECTION_ERROR") from exc
        try:
            client.login(self.config.smtp_user, self.config.smtp_password)
        except smtplib.SMTPAuthenticationError as exc:
            client.quit()
            raise SMTPAuthenticationError("Autenticación SMTP fallida.", "SMTP_AUTHENTICATION_ERROR") from exc
        except smtplib.SMTPException as exc:
            client.quit()
            raise SMTPConnectionError(f"Error SMTP durante la autenticación: {exc}", "SMTP_CONNECTION_ERROR") from exc
        return client

    def send_message(self, message: EmailMessage) -> None:
        client = self.connect()
        try:
            client.send_message(message)
        except smtplib.SMTPException as exc:
            raise EmailSendError(f"No se pudo enviar el correo: {exc}", "EMAIL_SEND_ERROR") from exc
        finally:
            client.quit()

    def test_connection(self) -> dict[str, Any]:
        client = self.build_connection()
        try:
            client.quit()
            return {"success": True, "message": "Conexión SMTP preparada", "tls": self.config.smtp_tls, "ssl": self.config.smtp_ssl}
        except smtplib.SMTPException as exc:
            raise SMTPConnectionError(f"Error SMTP al probar la conexión: {exc}", "SMTP_CONNECTION_ERROR") from exc
        finally:
            try:
                client.quit()
            except (AttributeError, OSError, smtplib.SMTPException):
                pass

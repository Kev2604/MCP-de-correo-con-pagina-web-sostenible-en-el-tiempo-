import pytest

from config import load_config
from email_service import EmailService
from exceptions import EmailValidationError
from models import EmailRequest


def build_email_service() -> EmailService:
    config = load_config(
        env={
            "SMTP_HOST": "smtp.example.com",
            "SMTP_USER": "user@example.com",
            "SMTP_PASSWORD": "secret",
            "SMTP_PORT": "587",
            "SMTP_TLS": "true",
            "SMTP_SSL": "false",
            "MAX_ATTACHMENT_SIZE": "1000",
            "MAX_TOTAL_SIZE": "5000",
            "MAX_BODY_SIZE": "1000",
            "MAX_HTML_SIZE": "1000",
            "MAX_ATTACHMENTS": "2",
            "MAX_RECIPIENTS": "5",
        },
        require_credentials=True,
    )
    return EmailService(config)


def test_dry_run_returns_preview():
    service = build_email_service()
    result = service.send_email(EmailRequest(to=["destino@example.com"], subject="Asunto", body="Hola", dry_run=True))
    assert result.success is True
    assert result.dry_run is True


def test_rejects_invalid_recipient():
    service = build_email_service()
    with pytest.raises(EmailValidationError):
        service.send_email(EmailRequest(to=["correo-invalido"], subject="Asunto", body="Hola"))


def test_rejects_attachment_path_traversal(tmp_path):
    service = build_email_service()
    target = tmp_path / ".." / "evil.txt"
    target.write_text("hola")
    with pytest.raises(EmailValidationError):
        service.send_email(EmailRequest(to=["destino@example.com"], subject="Asunto", body="Hola", attachments=[str(target)]))

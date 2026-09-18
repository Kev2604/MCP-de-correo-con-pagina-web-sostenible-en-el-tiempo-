import os

import pytest

from config import SMTPConfigurationError, load_config
from validators import validate_attachment_input, validate_headers, validate_recipients


def test_load_config_uses_safe_defaults(monkeypatch):
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    config = load_config(env={})
    assert config.smtp_port == 587
    assert config.smtp_tls is True
    assert config.max_recipients == 50


def test_validate_config_requires_credentials(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.delenv("SMTP_PASSWORD", raising=False)
    with pytest.raises(SMTPConfigurationError):
        load_config(env=os.environ).validate(require_credentials=True)


def test_rejects_invalid_recipients():
    with pytest.raises(ValueError):
        validate_recipients(["correo-invalido"])


def test_rejects_newline_in_headers():
    with pytest.raises(ValueError):
        validate_headers({"X-Test": "hola\nB"})


def test_rejects_path_traversal(tmp_path):
    target = tmp_path / ".." / "secret.txt"
    with pytest.raises(ValueError):
        validate_attachment_input(str(target), allowed_base_dir=tmp_path)

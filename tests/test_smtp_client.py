from config import load_config
from smtp_client import SMTPClient


def test_client_uses_config():
    config = load_config(env={"SMTP_HOST": "smtp.example.com", "SMTP_USER": "user@example.com", "SMTP_PASSWORD": "secret", "SMTP_PORT": "587", "SMTP_TLS": "true", "SMTP_SSL": "false"}, require_credentials=True)
    client = SMTPClient(config)
    assert client.config.smtp_host == "smtp.example.com"

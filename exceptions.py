from __future__ import annotations


class EmailError(Exception):
    """Base exception for the email service."""

    def __init__(self, message: str, error_code: str = "EMAIL_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class EmailValidationError(ValueError, EmailError):
    """Raised when the request content is invalid."""

    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class SMTPConfigurationError(EmailError, ValueError):
    """Raised when the SMTP configuration is incomplete or invalid."""

    def __init__(self, message: str, error_code: str = "SMTP_CONFIGURATION_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class SMTPConnectionError(EmailError):
    """Raised when the SMTP server cannot be reached."""

    def __init__(self, message: str, error_code: str = "SMTP_CONNECTION_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class SMTPAuthenticationError(EmailError):
    """Raised when SMTP authentication fails."""

    def __init__(self, message: str, error_code: str = "SMTP_AUTHENTICATION_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class AttachmentValidationError(EmailValidationError):
    """Raised when an attachment is invalid."""

    def __init__(self, message: str, error_code: str = "ATTACHMENT_VALIDATION_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class EmailSizeLimitError(EmailValidationError):
    """Raised when the email exceeds configured limits."""

    def __init__(self, message: str, error_code: str = "EMAIL_SIZE_LIMIT_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class EmailSendError(EmailError):
    """Raised when the SMTP server rejects the send operation."""

    def __init__(self, message: str, error_code: str = "EMAIL_SEND_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code

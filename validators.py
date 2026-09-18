from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

from exceptions import AttachmentValidationError, EmailValidationError

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
HEADER_RE = re.compile(r"^[A-Za-z0-9-]+$")
COMMON_PASSWORDS = {"123456", "password", "admin", "admin123", "qwerty", "letmein", "welcome"}


def assess_password_strength(password: str) -> dict[str, object]:
    """Return a deterministic strength report without exposing the password."""
    feedback: list[str] = []
    normalized = password.strip().lower()
    score = 0

    if len(password) >= 12:
        score += 1
    else:
        feedback.append("Usa al menos 12 caracteres.")
    if not re.search(r"[a-z]", password):
        feedback.append("Incluye letras minúsculas.")
    else:
        score += 1
    if not re.search(r"[A-Z]", password):
        feedback.append("Incluye letras mayúsculas.")
    else:
        score += 1
    if not re.search(r"\d", password):
        feedback.append("Incluye al menos un número.")
    else:
        score += 1
    if not re.search(r"[^A-Za-z0-9\s]", password):
        feedback.append("Incluye un símbolo especial.")
    else:
        score += 1

    if normalized in COMMON_PASSWORDS or len(set(password)) <= 3:
        score = 0
        feedback.append("No uses una contraseña común o con pocos caracteres distintos.")
    elif len(password) < 8:
        score = min(score, 2)
    elif len(password) < 12:
        score = min(score, 3)

    levels = ("Muy débil", "Débil", "Media", "Fuerte", "Muy fuerte", "Muy fuerte")
    return {"score": score, "max_score": 5, "level": levels[score], "feedback": feedback}


def validate_password_strength(password: str, minimum_score: int = 4) -> dict[str, object]:
    report = assess_password_strength(password)
    if report["score"] < minimum_score or report["feedback"]:
        details = " ".join(report["feedback"]) or "Elige una contraseña más difícil de adivinar."
        raise ValueError(f"Contraseña {report['level'].lower()}. {details}")
    return report


def _normalize_recipients(raw: str | Iterable[str] | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [item.strip() for item in raw.split(",") if item.strip()]
    else:
        items = [item.strip() for item in raw if str(item).strip()]
    return items


def validate_recipients(recipients: str | Iterable[str] | None) -> list[str]:
    normalized = _normalize_recipients(recipients)
    if not normalized:
        raise EmailValidationError("Se requiere al menos un destinatario válido.", "VALIDATION_ERROR")
    invalid = [address for address in normalized if not EMAIL_RE.match(address)]
    if invalid:
        raise EmailValidationError(f"Destinatarios inválidos: {', '.join(invalid)}", "VALIDATION_ERROR")
    return normalized


def validate_headers(headers: dict[str, str] | None) -> dict[str, str]:
    if not headers:
        return {}
    cleaned: dict[str, str] = {}
    for key, value in headers.items():
        if not HEADER_RE.match(key):
            raise EmailValidationError(f"Encabezado inválido: {key}", "VALIDATION_ERROR")
        if "\n" in value or "\r" in value:
            raise EmailValidationError(f"Valor de encabezado inválido: {key}", "VALIDATION_ERROR")
        cleaned[key] = value
    return cleaned


def validate_attachment_input(path: str, allowed_base_dir: str | os.PathLike[str] | None = None) -> str:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if not candidate.exists() or not candidate.is_file():
        raise AttachmentValidationError("La ruta del adjunto no existe o no es un archivo.", "ATTACHMENT_VALIDATION_ERROR")
    if allowed_base_dir is not None:
        allowed = Path(allowed_base_dir).expanduser().resolve()
        candidate_resolved = candidate.resolve()
        if allowed not in candidate_resolved.parents and candidate_resolved != allowed:
            raise AttachmentValidationError("La ruta del adjunto está fuera del directorio autorizado.", "ATTACHMENT_VALIDATION_ERROR")
    if ".." in Path(path).parts:
        raise AttachmentValidationError("Ruta de adjunto con traversal no permitida.", "ATTACHMENT_VALIDATION_ERROR")
    return str(candidate)


def validate_attachment_metadata(path: str, size_bytes: int, allowed_extensions: Iterable[str], max_size_bytes: int, allowed_base_dir: str | os.PathLike[str] | None = None) -> dict[str, object]:
    resolved_path = validate_attachment_input(path, allowed_base_dir=allowed_base_dir)
    extension = Path(resolved_path).suffix.lower().lstrip(".")
    allowed = {ext.lower().lstrip(".") for ext in allowed_extensions}
    if allowed and extension not in allowed:
        raise AttachmentValidationError(f"Extensión no permitida: {extension}", "ATTACHMENT_VALIDATION_ERROR")
    if size_bytes <= 0:
        raise AttachmentValidationError("El adjunto está vacío.", "ATTACHMENT_VALIDATION_ERROR")
    if size_bytes > max_size_bytes:
        raise AttachmentValidationError(f"El adjunto excede el tamaño máximo permitido de {max_size_bytes} bytes.", "ATTACHMENT_VALIDATION_ERROR")
    return {"path": resolved_path, "extension": extension, "size_bytes": size_bytes}

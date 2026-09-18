import base64
import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

from validators import validate_password_strength

DB_PATH = os.getenv("APP_DB_PATH", os.path.join(os.path.dirname(__file__), "app.db"))


def set_db_path(path: str) -> None:
    global DB_PATH
    DB_PATH = path


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"pbkdf2_sha256$100000${salt.hex()}${digest.hex()}"


def _encrypt_value(value: str) -> str:
    key = hashlib.sha256(os.getenv("APP_SECRET_KEY", "mcp-correo-local-secret").encode("utf-8")).digest()
    nonce = secrets.token_bytes(12)
    payload = value.encode("utf-8")
    encrypted = bytearray()
    for index, byte in enumerate(payload):
        encrypted.append(byte ^ key[index % len(key)] ^ nonce[index % len(nonce)])
    return base64.b64encode(nonce + bytes(encrypted)).decode("utf-8")


def _decrypt_value(value: str) -> str:
    key = hashlib.sha256(os.getenv("APP_SECRET_KEY", "mcp-correo-local-secret").encode("utf-8")).digest()
    decoded = base64.b64decode(value.encode("utf-8"))
    nonce = decoded[:12]
    payload = decoded[12:]
    result = bytearray()
    for index, byte in enumerate(payload):
        result.append(byte ^ key[index % len(key)] ^ nonce[index % len(nonce)])
    return result.decode("utf-8")


def _verify_password(password: str, stored_hash: str) -> bool:
    if not stored_hash:
        return False

    if stored_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt_hex, digest_hex = stored_hash.split("$")
            salt = bytes.fromhex(salt_hex)
            digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
            return secrets.compare_digest(digest.hex(), digest_hex)
        except (ValueError, TypeError):
            return False

    return password == stored_hash


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS app_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            user_name TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sent_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS smtp_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            smtp_host TEXT NOT NULL,
            smtp_user TEXT NOT NULL,
            smtp_password TEXT NOT NULL,
            smtp_port INTEGER NOT NULL,
            smtp_tls INTEGER NOT NULL,
            smtp_ssl INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    cur.execute("SELECT COUNT(*) FROM users WHERE username = ?", ("admin",))
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)",
            ("admin", _hash_password("admin123"), "admin", _now()),
        )

    conn.commit()
    conn.close()


def create_user(username: str, password: str, role: str = "user") -> bool:
    username = username.strip()
    password = password.strip()
    if not username or not password:
        return False
    try:
        validate_password_strength(password)
    except ValueError:
        return False

    if role not in {"admin", "user"}:
        role = "user"

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)",
            (username, _hash_password(password), role, _now()),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def update_user(user_id: int, username: str, role: str, password: Optional[str] = None) -> bool:
    username = username.strip()
    if not username:
        return False

    if role not in {"admin", "user"}:
        return False
    if password and password.strip():
        try:
            validate_password_strength(password.strip())
        except ValueError:
            return False

    conn = get_connection()
    cur = conn.cursor()
    try:
        if password and password.strip():
            cur.execute(
                "UPDATE users SET username = ?, role = ?, password = ? WHERE id = ?",
                (username, role, _hash_password(password.strip()), user_id),
            )
        else:
            cur.execute(
                "UPDATE users SET username = ?, role = ? WHERE id = ?",
                (username, role, user_id),
            )
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_user(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row is None:
            return False

        if row[0] == "admin":
            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if cur.fetchone()[0] <= 1:
                return False

        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def reset_password(username: str, new_password: str) -> bool:
    try:
        validate_password_strength(new_password)
    except ValueError:
        return False
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET password = ? WHERE username = ?", (_hash_password(new_password), username))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> Optional[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password, role FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    conn.close()

    if user is None:
        return None

    if not _verify_password(password, user[2]):
        return None

    if not user[2].startswith("pbkdf2_sha256$"):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password = ? WHERE username = ?", (_hash_password(password), user[1]))
        conn.commit()
        conn.close()

    return {"id": user[0], "username": user[1], "role": user[3]}


def create_session(username: str, role: str) -> str:
    session_id = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sessions (session_id, username, role, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, username, role, expires_at, _now()),
    )
    conn.commit()
    conn.close()
    return session_id


def get_session_user(session_id: Optional[str]) -> Optional[dict]:
    if not session_id:
        return None

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, role, expires_at FROM sessions WHERE session_id = ?", (session_id,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    expires_at = datetime.fromisoformat(row[2])
    if expires_at <= datetime.now(timezone.utc):
        delete_session(session_id)
        return None

    return {"username": row[0], "role": row[1]}


def delete_session(session_id: Optional[str]) -> None:
    if not session_id:
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def get_all_users() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, created_at FROM users ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": row[0], "username": row[1], "role": row[2], "created_at": row[3]}
        for row in rows
    ]

def save_smtp_settings(host: str, user: str, password: str, port: int = 587, tls: bool = True, ssl: bool = False) -> bool:
    host = host.strip()
    user = user.strip()
    password = password.strip()
    if not host or not user or not password:
        return False

    encrypted_password = _encrypt_value(password)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT id FROM smtp_settings WHERE id = 1"
        )
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO smtp_settings (id, smtp_host, smtp_user, smtp_password, smtp_port, smtp_tls, smtp_ssl, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (1, host, user, encrypted_password, port, int(tls), int(ssl), _now()),
            )
        else:
            cur.execute(
                "UPDATE smtp_settings SET smtp_host = ?, smtp_user = ?, smtp_password = ?, smtp_port = ?, smtp_tls = ?, smtp_ssl = ?, updated_at = ? WHERE id = 1",
                (host, user, encrypted_password, port, int(tls), int(ssl), _now()),
            )
        conn.commit()
        return True
    finally:
        conn.close()


def get_smtp_settings() -> dict:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT smtp_host, smtp_user, smtp_password, smtp_port, smtp_tls, smtp_ssl FROM smtp_settings WHERE id = 1"
    )
    row = cur.fetchone()
    conn.close()
    if row is None:
        return {"host": "", "user": "", "password": "", "port": 587, "tls": True, "ssl": False}

    return {
        "host": row[0],
        "user": row[1],
        "password": _decrypt_value(row[2]),
        "port": row[3],
        "tls": bool(row[4]),
        "ssl": bool(row[5]),
    }


def change_smtp_settings_with_permission(host: str, user: str, password: str, admin_username: str, admin_password: str, port: int = 587, tls: bool = True, ssl: bool = False) -> bool:
    admin_user = authenticate_user(admin_username, admin_password)
    if admin_user is None or admin_user.get("role") != "admin":
        return False
    return save_smtp_settings(host, user, password, port, tls, ssl)


def log_event(level: str, message: str, source: str, status: str, user_name: Optional[str] = None) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO app_logs (level, message, source, status, user_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (level, message, source, status, user_name, _now()),
    )
    conn.commit()
    conn.close()


def get_recent_logs(limit: int = 20) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, level, message, source, status, user_name, created_at FROM app_logs ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "level": row[1],
            "message": row[2],
            "source": row[3],
            "status": row[4],
            "user_name": row[5],
            "created_at": row[6],
        }
        for row in rows
    ]


def log_sent_email(sender: str, recipient: str, subject: str, body: str, status: str) -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO sent_emails (sender, recipient, subject, body, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (sender, recipient, subject, body, status, _now()),
    )
    conn.commit()
    conn.close()


def get_sent_emails(limit: int = 20) -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT sender, recipient, subject, body, status, created_at FROM sent_emails ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "sender": row[0],
            "recipient": row[1],
            "subject": row[2],
            "body": row[3],
            "status": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]

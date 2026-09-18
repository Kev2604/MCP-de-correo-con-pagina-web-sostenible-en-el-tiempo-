import os
import tempfile
import unittest

import database


class DatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = tempfile.NamedTemporaryFile(delete=False, suffix=".db").name
        database.set_db_path(self.db_path)
        database.init_db()

    def tearDown(self) -> None:
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_admin_user_is_created(self) -> None:
        user = database.authenticate_user("admin", "admin123")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "admin")

    def test_create_user_and_log_event(self) -> None:
        created = database.create_user("usuario", "Clave!Segura_47", "user")
        self.assertTrue(created)

        database.log_event("info", "Prueba de log", "tests", "ok", user_name="usuario")
        logs = database.get_recent_logs(limit=5)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["message"], "Prueba de log")

    def test_sent_email_history_is_recorded(self) -> None:
        database.log_sent_email("admin", "destino@example.com", "Asunto", "Cuerpo", "sent")
        history = database.get_sent_emails(limit=5)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["recipient"], "destino@example.com")

    def test_legacy_plaintext_password_is_accepted_and_migrated(self) -> None:
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, role, created_at) VALUES (?, ?, ?, ?)",
            ("legacy", "admin123", "user", database._now()),
        )
        conn.commit()
        conn.close()

        user = database.authenticate_user("legacy", "admin123")
        self.assertIsNotNone(user)

        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username = ?", ("legacy",))
        stored_hash = cur.fetchone()[0]
        conn.close()
        self.assertTrue(stored_hash.startswith("pbkdf2_sha256$"))

    def test_smtp_settings_are_encrypted_and_permission_is_checked(self) -> None:
        saved = database.save_smtp_settings(
            host="smtp.example.com",
            user="correo@example.com",
            password="supersecret",
            port=2525,
            tls=True,
            ssl=False,
        )
        self.assertTrue(saved)

        settings = database.get_smtp_settings()
        self.assertEqual(settings["host"], "smtp.example.com")
        self.assertEqual(settings["user"], "correo@example.com")
        self.assertEqual(settings["password"], "supersecret")
        self.assertEqual(settings["port"], 2525)
        self.assertTrue(settings["tls"])

        conn = database.get_connection()
        row = conn.execute("SELECT smtp_host, smtp_user, smtp_password FROM smtp_settings WHERE id = 1").fetchone()
        conn.close()
        self.assertNotIn("supersecret", "".join(row))

        denied = database.change_smtp_settings_with_permission(
            host="smtp2.example.com",
            user="otro@example.com",
            password="otraclave",
            admin_username="admin",
            admin_password="wrong-password",
        )
        self.assertFalse(denied)


if __name__ == "__main__":
    unittest.main()

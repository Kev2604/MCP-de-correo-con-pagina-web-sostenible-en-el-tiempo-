import unittest
from uuid import uuid4

from fastapi.testclient import TestClient

from interfaz_web import app


class InterfazWebTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_home_page_returns_html(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Acceso al sistema", response.text)

    def test_send_endpoint_returns_message(self) -> None:
        response = self.client.post(
            "/send",
            data={
                "destinatario": "prueba@example.com",
                "asunto": "Prueba",
                "cuerpo": "Hola desde la interfaz",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("mensaje", response.json())

    def test_registration_enforces_password_strength(self) -> None:
        weak = self.client.post(
            "/register",
            data={"username": f"weak_{uuid4().hex}", "password": "admin123", "role": "user"},
        )
        self.assertEqual(weak.status_code, 200)
        self.assertIn("Contraseña muy débil", weak.text)

        strong = self.client.post(
            "/register",
            data={"username": f"strong_{uuid4().hex}", "password": "Q7!a_secure_user#42", "role": "user"},
            follow_redirects=False,
        )
        self.assertEqual(strong.status_code, 303)


if __name__ == "__main__":
    unittest.main()

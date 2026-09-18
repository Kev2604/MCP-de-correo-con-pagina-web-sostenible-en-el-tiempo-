import os
import unittest

from dotenv import load_dotenv

from servidor_correo import enviar_correo


class TestEmailReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        load_dotenv()
        cls.to = os.getenv("TEST_TO", "destino@example.com")
        cls.subject = os.getenv("TEST_SUBJECT", "Prueba real desde test_email_real")
        cls.body = os.getenv("TEST_BODY", "Este es un correo de prueba enviado desde test_email_real.")
        cls.smtp_host = os.getenv("SMTP_HOST")
        cls.smtp_user = os.getenv("SMTP_USER")
        cls.smtp_password = os.getenv("SMTP_PASSWORD")

        if not all([cls.smtp_host, cls.smtp_user, cls.smtp_password]):
            raise unittest.SkipTest("SMTP credentials are not configured in .env")

    def test_email_real(self):
        result = enviar_correo(self.to, self.subject, self.body)
        self.assertIn("Correo enviado correctamente", result)


if __name__ == "__main__":
    unittest.main()

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from servidor_correo import enviar_correo


def main() -> int:
    parser = argparse.ArgumentParser(description="Prueba simple del servidor de correo")
    parser.add_argument("--to", default=os.getenv("TEST_TO", ""), help="Correo de destino")
    parser.add_argument("--subject", default="Prueba desde Docker", help="Asunto del correo")
    parser.add_argument("--body", default="Este es un correo de prueba enviado desde el contenedor.", help="Cuerpo del correo")
    parser.add_argument("--dry-run", action="store_true", help="Solo valida la configuración y el formato del correo")
    args = parser.parse_args()

    load_dotenv()

    if not args.to:
        print("No se indicó un destinatario. Usa --to o define TEST_TO en el entorno.")
        return 2

    if args.dry_run:
        print("Modo dry-run: se validará el correo sin enviarlo.")
        print(f"Destino: {args.to}")
        print(f"Asunto: {args.subject}")
        print(f"Cuerpo: {args.body}")
        return 0

    result = enviar_correo(
        destinatario=args.to,
        asunto=args.subject,
        cuerpo=args.body,
    )
    print(result)
    return 0 if "correctamente" in result.lower() or "inválido" not in result.lower() else 1


if __name__ == "__main__":
    sys.exit(main())

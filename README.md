# Servidor MCP de correos

Este proyecto expone un servidor MCP para enviar correos mediante SMTP y además incorpora una interfaz web local para gestionar envíos, usuarios, logs y adjuntos.

## Inicio rápido

Si querés usar la interfaz web, seguí la guía completa en [README_INTERFAZ.md](README_INTERFAZ.md).

## Uso con Docker

Construye la imagen:

```powershell
docker build -t mcp-correo:latest -f dockerfile.txt .
```

Ejecuta el contenedor en modo interactivo para un cliente MCP real:

```powershell
docker run --rm -i --env-file .env mcp-correo:latest
```

## Prueba rápida local

Para probar el envío sin depender de un cliente MCP:

```powershell
python test_email.py --to tu@correo.com --subject "Prueba" --body "Hola" --dry-run
```

Para enviar realmente el correo:

```powershell
python test_email.py --to tu@correo.com --subject "Prueba" --body "Hola"
```

Para ejecutar el test de envío real:

```powershell
python test_email_real.py
```

## Variables de entorno

Crea un archivo [.env](.env) con:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=tu_usuario@example.com
SMTP_PASSWORD=tu_contraseña
SMTP_TLS=true
TEST_TO=destino@ejemplo.com
```

## Conectar con VS Code o Claude Desktop

El archivo [Servidor_Mcp_Correos.json](Servidor_Mcp_Correos.json) está preparado para un cliente MCP que acepte un bloque `mcpServers`.

### Ejemplo para VS Code

Puedes usar el archivo [vscode-mcp.json](vscode-mcp.json) como referencia o copiar este bloque:

```json
{
  "servers": {
    "correo-mcp": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env-file",
        "C:/Users/KFsil/OneDrive/Desktop/mcp-correo/.env",
        "mcp-correo:latest"
      ],
      "cwd": "C:/Users/KFsil/OneDrive/Desktop/mcp-correo"
    }
  }
}
```

### Ejemplo para Claude Desktop

En la configuración de Claude Desktop, usa este bloque:

```json
{
  "mcpServers": {
    "correo-mcp": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env-file",
        "C:/Users/KFsil/OneDrive/Desktop/mcp-correo/.env",
        "mcp-correo:latest"
      ],
      "cwd": "C:/Users/KFsil/OneDrive/Desktop/mcp-correo"
    }
  }
}
```

## Notas

El servidor usa MCP sobre stdio, por lo que se debe ejecutar en modo interactivo con `-i`.

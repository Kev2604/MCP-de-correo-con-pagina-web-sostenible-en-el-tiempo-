# Guía paso a paso para implementar y ejecutar el proyecto

## 1. Preparar el entorno

1. Abre la carpeta del proyecto:
   - `c:\Users\KFsil\OneDrive\Desktop\mcp-correo`
2. Instala Python 3.12 o superior si aún no lo tienes.
3. Instala dependencias en el entorno de Python:

```powershell
pip install -r requirements.txt
```

## 2. Crear el archivo de variables de entorno

1. En la raíz del proyecto crea un archivo llamado `.env`.
2. Copia la configuración SMTP/Gmail siguiente y reemplaza los valores con tus datos reales:

```env
# Configuración POP/SMTP para Gmail
POP_HOST=pop.gmail.com
POP_PORT=995
POP_SSL=true

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=tu_usuario@example.com
SMTP_PASSWORD=tu_contraseña_de_aplicacion
SMTP_FROM="Tu aplicación <tu_usuario@example.com>"
SMTP_TLS=true
SMTP_SSL=false
TEST_TO=destino@example.com
```

3. Asegúrate de que `SMTP_PASSWORD` sea una contraseña de aplicación válida de Google.
4. Guarda el archivo.

## 3. Entender los archivos principales

- `servidor_correo.py`
  - Carga las variables de entorno.
  - Define la herramienta MCP `enviar_correo`.
  - Construye el mensaje `EmailMessage`.
  - Envía el correo usando `smtplib.SMTP_SSL` o `smtplib.SMTP` según la configuración.

- `test_email.py`
  - Es un script de prueba local.
  - Permite enviar un correo real o hacer una validación en `dry-run`.

- `test_email_real.py`
  - Es un test automatizado con `unittest`.
  - Envía un correo real mientras valida la configuración SMTP.

## 4. Ejecutar una prueba de envío simple

Para enviar un correo de prueba desde la terminal:

```powershell
python test_email.py --to destino@example.com --subject "Prueba" --body "Hola"
```

## 5. Ejecutar el test real automatizado

Para ejecutar el test real que envía el correo usando la configuración actual:

```powershell
python test_email_real.py
```

## 6. Ejecutar con Docker (opcional)

1. Construye la imagen Docker:

```powershell
docker build -t mcp-correo:latest -f dockerfile.txt .
```

2. Ejecuta el contenedor con el archivo `.env`:

```powershell
docker run --rm -i --env-file .env mcp-correo:latest
```

## 7. Notas importantes

- El correo real se envía desde `SMTP_USER` pero el encabezado `From` se muestra como `SMTP_FROM`.
- Si usas Gmail, necesitas habilitar una contraseña de aplicación y/o verificación en dos pasos.
- Si cambias de proveedor de correo, actualiza `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_TLS` y `SMTP_SSL` con los valores correspondientes.

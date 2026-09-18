# Interfaz web para el MCP de correos

Esta interfaz transforma el servidor de correos en una plataforma local más completa, con autenticación, panel de control, administración de usuarios, historial de envíos, registro de eventos y soporte para adjuntos.

## Qué incluye la interfaz

- Inicio de sesión y gestión de sesiones.
- Registro de usuarios y recuperación de contraseña.
- Roles de usuario y administrador.
- Dashboard para redactar correos y enviar mensajes.
- Subida de archivos adjuntos.
- Historial de correos enviados.
- Registro de eventos y logs de actividad.
- Panel de administración para crear, editar y eliminar usuarios.
- Pruebas automáticas con Playwright.

## Estructura principal

- [interfaz_web.py](interfaz_web.py): punto de entrada de la aplicación web.
- [database.py](database.py): base de datos SQLite con usuarios, sesiones, logs y historial.
- [servidor_correo.py](servidor_correo.py): lógica de envío de correo reutilizada por la interfaz.
- [templates/](templates/): plantillas HTML del login, dashboard y administración.
- [tests/](tests/): pruebas unitarias y de navegador.

## Requisitos

- Python 3.10 o superior.
- Windows, Linux o macOS.
- Acceso a un servidor SMTP configurado en el archivo [.env](.env) o variables de entorno.

## Instalación paso a paso

### 1. Entrar en la carpeta del proyecto

```powershell
cd C:\Users\KFsil\OneDrive\Desktop\mcp-correo
```

### 2. Crear un entorno virtual

```powershell
python -m venv .venv
```

### 3. Activar el entorno virtual

En PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 5. Instalar el navegador de Playwright (solo para pruebas de navegador)

```powershell
python -m playwright install chromium
```

## Configuración del correo

Crea un archivo [.env](.env) con las siguientes variables:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=tu_usuario@example.com
SMTP_PASSWORD=tu_contraseña
SMTP_TLS=true
TEST_TO=destino@ejemplo.com
```

Si no configurás SMTP real, la interfaz seguirá arrancando, pero los envíos podrán quedar limitados a pruebas o a mensajes simulados según la configuración del servidor.

## Ejecutar la interfaz

### Opción 1: ejecutar la app localmente

```powershell
python -m uvicorn interfaz_web:app --host 127.0.0.1 --port 8020
```

Luego abre en el navegador:

```text
http://127.0.0.1:8020/
```

### Credenciales por defecto

- Usuario: admin
- Contraseña: admin123

## Flujo de uso

1. Ingresá con el usuario administrador.
2. Accedé al dashboard.
3. Redactá el correo, agregá destinatario, asunto y cuerpo.
4. Adjuntá uno o varios archivos si lo necesitás.
5. Enviá el correo desde el formulario.
6. Revisá el historial y los logs desde el panel.
7. Desde la sección de administración podés crear o modificar usuarios.

## Pruebas automáticas

### Pruebas de base de datos

```powershell
python -m unittest tests.test_database
```

### Pruebas de navegador con Playwright

```powershell
python -m pytest -q tests/playwright/app.spec.js
```

## Notas importantes

- La aplicación guarda los datos en un archivo local llamado [app.db](app.db).
- Los archivos adjuntos se almacenan en la carpeta [uploads/](uploads/).
- Para entornos de producción, conviene reemplazar SQLite por PostgreSQL o MySQL.
- La interfaz está pensada para uso local o interno, no como servicio público expuesto directamente a internet.

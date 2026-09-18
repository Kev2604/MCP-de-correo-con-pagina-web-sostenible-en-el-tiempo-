import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

import database
import servidor_correo
from validators import validate_password_strength

app = FastAPI(title="Interfaz de correo")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

database.init_db()


def get_current_user(request: Request):
    session_id = request.cookies.get("session_id")
    return database.get_session_user(session_id)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = database.authenticate_user(username, password)
    if user is None:
        database.log_event("error", "Intento de login fallido", "auth", "fail", user_name=username)
        return templates.TemplateResponse(request=request, name="login.html", context={"error": "Credenciales inválidas"})

    session_id = database.create_session(user["username"], user["role"])
    database.log_event("info", "Login correcto", "auth", "ok", user_name=username)

    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="session_id", value=session_id, httponly=True, max_age=8 * 3600, samesite="lax")
    return response


@app.get("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    database.delete_session(session_id)
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_id")
    return response


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    sent_emails = database.get_sent_emails(1000)
    logs = database.get_recent_logs(100)
    successful = sum(email["status"] in {"sent", "success", "ok"} for email in sent_emails)
    failed = sum(email["status"] in {"failed", "error", "fail"} for email in sent_emails)
    pending = sum(email["status"] in {"pending", "queued"} for email in sent_emails)
    total = len(sent_emails)
    tools = [
        "enviar_correo",
        "validar_configuracion_smtp",
        "probar_conexion_smtp",
        "previsualizar_correo",
        "listar_proveedores_smtp",
    ]

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "sent_emails": sent_emails,
            "logs": logs,
            "metrics": {
                "sent": total,
                "successful": successful,
                "failed": failed,
                "pending": pending,
                "success_rate": round((successful / total) * 100, 1) if total else 0,
            },
            "mcp_tools": tools,
            "smtp_configured": bool(database.get_smtp_settings().get("host")),
            "is_admin": user["role"] == "admin",
        },
    )


@app.post("/api/mcp/test")
async def test_mcp(request: Request):
    user = get_current_user(request)
    if not user:
        return {"ok": False, "message": "Debes iniciar sesión"}

    database.log_event("info", "Prueba de disponibilidad MCP ejecutada", "mcp", "ok", user_name=user["username"])
    return {"ok": True, "message": "MCP Server disponible", "tools": 5, "resources": 0}


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request) -> HTMLResponse:
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="logs.html",
        context={"user": user, "logs": database.get_recent_logs(100)},
    )


@app.get("/smtp-settings", response_class=HTMLResponse)
async def smtp_settings_page(request: Request) -> HTMLResponse:
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="smtp_settings.html",
        context={
            "user": user,
            "smtp_settings": database.get_smtp_settings(),
            "success": request.query_params.get("success") == "1",
            "error": request.query_params.get("error"),
        },
    )


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="register.html", context={})


@app.post("/register")
async def register(request: Request, username: str = Form(...), password: str = Form(...), role: str = Form("user")):
    if not username or not password:
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "Completa ambos campos"})
    try:
        validate_password_strength(password)
    except ValueError as error:
        return templates.TemplateResponse(request=request, name="register.html", context={"error": str(error)})

    if not database.create_user(username, password, role):
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "El usuario ya existe"})

    database.log_event("info", f"Usuario creado: {username}", "auth", "ok", user_name=username)
    return RedirectResponse(url="/", status_code=303)


@app.get("/recover", response_class=HTMLResponse)
async def recover_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name="recover.html", context={})


@app.post("/recover")
async def recover(request: Request, username: str = Form(...), new_password: str = Form(...)):
    try:
        validate_password_strength(new_password)
    except ValueError as error:
        return templates.TemplateResponse(request=request, name="recover.html", context={"error": str(error)})
    if not database.reset_password(username, new_password):
        return templates.TemplateResponse(request=request, name="recover.html", context={"error": "No existe ese usuario"})

    database.log_event("info", f"Contraseña restablecida para {username}", "auth", "ok", user_name=username)
    return templates.TemplateResponse(request=request, name="recover.html", context={"success": "Contraseña restablecida correctamente"})


@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request) -> HTMLResponse:
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin_users.html",
        context={"user": user, "users": database.get_all_users()},
    )


@app.post("/admin/users")
async def create_admin_user(request: Request, username: str = Form(...), password: str = Form(...), role: str = Form("user")):
    user = get_current_user(request)
    if not user or user["role"] != "admin":
        return RedirectResponse(url="/dashboard", status_code=303)
    try:
        validate_password_strength(password)
    except ValueError as error:
        return templates.TemplateResponse(
            request=request,
            name="admin_users.html",
            context={"user": user, "users": database.get_all_users(), "error": str(error)},
        )

    if not database.create_user(username, password, role):
        return templates.TemplateResponse(
            request=request,
            name="admin_users.html",
            context={"user": user, "users": database.get_all_users(), "error": "El usuario ya existe"},
        )

    database.log_event("info", f"Usuario creado por admin: {username}", "auth", "ok", user_name=user["username"])
    return RedirectResponse(url="/admin/users", status_code=303)


@app.post("/admin/users/update")
async def update_user(request: Request, user_id: int = Form(...), username: str = Form(...), role: str = Form(...), password: str = Form(default="")):
    current_user = get_current_user(request)
    if not current_user or current_user["role"] != "admin":
        return RedirectResponse(url="/dashboard", status_code=303)

    database.update_user(user_id, username, role, password or None)
    return RedirectResponse(url="/admin/users", status_code=303)


@app.post("/admin/users/delete")
async def delete_user_route(request: Request, user_id: int = Form(...)):
    current_user = get_current_user(request)
    if not current_user or current_user["role"] != "admin":
        return RedirectResponse(url="/dashboard", status_code=303)

    database.delete_user(user_id)
    return RedirectResponse(url="/admin/users", status_code=303)


@app.post("/send")
async def send(
    request: Request,
    destinatario: str = Form(...),
    asunto: str = Form(...),
    cuerpo: str = Form(...),
    html: str | None = Form(default=None),
    files: List[UploadFile] = File(default=[]),
):
    user = get_current_user(request)
    if not user:
        return {"ok": False, "mensaje": "Debes iniciar sesión"}

    upload_dir = BASE_DIR / "uploads"
    upload_dir.mkdir(exist_ok=True)
    saved_files = []

    for file in files:
        if file.filename:
            destination = upload_dir / file.filename
            with destination.open("wb") as f:
                f.write(await file.read())
            saved_files.append(str(destination))

    mensaje = servidor_correo.enviar_correo_impl(destinatario, asunto, cuerpo, html=html, adjuntos=saved_files)
    database.log_event("info", mensaje, "email", "ok", user_name=user["username"])
    database.log_sent_email(user["username"], destinatario, asunto, cuerpo, "sent")
    return {"ok": True, "mensaje": mensaje}


@app.post("/smtp-settings")
async def smtp_settings(
    request: Request,
    smtp_host: str = Form(...),
    smtp_user: str = Form(...),
    smtp_password: str = Form(...),
    smtp_port: int = Form(587),
    tls: str = Form("on"),
    ssl: str = Form("off"),
    admin_username: str = Form(...),
    admin_password: str = Form(...),
):
    current_user = get_current_user(request)
    if not current_user or current_user["role"] != "admin":
        return RedirectResponse(url="/dashboard", status_code=303)

    result = database.change_smtp_settings_with_permission(
        host=smtp_host,
        user=smtp_user,
        password=smtp_password,
        admin_username=admin_username,
        admin_password=admin_password,
        port=smtp_port,
        tls=tls == "on",
        ssl=ssl == "on",
    )

    if not result:
        return RedirectResponse(url="/smtp-settings?error=permission", status_code=303)

    database.log_event("info", "Configuración SMTP actualizada", "smtp", "ok", user_name=current_user["username"])
    return RedirectResponse(url="/smtp-settings?success=1", status_code=303)


if __name__ == "__main__":
    import uvicorn

    app_host = os.getenv("APP_HOST", "127.0.0.1")
    app_port = int(os.getenv("APP_PORT", "8020"))
    uvicorn.run(app, host=app_host, port=app_port)

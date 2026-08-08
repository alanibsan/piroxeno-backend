import smtplib
from email.message import EmailMessage
from html import escape

import requests

from app.config import settings


def _invitation_content(email: str, temporary_password: str, role: str, client_slug: str | None):
    login_url = f"{settings.public_app_url.rstrip('/')}/es/login"
    client_label = client_slug or "Global"
    html_email = escape(email)
    html_client_label = escape(client_label)
    html_temporary_password = escape(temporary_password)
    html_role = escape(role)

    text = f"""Te han invitado a unirte a Piroxeno.

Pasos:
1. Entra a {login_url}
2. Inicia sesion con este correo: {email}
3. Usa esta contrasena temporal: {temporary_password}
4. Accede al espacio asignado: {client_label}

Rol: {role}
"""
    html = f"""
    <div style="margin:0;padding:0;background:#050711;font-family:Inter,Arial,sans-serif;color:#f8fafc">
      <div style="max-width:620px;margin:0 auto;padding:36px 18px">
        <div style="border:1px solid rgba(255,255,255,.12);background:#0b1020;padding:28px">
          <img src="{settings.public_app_url.rstrip('/')}/favicon.png" alt="Piroxeno" width="48" height="48" style="display:block;margin-bottom:22px" />
          <p style="margin:0 0 8px;color:#00cc99;font-size:12px;font-weight:700;letter-spacing:.16em;text-transform:uppercase">Invitacion</p>
          <h1 style="margin:0 0 12px;font-size:28px;line-height:1.15;color:#ffffff">Bienvenido a Piroxeno</h1>
          <p style="margin:0 0 24px;color:#cbd5e1;font-size:15px;line-height:1.7">
            Te han invitado a unirte al portal de Piroxeno para revisar conversaciones, dashboards y actividad de asistentes de IA.
          </p>
          <div style="background:#111827;border:1px solid rgba(255,255,255,.10);padding:18px;margin-bottom:24px">
            <p style="margin:0 0 8px;color:#94a3b8;font-size:13px">Correo</p>
            <p style="margin:0 0 16px;color:#ffffff;font-size:16px;font-weight:700">{html_email}</p>
            <p style="margin:0 0 8px;color:#94a3b8;font-size:13px">Contrasena temporal</p>
            <p style="margin:0;color:#ffffff;font-size:16px;font-weight:700">{html_temporary_password}</p>
          </div>
          <a href="{login_url}" style="display:inline-block;background:#00cc99;color:#020617;text-decoration:none;font-weight:800;padding:13px 18px">Entrar a Piroxeno</a>
          <div style="margin-top:26px;color:#94a3b8;font-size:14px;line-height:1.7">
            <p style="margin:0 0 8px;font-weight:700;color:#e2e8f0">Pasos basicos</p>
            <p style="margin:0">1. Abre el link. 2. Inicia sesion con tu correo y contrasena temporal. 3. Revisa el espacio asignado: <strong style="color:#ffffff">{html_client_label}</strong>.</p>
            <p style="margin:12px 0 0">Rol: <strong style="color:#ffffff">{html_role}</strong></p>
          </div>
        </div>
      </div>
    </div>
    """
    return {"login_url": login_url, "client_label": client_label, "text": text, "html": html}


def _send_with_resend(email: str, html: str):
    response = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {settings.resend_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": settings.resend_from_email,
            "to": email,
            "subject": "Te han invitado a Piroxeno",
            "html": html,
        },
        timeout=12,
    )
    response.raise_for_status()


def send_invitation_email(
    email: str,
    temporary_password: str,
    role: str,
    client_slug: str | None,
):
    content = _invitation_content(email, temporary_password, role, client_slug)

    if settings.resend_api_key:
        try:
            _send_with_resend(email, content["html"])
            return True
        except Exception as exc:
            print(f"[EMAIL WARNING] could not send invitation email with Resend: {exc}")

    if not settings.smtp_host:
        print("[EMAIL WARNING] Email provider is not configured; invitation email was skipped")
        return False

    message = EmailMessage()
    message["Subject"] = "Te han invitado a Piroxeno"
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = email
    message.set_content(content["text"])
    message.add_alternative(content["html"], subtype="html")

    try:
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=12) as smtp:
                if settings.smtp_username and settings.smtp_password:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12) as smtp:
                smtp.starttls()
                if settings.smtp_username and settings.smtp_password:
                    smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
        return True
    except Exception as exc:
        print(f"[EMAIL WARNING] could not send invitation email: {exc}")
        return False

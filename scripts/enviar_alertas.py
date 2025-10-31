#!/usr/bin/env python3
"""
Script para enviar alertas de nuevas licitaciones a los suscriptores.

Lee el archivo ``data/subscribers.json`` donde se definen las suscripciones
(correo y filtros), identifica licitaciones nuevas en el último run y
envía un email personalizado a cada suscriptor con las coincidencias.

Este script está pensado para ejecutarse en una GitHub Action después de
actualizar los datos con ``placsp_sync.py``. Requiere que se definan
las variables de entorno ``SMTP_HOST``, ``SMTP_USER`` y ``SMTP_PASS`` con
las credenciales de un servidor SMTP válido (por ejemplo, Gmail con
contraseña de aplicación).
"""

import json
import os
import smtplib
from email.mime.text import MIMEText
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SUBS_FILE = DATA_DIR / "subscribers.json"


def load_subscribers() -> list:
    if not SUBS_FILE.exists():
        return []
    with open(SUBS_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_tenders() -> list:
    # Leer el JSON de licitaciones activas (ya filtrado) para eficiencia
    active_file = DATA_DIR / "tenders-active.json"
    if not active_file.exists():
        return []
    with open(active_file, encoding="utf-8") as f:
        return json.load(f)


def filter_tenders(sub, tenders: list) -> list:
    """Filtra las licitaciones según los criterios de un suscriptor."""
    keywords = [k.strip().lower() for k in sub.get("keywords", []) if k.strip()]
    provs = [p.strip().lower() for p in sub.get("provincias", []) if p.strip()]
    tipos = [t.strip().lower() for t in sub.get("tipos", []) if t.strip()]
    min_importe = sub.get("importeMin") or 0

    results = []
    for lic in tenders:
        # Filtro por importe
        if min_importe:
            imp = lic.get("importe") or 0
            if imp < min_importe:
                continue
        # Filtro por provincias
        if provs:
            loc = (lic.get("provincia") or lic.get("ccaa") or "").lower()
            if not any(p in loc for p in provs):
                continue
        # Filtro por tipos
        if tipos:
            tipo = (lic.get("tipo") or "").lower()
            if not any(t in tipo for t in tipos):
                continue
        # Filtro por palabras clave
        if keywords:
            contenido = " ".join([
                lic.get("titulo") or "",
                lic.get("organo") or "",
                lic.get("cpv") or "",
            ]).lower()
            if not any(k in contenido for k in keywords):
                continue
        results.append(lic)
    return results


def send_email(to_addr: str, subject: str, body: str):
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    if not (host and user and password):
        print("SMTP no configurado. No se envían correos.")
        return
    msg = MIMEText(body, "html", "utf-8")
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_addr
    try:
        with smtplib.SMTP(host, 587) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        print(f"Enviado correo a {to_addr}")
    except Exception as e:
        print(f"Error enviando correo a {to_addr}: {e}")


def main():
    subscribers = load_subscribers()
    if not subscribers:
        print("No hay suscriptores")
        return
    tenders = load_tenders()
    if not tenders:
        print("No hay licitaciones cargadas")
        return
    for sub in subscribers:
        email = sub.get("email")
        if not email:
            continue
        matches = filter_tenders(sub, tenders)
        if not matches:
            continue
        # Construir cuerpo del email
        rows = []
        for lic in matches[:20]:  # limitar a 20 para correos manejables
            fila = f"<li><strong>{lic.get('titulo')}</strong> – {lic.get('organo')}<br/>" \
                   f"<em>Provincia:</em> {lic.get('provincia') or lic.get('ccaa')} | " \
                   f"<em>Límite:</em> {lic.get('fechaLimite') or '-'} | " \
                   f"<a href='{lic.get('enlace')}' target='_blank'>Ver</a></li>"
            rows.append(fila)
        body = """
        <p>Hola,</p>
        <p>A continuación encontrarás las licitaciones que coinciden con tus intereses:</p>
        <ul>
        {} 
        </ul>
        <p>Gracias por usar LicitApp.</p>
        <p><em>No respondas a este mensaje. Para cancelar tu suscripción envía un correo indicando tu email.</em></p>
        """.format("\n".join(rows))
        subject = "Nuevas licitaciones de tu interés – LicitApp"
        send_email(email, subject, body)


if __name__ == "__main__":
    main()

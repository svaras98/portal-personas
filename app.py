from flask import Flask, request, redirect, session, send_from_directory, send_file
import json
import os
from datetime import timedelta, datetime
from leer_datos_jason import generar_json
from db import guardar_estado

import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = "Empresacoldcontrolcontactocoldcontrol"

SERVER_START = datetime.utcnow()
app.permanent_session_lifetime = timedelta(days=30)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================
# GOOGLE SHEETS CONFIG
# =============================
SHEET_ID = "11omZV-J8sn_qZ7htmaF-9tgCGwh_fwcklGchlGOA0RI"
SHEET_NAME = "Hoja 1"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

if os.getenv("GOOGLE_CREDENTIALS"):
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    CREDS = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
else:
    CREDS = Credentials.from_service_account_file(
        os.path.join(BASE_DIR, "credenciales.json"),
        scopes=SCOPES
    )

client = gspread.authorize(CREDS)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# =============================
# VALIDAR SESIÓN
# =============================
@app.before_request
def validar_sesion():

    if "user" in session:

        recordar = session.get("recordar", False)
        login_time = session.get("login_time")

        if not recordar and login_time:
            login_time = datetime.fromisoformat(login_time)

            if login_time < SERVER_START:
                session.clear()
                return redirect("/")

# =============================
# CARGAR USUARIOS
# =============================
def cargar_usuarios():
    with open(os.path.join(BASE_DIR, "usuarios.json"), "r", encoding="utf-8") as f:
        return json.load(f)["usuarios"]

# =============================
# LOGIN (CON NEXT 🔥)
# =============================
@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        next_url = request.args.get("next")
        if next_url:
            session["next"] = next_url

    if "user" in session:
        next_url = session.pop("next", None)
        if next_url:
            return redirect(next_url)
        return redirect("/index.html")

    if request.method == "POST":

        user = request.form["usuario"].lower()
        password = request.form["password"]
        recordar = request.form.get("recordar")

        usuarios = cargar_usuarios()

        for u in usuarios:
            if u["usuario"] == user and u["password"] == password:

                session["user"] = user
                session["recordar"] = bool(recordar)
                session["login_time"] = datetime.utcnow().isoformat()
                session.permanent = bool(recordar)

                next_url = session.pop("next", None)

                if next_url:
                    return redirect(next_url)
                else:
                    return redirect("/index.html")

        return redirect("/?error=1")

    return send_from_directory(BASE_DIR, "login.html")

# =============================
# INDEX
# =============================
@app.route("/index.html")
def index():
    if "user" not in session:
        return redirect("/?next=/index.html")
    return send_from_directory(BASE_DIR, "index.html")

# =============================
# DETALLE
# =============================
@app.route("/detalle.html")
def detalle():
    if "user" not in session:
        return redirect("/?next=" + request.url)
    return send_from_directory(BASE_DIR, "detalle.html")

# =============================
# DATOS JSON
# =============================
@app.route("/datos.json")
def datos():

    if "user" not in session:
        return {"error": "no autorizado"}, 403

    generar_json()
    return send_file(os.path.join(BASE_DIR, "datos.json"))

# =============================
# CAMBIAR ESTADO
# =============================
@app.route("/desactivar/<rut>", methods=["POST"])
def desactivar(rut):

    if "user" not in session:
        return {"error": "no autorizado"}, 403

    try:
        data = request.get_json()
        nuevo_estado = data.get("estado", "INACTIVO")

        guardar_estado(rut, nuevo_estado)

        datos_sheet = sheet.get_all_records()

        for i, row in enumerate(datos_sheet, start=2):

            rut_sheet = str(row.get("CARNET", "")).strip()

            if rut_sheet == rut:
                sheet.update_cell(i, 15, nuevo_estado)
                break

        generar_json()

        return {"ok": True}

    except Exception as e:
        print("Error:", e)
        return {"ok": False}

# =============================
# LOGOUT
# =============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =============================
# AUTO PROCESO 🔥 (AÑADIDO)
# =============================
@app.route("/auto-proceso")
def auto_proceso():

    import subprocess
    import sys

    print("🚀 INICIANDO AUTOMATIZACIÓN COMPLETA")

    try:
        resultado = subprocess.run(
            [sys.executable, "automizar_todo.py"],
            capture_output=True,
            text=True
        )

        salida = f"""
        ===== STDOUT =====
        {resultado.stdout}

        ===== STDERR =====
        {resultado.stderr}
        """

        if resultado.returncode != 0:
            return f"<pre>❌ ERROR EN PIPELINE\n\n{salida}</pre>", 500

        return f"<pre>✅ PROCESO COMPLETADO\n\n{salida}</pre>"

    except Exception as e:
        print("❌ ERROR GRAVE:", e)
        return f"<pre>ERROR: {str(e)}</pre>", 500

# =============================
# RUN
# =============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

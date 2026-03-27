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

# ⏱️ TIEMPO DE INICIO DEL SERVIDOR (CLAVE)
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
# VALIDAR SESIÓN EN CADA REQUEST 🔥
# =============================
@app.before_request
def validar_sesion():

    if "user" in session:

        recordar = session.get("recordar", False)
        login_time = session.get("login_time")

        if not recordar and login_time:
            login_time = datetime.fromisoformat(login_time)

            # 🔥 SI EL SERVIDOR SE REINICIÓ → LOGOUT
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
# LOGIN
# =============================
@app.route("/", methods=["GET", "POST"])
def login():

    if "user" in session:
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

                # ⏱️ guardar momento de login
                session["login_time"] = datetime.utcnow().isoformat()

                session.permanent = bool(recordar)

                return redirect("/index.html")

        return redirect("/?error=1")

    return send_from_directory(BASE_DIR, "login.html")

# =============================
# INDEX
# =============================
@app.route("/index.html")
def index():
    if "user" not in session:
        return redirect("/")
    return send_from_directory(BASE_DIR, "index.html")

# =============================
# DETALLE
# =============================
@app.route("/detalle.html")
def detalle():
    if "user" not in session:
        return redirect("/")
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
# AUTO PROCESO (CRON) 🔥
# =============================
@app.route("/auto-proceso")
def auto_proceso():

    try:
        import subprocess
        import sys

        print("🚀 INICIANDO PROCESO AUTOMÁTICO")

        result = subprocess.run(
            [sys.executable, "verificar_cambios.py"],
            capture_output=True,
            text=True
        )

        print(result.stdout)
        print(result.stderr)

        print("✅ PROCESO TERMINADO")

        return "Proceso ejecutado OK"

    except Exception as e:
        print("❌ ERROR:", e)
        return "Error en proceso", 500

# =============================
# RUN
# =============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

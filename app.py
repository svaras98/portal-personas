from flask import Flask, request, redirect, session, send_from_directory, send_file
import json
import os
from datetime import timedelta
from leer_datos_jason import generar_json
from db import guardar_estado  # 🔥 NUEVO

# 🔥 GOOGLE SHEETS
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = "Empresacoldcontrolcontactocoldcontrol"

app.permanent_session_lifetime = timedelta(days=30)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================
# GOOGLE SHEETS CONFIG 🔥
# =============================
SHEET_ID = "11omZV-J8sn_qZ7htmaF-9tgCGwh_fwcklGchlGOA0RI"
SHEET_NAME = "Hoja 1"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# 🔥 USAR ENV EN RENDER
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
# CAMBIAR ESTADO 🔥🔥🔥
# =============================
@app.route("/desactivar/<rut>", methods=["POST"])
def desactivar(rut):

    if "user" not in session:
        return {"error": "no autorizado"}, 403

    try:
        data = request.get_json()
        nuevo_estado = data.get("estado", "INACTIVO")

        # 🔥 1. GUARDAR EN SQLITE
        guardar_estado(rut, nuevo_estado)

        # 🔥 2. ACTUALIZAR GOOGLE SHEETS
        datos_sheet = sheet.get_all_records()

        for i, row in enumerate(datos_sheet, start=2):

            rut_sheet = str(row.get("CARNET", "")).strip()

            if rut_sheet == rut:
                sheet.update_cell(i, 15, nuevo_estado)  # Columna O
                break

        # 🔥 3. REGENERAR JSON
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
# RUN
# =============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

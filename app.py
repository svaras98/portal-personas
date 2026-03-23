# app.py
from flask import Flask, request, redirect, session, send_from_directory, send_file
import json
import os
from datetime import timedelta, datetime
from leer_datos_jason import generar_json

app = Flask(__name__)
app.secret_key = "Empresacoldcontrolcontactocoldcontrol"

app.permanent_session_lifetime = timedelta(days=30)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def cargar_usuarios():
    with open(os.path.join(BASE_DIR, "usuarios.json"), "r", encoding="utf-8") as f:
        return json.load(f)["usuarios"]

def calcular_dias(fecha_str):
    if not fecha_str or fecha_str == "∞":
        return "INDEFINIDO"
    try:
        fecha = datetime.strptime(fecha_str, "%d-%m-%Y")
        hoy = datetime.today()
        return (fecha - hoy).days
    except:
        return ""

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

@app.route("/index.html")
def index():
    if "user" not in session:
        return redirect("/")
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/detalle.html")
def detalle():
    if "user" not in session:
        return redirect("/")
    return send_from_directory(BASE_DIR, "detalle.html")

@app.route("/datos.json")
def datos():
    if "user" not in session:
        return redirect("/")

    # 🔹 Generar automáticamente cada vez que se solicita
    generar_json()

    return send_file(os.path.join(BASE_DIR, "datos.json"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
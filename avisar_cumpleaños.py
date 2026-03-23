import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

# =============================
# Cargar Excel
# =============================

df = pd.read_excel("Cumpleaños.xlsx")

hoy = datetime.today().date()
mañana = hoy + timedelta(days=1)

alertas = []

# =============================
# Revisar cumpleaños
# =============================

for index, row in df.iterrows():

    nombre = row["NOMBRE"]
    fecha_cumpleaños = row["CUMPLEAÑOS"]

    if pd.isnull(fecha_cumpleaños):
        continue

    fecha_cumpleaños = pd.to_datetime(fecha_cumpleaños)

    cumple_este_año = datetime(
        hoy.year,
        fecha_cumpleaños.month,
        fecha_cumpleaños.day
    ).date()

    if cumple_este_año == mañana:
        alertas.append(f"{nombre} está de cumpleaños mañana ({cumple_este_año})")

# =============================
# Enviar correo
# =============================

if alertas:

    mensaje = "\n".join(alertas)

    email = EmailMessage()
    email["Subject"] = "Aviso de cumpleaños"
    email["From"] = "contacto@coldcontrol.cl"
    email["To"] = "cmolina@coldcontrol.cl"

    email.set_content(mensaje)

    try:

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login("contacto@coldcontrol.cl", "fhkc zwiz pmup xgrc")
            smtp.send_message(email)

        print("Correo enviado correctamente")

    except Exception as e:
        print("Error enviando correo:", e)

else:
    print("No hay cumpleaños mañana")
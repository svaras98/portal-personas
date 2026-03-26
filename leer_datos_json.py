# leer_datos_jason.py

import json
import gspread
from datetime import datetime, date
from google.oauth2.service_account import Credentials
from db import obtener_estado, guardar_estado

SHEET_ID = "11omZV-J8sn_qZ7htmaF-9tgCGwh_fwcklGchlGOA0RI"
SHEET_NAME = "Hoja 1"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

import os
import json

if os.getenv("GOOGLE_CREDENTIALS"):
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    CREDS = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
else:
    CREDS = Credentials.from_service_account_file(
        "credenciales.json", scopes=SCOPES
    )

client = gspread.authorize(CREDS)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)


def calcular_dias_contrato(fecha):
    hoy = datetime.today()
    return (fecha - hoy).days + 1


def calcular_dias_cumple(cumple):

    if not cumple:
        return ""

    try:
        hoy = date.today()
        cumple_este_año = date(hoy.year, cumple.month, cumple.day)

        if cumple_este_año < hoy:
            cumple_este_año = date(hoy.year + 1, cumple.month, cumple.day)

        return (cumple_este_año - hoy).days

    except:
        return ""


def generar_json():

    datos_sheet = sheet.get_all_records()

    datos = []

    for i, row in enumerate(datos_sheet, start=2):

        nombre = row.get("NOMBRE")
        tipo = row.get("TIPO DE CONTRATO")
        rut = str(row.get("CARNET", "")).strip()

        cumple_raw = row.get("CUMPLEAÑOS")
        fecha_raw = row.get("FECHA DE CONTRATO")

        cumple = None
        if cumple_raw:
            try:
                cumple = datetime.strptime(cumple_raw, "%d/%m/%Y")
            except:
                pass

        estado = obtener_estado(rut)

        if not estado:
            estado_excel = row.get("ESTADO")
            estado = estado_excel if estado_excel else "ACTIVO"

        if estado not in ["ACTIVO", "INACTIVO"]:
            estado = "ACTIVO"

        if tipo == "INDEFINIDO":

            dias = "INDEFINIDO"
            fecha_termino = "∞"

        else:

            try:
                fecha = datetime.strptime(fecha_raw, "%d-%m-%Y")

                dias = calcular_dias_contrato(fecha)
                fecha_termino = fecha.strftime("%d-%m-%Y")

                # 🔥 AUTO INACTIVO
                if isinstance(dias, int) and dias <= 0:
                    estado = "INACTIVO"
                    guardar_estado(rut, "INACTIVO")

            except:
                dias = ""
                fecha_termino = None

        persona = {

            "id": i,
            "nombre": nombre,
            "tipo": tipo,
            "dias": dias,
            "fecha_termino": fecha_termino,
            "rut": rut,
            "estado": estado,

            "cumple": cumple.strftime("%d/%m/%Y") if cumple else "",
            "dias_cumple": calcular_dias_cumple(cumple),

            "pdfs": {
                "ci": row.get("PDF CI", ""),
                "contrato": row.get("PDF CT", ""),
                "psi": row.get("PDF PSI", ""),
                "lc": row.get("PDF LC", ""),
                "informe": row.get("PDF INFORME", "")
            }

        }

        datos.append(persona)

    with open("datos.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

    print("✅ datos.json generado desde Google Sheets")


if __name__ == "__main__":
    generar_json()

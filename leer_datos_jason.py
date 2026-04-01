import json
import os
import gspread
from datetime import datetime, date
from google.oauth2.service_account import Credentials
from db import obtener_estado, guardar_estado

SHEET_ID = "11omZV-J8sn_qZ7htmaF-9tgCGwh_fwcklGchlGOA0RI"
SHEET_NAME = "Hoja 1"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# =============================
# CREDENCIALES
# =============================
if os.getenv("GOOGLE_CREDENTIALS"):
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    CREDS = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
else:
    CREDS = Credentials.from_service_account_file(
        "credenciales.json", scopes=SCOPES
    )

client = gspread.authorize(CREDS)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# =============================
# FUNCIONES
# =============================
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

# =============================
# GENERAR JSON
# =============================
def generar_json():

    datos_sheet = sheet.get_all_records()
    datos = []

    for i, row in enumerate(datos_sheet, start=2):

        nombre = row.get("NOMBRE")
        tipo = row.get("TIPO DE CONTRATO")
        rut = str(row.get("CARNET", "")).strip()

        cumple_raw = row.get("CUMPLEAÑOS")
        fecha_raw = row.get("FECHA DE CONTRATO")

        # =============================
        # CUMPLEAÑOS
        # =============================
        cumple = None
        if cumple_raw:
            try:
                if isinstance(cumple_raw, datetime):
                    cumple = cumple_raw
                else:
                    for formato in ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                        try:
                            cumple = datetime.strptime(str(cumple_raw), formato)
                            break
                        except:
                            continue
            except:
                cumple = None

        # =============================
        # ESTADO
        # =============================
        estado = obtener_estado(rut)

        if not estado:
            estado = row.get("ESTADO") or "ACTIVO"

        if estado not in ["ACTIVO", "INACTIVO"]:
            estado = "ACTIVO"

        # =============================
        # 🔥 LÓGICA CONTRATO (CLAVE)
        # =============================
        if estado == "INACTIVO":
            dias = "SIN CONTRATO"
            fecha_termino = "SIN FECHA"

        elif tipo == "INDEFINIDO":
            dias = "INDEFINIDO"
            fecha_termino = "∞"

        else:
            try:
                if fecha_raw:
                    fecha = datetime.strptime(str(fecha_raw), "%d-%m-%Y")
                    dias_calc = calcular_dias_contrato(fecha)

                    if dias_calc <= 0:
                        dias = "SIN CONTRATO"
                        fecha_termino = "SIN FECHA"
                        estado = "INACTIVO"
                        guardar_estado(rut, "INACTIVO")
                    else:
                        dias = dias_calc
                        fecha_termino = fecha.strftime("%d-%m-%Y")
                else:
                    dias = ""
                    fecha_termino = ""

            except:
                dias = ""
                fecha_termino = ""

        # =============================
        # OBJETO FINAL
        # =============================
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
                "ci": str(row.get("PDF CI", "")).strip(),
                "contrato": str(row.get("PDF CT", "")).strip(),
                "psi": str(row.get("PDF PSI", "")).strip(),
                "lc": str(row.get("PDF LC", "")).strip(),
                "informe": str(row.get("PDF INFORME", "")).strip()
            }
        }

        datos.append(persona)

    with open("datos.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

    print("✅ datos.json generado correctamente")


if __name__ == "__main__":
    generar_json()

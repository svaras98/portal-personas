# leer_datos_json.py

import json
from openpyxl import load_workbook
from datetime import datetime, date

EXCEL_FILE = "Cumpleaños.xlsx"

def get_link(cell):

    # Caso 1: hyperlink normal de Excel
    if cell.hyperlink:
        return cell.hyperlink.target

    # Caso 2: hyperlink guardado como texto
    if isinstance(cell.value, str) and cell.value.startswith("http"):
        return cell.value

    # Caso 3: fórmula =HYPERLINK(...)
    if isinstance(cell.value, str) and "HYPERLINK" in cell.value.upper():
        try:
            link = cell.value.split('"')[1]
            return link
        except:
            return ""

    return ""

def calcular_dias_contrato(fecha):
    hoy = datetime.today()
    return (fecha - hoy).days + 1


def calcular_dias_cumple(cumple):

    if not cumple:
        return ""

    try:
        hoy = date.today()

        # Convertir cumpleaños a fecha limpia (sin hora)
        cumple_este_año = date(hoy.year, cumple.month, cumple.day)

        # Si ya pasó este año, usar el siguiente
        if cumple_este_año < hoy:
            cumple_este_año = date(hoy.year + 1, cumple.month, cumple.day)

        return (cumple_este_año - hoy).days

    except:
        return ""


def generar_json():

    wb = load_workbook(EXCEL_FILE)
    ws = wb.active

    datos = []

    for row in range(2, ws.max_row + 1):

        nombre = ws[f"B{row}"].value
        tipo = ws[f"A{row}"].value
        rut = ws[f"E{row}"].value
        cumple = ws[f"C{row}"].value
        fecha_raw = ws[f"N{row}"].value

        # 🔹 leer estado del Excel
        estado = ws[f"O{row}"].value

        # 🔹 si está vacío se considera ACTIVO
        if not estado:
            estado = "ACTIVO"

        if fecha_raw == "∞" or tipo == "INDEFINIDO":

            dias = "INDEFINIDO"
            fecha_termino = "∞"

        else:

            try:

                if isinstance(fecha_raw, datetime):
                    fecha = fecha_raw
                else:
                    fecha = datetime.strptime(str(fecha_raw), "%d-%m-%Y")

                dias = calcular_dias_contrato(fecha)
                fecha_termino = fecha.strftime("%d-%m-%Y")

            except:

                dias = ""
                fecha_termino = None

        persona = {

            "id": row,
            "nombre": nombre,
            "tipo": tipo,
            "dias": dias,
            "fecha_termino": fecha_termino,
            "rut": rut if rut else "",
            "estado": estado,

            "cumple": cumple.strftime("%d/%m/%Y") if isinstance(cumple, datetime) else "",
            "dias_cumple": calcular_dias_cumple(cumple),

            "pdfs": {

                "ci": get_link(ws[f"F{row}"]),
                "contrato": get_link(ws[f"H{row}"]),
                "psi": get_link(ws[f"J{row}"]),
                "lc": get_link(ws[f"L{row}"]),
                "informe": get_link(ws[f"M{row}"])

            }

        }

        datos.append(persona)

    with open("datos.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

    print("✅ datos.json generado correctamente")


if __name__ == "__main__":
    generar_json()

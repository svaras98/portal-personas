# leer_datos_json.py
import json 
from openpyxl import load_workbook
from datetime import datetime

EXCEL_FILE = "Cumpleaños.xlsx"

def get_link(cell):
    if cell.hyperlink:
        return cell.hyperlink.target
    return ""

def calcular_dias_contrato(fecha):
    hoy = datetime.today()
    return (fecha - hoy).days + 1 

def calcular_dias_cumple(cumple):
    if not cumple:
        return ""
    hoy = datetime.today()
    try:
        cumple_este_año = cumple.replace(year=hoy.year)
        if cumple_este_año < hoy:
            cumple_este_año = cumple.replace(year=hoy.year + 1)
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

# Solo se ejecuta si se llama directamente
if __name__ == "__main__":
    generar_json()

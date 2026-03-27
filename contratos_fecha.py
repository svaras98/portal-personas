import os
import re
import requests
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from pdf2image import convert_from_path
import pytesseract
from pypdf import PdfReader


# =============================
# CONFIG
# =============================

SHEET_ID = "11omZV-J8sn_qZ7htmaF-9tgCGwh_fwcklGchlGOA0RI"
SHEET_NAME = "Hoja 1"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


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


POPPLER_PATH = r"C:\Users\svara\Desktop\Release-24.08.0-0\poppler-24.08.0\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

PDF_FOLDER = "pdfs"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

os.makedirs(PDF_FOLDER, exist_ok=True)


# =============================
# DRIVE
# =============================

def convertir_drive(url):
    match = re.search(r'/d/(.*?)/', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


# =============================
# PDF
# =============================

def descargar_pdf(url, path):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except:
        pass
    return False


def leer_pdf(path):
    texto = ""
    try:
        reader = PdfReader(path)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                texto += t
    except:
        pass
    return texto


def leer_ocr(path):
    texto = ""
    images = convert_from_path(path, poppler_path=POPPLER_PATH)

    for img in images:
        texto += pytesseract.image_to_string(img, lang="spa")

    return texto


def limpiar_texto(texto):
    texto = texto.lower()

    reemplazos = {
        "mar20": "marzo",
        "marz0": "marzo",
        "setiembre": "septiembre",
        "novienbre": "noviembre"
    }

    for k, v in reemplazos.items():
        texto = texto.replace(k, v)

    return texto


def extraer_fechas(texto):

    texto = limpiar_texto(texto)

    meses = {
        "enero":1, "febrero":2, "marzo":3, "abril":4,
        "mayo":5, "junio":6, "julio":7, "agosto":8,
        "septiembre":9, "octubre":10, "noviembre":11, "diciembre":12
    }

    fechas = []

    matches = re.findall(r"(\d{1,2}) de ([a-z]+) de (\d{4})", texto)

    for d, m, y in matches:
        if m in meses:
            try:
                fechas.append(datetime(int(y), meses[m], int(d)))
            except:
                pass

    return fechas


def detectar_fecha(path):
    texto = leer_pdf(path)
    texto += leer_ocr(path)

    fechas = extraer_fechas(texto)

    if fechas:
        return max(fechas)

    return None


# =============================
# PROCESO
# =============================

def procesar():

    print("📄 LEYENDO CONTRATOS...\n")

    data = sheet.get_all_records()

    for i, row in enumerate(data, start=2):

        nombre = row.get("NOMBRE")
        tipo = row.get("TIPO DE CONTRATO")
        pdf_link = row.get("PDF CT")
        fecha_actual = row.get("FECHA DE CONTRATO")

        print(f"👤 {nombre}")

        if tipo == "INDEFINIDO":
            sheet.update_cell(i, 14, "∞")  # columna FECHA
            print("♾️ Indefinido\n")
            continue

        if fecha_actual not in (None, "", " "):
            print("✅ Ya tiene fecha\n")
            continue

        if not pdf_link:
            print("❌ Sin PDF\n")
            continue

        url = convertir_drive(pdf_link)

        pdf_path = os.path.join(PDF_FOLDER, f"{i}.pdf")

        if not descargar_pdf(url, pdf_path):
            print("❌ Error descarga\n")
            continue

        fecha = detectar_fecha(pdf_path)

        if fecha:
            fecha_str = fecha.strftime("%d-%m-%Y")
            sheet.update_cell(i, 14, fecha_str)
            print("📅 Fecha detectada:", fecha_str, "\n")
        else:
            print("❌ No se detectó fecha\n")

    print("✅ PROCESO TERMINADO")


if __name__ == "__main__":
    procesar()

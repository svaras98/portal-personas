import os
import sys
import json
import gspread

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# =========================
# CONFIG
# =========================

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets"
]

SHEET_ID = "11omZV-J8sn_qZ7htmaF-9tgCGwh_fwcklGchlGOA0RI"
SHEET_NAME = "Hoja 1"

FOLDER_ID = "1MAleZ8QRbl7ldXYlORErhGQP_ptnYIxq"

# =========================
# AUTH 🔥
# =========================

if os.getenv("GOOGLE_CREDENTIALS"):
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
else:
    creds = Credentials.from_service_account_file("credenciales.json", scopes=SCOPES)

# Sheets
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# Drive
service = build("drive", "v3", credentials=creds)

print("✅ Conectado a Google Drive + Sheets")

# =========================
# FUNCIONES
# =========================

def invertir_nombre(nombre):
    partes = nombre.strip().split()
    if len(partes) >= 2:
        return f"{partes[-1]} {partes[0]}".upper()
    return nombre.upper()


def buscar_carpeta(nombre):
    query = f"name contains '{nombre}' and '{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"

    results = service.files().list(
        q=query,
        fields="files(id,name)"
    ).execute()

    files = results.get("files", [])
    return files[0]["id"] if files else None


def contar_pdfs_drive(folder_id):
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"

    results = service.files().list(
        q=query,
        fields="files(id,name)"
    ).execute()

    return len(results.get("files", []))


def contar_pdfs_sheet(row):
    columnas = ["PDF CI", "PDF CT", "PDF PSI", "PDF LC", "PDF INFORME"]
    return sum(1 for col in columnas if row.get(col))


# =========================
# PROCESO
# =========================

data = sheet.get_all_records()
cambios_detectados = False

for row in data:

    nombre_excel = str(row.get("NOMBRE", "")).upper()
    nombre_busqueda = invertir_nombre(nombre_excel)

    print("🔎 Revisando:", nombre_busqueda)

    carpeta = buscar_carpeta(nombre_busqueda)

    if not carpeta:
        print("❌ Carpeta no encontrada\n")
        continue

    pdf_drive = contar_pdfs_drive(carpeta)
    pdf_sheet = contar_pdfs_sheet(row)

    print("Drive:", pdf_drive, "| Sheet:", pdf_sheet)

    if pdf_drive > pdf_sheet:
        print("🚨 CAMBIOS DETECTADOS\n")
        cambios_detectados = True
        break

    print("✔ Sin cambios\n")


# =========================
# RESULTADO
# =========================

if cambios_detectados:
    sys.exit(1)
else:
    sys.exit(0)

import os
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
# AUTH (🔥 CLAVE)
# =========================

if os.getenv("GOOGLE_CREDENTIALS"):
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
else:
    creds = Credentials.from_service_account_file(
        "credenciales.json", scopes=SCOPES
    )

# Sheets
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# Drive
service = build("drive", "v3", credentials=creds)

print("✅ Conectado a Google Sheets + Drive")

# =========================
# INVERTIR NOMBRE
# =========================

def invertir_nombre(nombre):

    partes = nombre.strip().split()

    if len(partes) >= 2:
        nombre = partes[0]
        apellido = partes[-1]
        return f"{apellido} {nombre}".upper()

    return nombre.upper()

# =========================
# BUSCAR CARPETA
# =========================

def buscar_carpeta(nombre):

    query = f"name contains '{nombre}' and '{FOLDER_ID}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"

    results = service.files().list(
        q=query,
        fields="files(id,name)"
    ).execute()

    files = results.get("files", [])

    if files:
        return files[0]["id"]

    return None

# =========================
# OBTENER PDFS
# =========================

def obtener_pdfs(folder_id):

    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"

    results = service.files().list(
        q=query,
        fields="files(id,name)"
    ).execute()

    return results.get("files", [])

# =========================
# COLUMNAS DINÁMICAS
# =========================

headers = sheet.row_values(1)
col_index = {name: idx+1 for idx, name in enumerate(headers)}

# =========================
# RECORRER SHEET
# =========================

data = sheet.get_all_records()

for i, row in enumerate(data, start=2):

    nombre_excel = str(row["NOMBRE"]).upper()
    nombre_busqueda = invertir_nombre(nombre_excel)

    print("🔎 Buscando:", nombre_busqueda)

    folder_id = buscar_carpeta(nombre_busqueda)

    if not folder_id:
        print("❌ Carpeta no encontrada\n")
        continue

    archivos = obtener_pdfs(folder_id)

    for archivo in archivos:

        nombre_archivo = archivo["name"].upper()
        file_id = archivo["id"]

        link = f"https://drive.google.com/file/d/{file_id}/view"

        # =========================
        # PSI
        # =========================
        if "PSICOSENSOTECNICO" in nombre_archivo:

            col = col_index.get("PDF PSI")
            if col and not row.get("PDF PSI"):
                sheet.update_cell(i, col, link)

        # =========================
        # LICENCIA
        # =========================
        elif nombre_archivo.startswith("LC"):

            col = col_index.get("PDF LC")
            if col and not row.get("PDF LC"):
                sheet.update_cell(i, col, link)

        # =========================
        # INFORME
        # =========================
        elif "INFORME" in nombre_archivo:

            col = col_index.get("PDF INFORME")
            if col and not row.get("PDF INFORME"):
                sheet.update_cell(i, col, link)

        # =========================
        # CONTRATO
        # =========================
        elif nombre_archivo.startswith("CT"):

            col = col_index.get("PDF CT")
            if col and not row.get("PDF CT"):
                sheet.update_cell(i, col, link)

        # =========================
        # CI
        # =========================
        elif "CI" in nombre_archivo:

            col = col_index.get("PDF CI")
            if col and not row.get("PDF CI"):
                sheet.update_cell(i, col, link)

    print("✅ Actualizado\n")

print("🚀 PROCESO TERMINADO")

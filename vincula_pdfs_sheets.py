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
# AUTH
# =========================

if os.getenv("GOOGLE_CREDENTIALS"):
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
else:
    creds = Credentials.from_service_account_file(
        "credenciales.json", scopes=SCOPES
    )

client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
service = build("drive", "v3", credentials=creds)

print("✅ Conectado a Google Sheets + Drive")

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


def obtener_pdfs(folder_id):
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"

    results = service.files().list(
        q=query,
        fields="files(id,name)"
    ).execute()

    return results.get("files", [])


# =========================
# COLUMNAS
# =========================

headers = sheet.row_values(1)
col_index = {name: idx+1 for idx, name in enumerate(headers)}

# =========================
# PROCESO
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

    # 🔥 limpiar estructura temporal
    nuevos_links = {
        "PDF CI": "",
        "PDF CT": "",
        "PDF PSI": "",
        "PDF LC": "",
        "PDF INFORME": ""
    }

    for archivo in archivos:

        nombre_archivo = archivo["name"].upper()
        file_id = archivo["id"]

        link = f"https://drive.google.com/file/d/{file_id}/view"

        if "PSICOSENSOTECNICO" in nombre_archivo:
            nuevos_links["PDF PSI"] = link

        elif nombre_archivo.startswith("LC"):
            nuevos_links["PDF LC"] = link

        elif "INFORME" in nombre_archivo:
            nuevos_links["PDF INFORME"] = link

        elif nombre_archivo.startswith("CT"):
            nuevos_links["PDF CT"] = link

        elif "CI" in nombre_archivo:
            nuevos_links["PDF CI"] = link

    # 🔥 AHORA SÍ: actualizar SI CAMBIA
    for campo, nuevo_link in nuevos_links.items():

        col = col_index.get(campo)
        valor_actual = str(row.get(campo, "")).strip()

        if col and nuevo_link != valor_actual:
            print(f"🔄 Actualizando {campo}")
            sheet.update_cell(i, col, nuevo_link)

    print("✅ Actualizado\n")

print("🚀 PROCESO TERMINADO")

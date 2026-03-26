import sys
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


# =========================
# CONFIG
# =========================

SHEET_ID = "11omZV-J8sn_qZ7htmaF-9tgCGwh_fwcklGchlGOA0RI"
SHEET_NAME = "Hoja 1"

FOLDER_ID = "1MAleZ8QRbl7ldXYlORErhGQP_ptnYIxq"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly"
]


# =========================
# AUTH
# =========================

CREDS = Credentials.from_service_account_file(
    "credenciales.json", scopes=SCOPES
)

client = gspread.authorize(CREDS)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

drive_service = build("drive", "v3", credentials=CREDS)

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

    results = drive_service.files().list(
        q=query,
        fields="files(id,name)"
    ).execute()

    files = results.get("files", [])

    if files:
        return files[0]["id"]

    return None


def contar_pdfs(folder_id):

    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"

    results = drive_service.files().list(
        q=query,
        fields="files(id,name)"
    ).execute()

    return len(results.get("files", []))


def contar_pdfs_sheet(row):

    columnas = ["PDF CI", "PDF CT", "PDF PSI", "PDF LC", "PDF INFORME"]

    total = 0

    for col in columnas:
        if row.get(col):
            total += 1

    return total


# =========================
# PROCESO
# =========================

data = sheet.get_all_records()

cambios_detectados = False

for row in data:

    nombre = str(row.get("NOMBRE", "")).upper()
    nombre_busqueda = invertir_nombre(nombre)

    print("🔎 Revisando:", nombre_busqueda)

    carpeta = buscar_carpeta(nombre_busqueda)

    if not carpeta:
        print("❌ Carpeta no encontrada\n")
        continue

    pdf_drive = contar_pdfs(carpeta)
    pdf_sheet = contar_pdfs_sheet(row)

    print("Drive:", pdf_drive, "| Sheet:", pdf_sheet)

    if pdf_drive > pdf_sheet:
        print("🚨 Cambios detectados\n")
        cambios_detectados = True
        break

    print("✔ Sin cambios\n")


# =========================
# RESULTADO
# =========================

if cambios_detectados:
    print("⚡ Se detectaron cambios en Drive")
    sys.exit(1)
else:
    print("✅ No hay cambios")
    sys.exit(0)
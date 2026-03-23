import os
import sys
import pandas as pd

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# =========================
# CONFIG
# =========================

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

EXCEL_FILE = "Cumpleaños.xlsx"

FOLDER_ID = "1MAleZ8QRbl7ldXYlORErhGQP_ptnYIxq"


# =========================
# AUTENTICACION GOOGLE
# =========================

creds = None

if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)

if not creds:

    flow = InstalledAppFlow.from_client_secrets_file(
        "credenciales.json", SCOPES)

    creds = flow.run_local_server(port=0)

    with open("token.json", "w") as token:
        token.write(creds.to_json())

service = build("drive", "v3", credentials=creds)

print("✅ Conectado a Google Drive")


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
# CONTAR PDFS EN DRIVE
# =========================

def contar_pdfs(folder_id):

    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"

    results = service.files().list(
        q=query,
        fields="files(id,name)"
    ).execute()

    files = results.get("files", [])

    return len(files)


# =========================
# CONTAR PDFS EN EXCEL
# =========================

def contar_pdfs_excel(row):

    columnas = ["PDF CI", "PDF CT", "PDF PSI", "PDF LC", "PDF INFORME"]

    total = 0

    for col in columnas:
        if pd.notna(row.get(col)):
            total += 1

    return total


# =========================
# REVISAR CAMBIOS
# =========================

df = pd.read_excel(EXCEL_FILE)

cambios_detectados = False


for i, row in df.iterrows():

    nombre_excel = str(row["NOMBRE"]).upper()

    nombre_busqueda = invertir_nombre(nombre_excel)

    print("🔎 Revisando:", nombre_busqueda)

    carpeta = buscar_carpeta(nombre_busqueda)

    if not carpeta:
        print("❌ Carpeta no encontrada\n")
        continue

    print("📁 Carpeta encontrada")

    pdf_drive = contar_pdfs(carpeta)

    pdf_excel = contar_pdfs_excel(row)

    print("PDFs Drive:", pdf_drive)
    print("PDFs Excel:", pdf_excel)

    if pdf_drive > pdf_excel:

        print("🚨 Cambios detectados (PDF nuevo o contrato actualizado)\n")

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
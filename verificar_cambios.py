import os
import sys
import json
import gspread
import subprocess

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

ESTADO_FILE = "estado_cambios.json"

# =========================
# AUTH
# =========================

if os.getenv("GOOGLE_CREDENTIALS"):
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
else:
    creds = Credentials.from_service_account_file("credenciales.json", scopes=SCOPES)

client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
service = build("drive", "v3", credentials=creds)

print("✅ Conectado a Google Drive + Sheets\n")

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


def obtener_ultima_modificacion(folder_id):
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"

    results = service.files().list(
        q=query,
        fields="files(name, modifiedTime)"
    ).execute()

    archivos = results.get("files", [])

    if not archivos:
        return None

    # 🔥 obtener la más reciente
    ultima = max(file["modifiedTime"] for file in archivos)
    return ultima


def cargar_estado():
    if not os.path.exists(ESTADO_FILE):
        return {}
    with open(ESTADO_FILE, "r") as f:
        return json.load(f)


def guardar_estado(estado):
    with open(ESTADO_FILE, "w") as f:
        json.dump(estado, f, indent=4)


# =========================
# PROCESO PRINCIPAL
# =========================

def verificar():

    data = sheet.get_all_records()
    estado_anterior = cargar_estado()
    nuevo_estado = {}

    cambios_detectados = False

    for row in data:

        nombre_excel = str(row.get("NOMBRE", "")).upper()
        nombre_busqueda = invertir_nombre(nombre_excel)

        print("🔎 Revisando:", nombre_busqueda)

        carpeta = buscar_carpeta(nombre_busqueda)

        if not carpeta:
            print("❌ Carpeta no encontrada\n")
            continue

        ultima_mod_drive = obtener_ultima_modificacion(carpeta)

        if not ultima_mod_drive:
            print("⚠️ Sin PDFs\n")
            continue

        print("Última modificación Drive:", ultima_mod_drive)

        ultima_guardada = estado_anterior.get(nombre_busqueda)

        if ultima_guardada != ultima_mod_drive:
            print("🚨 CAMBIO DETECTADO\n")
            cambios_detectados = True
        else:
            print("✔ Sin cambios\n")

        nuevo_estado[nombre_busqueda] = ultima_mod_drive

    guardar_estado(nuevo_estado)

    return cambios_detectados


# =========================
# PIPELINE
# =========================

def ejecutar_pipeline():

    try:
        print("⚙️ Ejecutando vinculación de PDFs...")
        subprocess.run(["python", "vincula_pdfs_sheets.py"], check=True)

        print("📄 Procesando contratos...")
        subprocess.run(["python", "contratos_fecha.py"], check=True)

        print("🔄 Generando JSON...")
        subprocess.run(["python", "leer_datos_jason.py"], check=True)

        print("✅ PIPELINE COMPLETO OK\n")

    except subprocess.CalledProcessError as e:
        print("❌ ERROR en pipeline:", e)


# =========================
# MAIN
# =========================

if __name__ == "__main__":

    print("🚀 INICIANDO VERIFICACIÓN...\n")

    cambios = verificar()

    if cambios:
        ejecutar_pipeline()
        sys.exit(1)
    else:
        print("✔ Todo actualizado, no se requieren cambios\n")
        sys.exit(0)

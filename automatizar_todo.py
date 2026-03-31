import subprocess
import sys

def ejecutar_script(script):
    print(f"\n▶ Ejecutando: {script}")
    
    resultado = subprocess.run(["python", script])
    
    if resultado.returncode != 0:
        print(f"❌ Error en {script}")
        sys.exit(1)  # Detiene todo si algo falla
    else:
        print(f"✅ {script} completado correctamente")


def main():
    print("🚀 INICIANDO AUTOMATIZACIÓN...\n")

    # 1. Vincular PDFs (SIEMPRE)
    ejecutar_script("vincula_pdfs_sheets.py")

    # 2. Procesar fechas desde contratos
    ejecutar_script("contratos_fecha.py")

    # 3. Generar JSON final
    ejecutar_script("leer_datos_jason.py")

    print("\n🎉 TODO ACTUALIZADO CORRECTAMENTE")


if __name__ == "__main__":
    main()

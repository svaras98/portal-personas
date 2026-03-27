import subprocess

print("🚀 INICIANDO AUTOMATIZACIÓN...\n")

# 1. Verificar cambios
resultado = subprocess.run(["python", "verificar_cambios.py"])

if resultado.returncode == 1:
    print("🔄 Cambios detectados...\n")

    # 2. Vincular PDFs
    subprocess.run(["python", "vincula_pdfs_sheets.py"])

    # 3. Leer contratos
    subprocess.run(["python", "contratos_fecha.py"])

    # 4. Generar JSON
    subprocess.run(["python", "leer_datos_jason.py"])

    print("\n✅ TODO ACTUALIZADO")

else:
    print("✔ No hay cambios")

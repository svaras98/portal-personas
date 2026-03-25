import sqlite3

DB_FILE = "estado.db"

def conectar():
    return sqlite3.connect(DB_FILE)

def crear_tabla():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estados (
            rut TEXT PRIMARY KEY,
            estado TEXT
        )
    """)

    conn.commit()
    conn.close()

# Guardar estado
def guardar_estado(rut, estado):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO estados (rut, estado)
        VALUES (?, ?)
        ON CONFLICT(rut) DO UPDATE SET estado=excluded.estado
    """, (rut, estado))

    conn.commit()
    conn.close()

# Obtener estado
def obtener_estado(rut):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT estado FROM estados WHERE rut = ?", (rut,))
    resultado = cursor.fetchone()

    conn.close()

    if resultado:
        return resultado[0]

    return None
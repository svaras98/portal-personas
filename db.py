import sqlite3
import os

DB_FILE = "estado.db"


# =============================
# CREAR TABLA SI NO EXISTE
# =============================
def crear_tabla():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS estados (
            rut TEXT PRIMARY KEY,
            estado TEXT
        )
    """)

    conn.commit()
    conn.close()


# =============================
# GUARDAR ESTADO
# =============================
def guardar_estado(rut, estado):

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO estados (rut, estado)
        VALUES (?, ?)
        ON CONFLICT(rut) DO UPDATE SET estado=excluded.estado
    """, (rut, estado))

    conn.commit()
    conn.close()


# =============================
# OBTENER ESTADO
# =============================
def obtener_estado(rut):

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT estado FROM estados WHERE rut = ?", (rut,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return None


# Crear tabla automáticamente
crear_tabla()

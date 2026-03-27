import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "estado.db")


def get_conn():
    return sqlite3.connect(DB_FILE)


# =============================
# CREAR TABLA
# =============================
def crear_tabla():
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estados (
                rut TEXT PRIMARY KEY,
                estado TEXT
            )
        """)


# =============================
# GUARDAR ESTADO
# =============================
def guardar_estado(rut, estado):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO estados (rut, estado)
            VALUES (?, ?)
            ON CONFLICT(rut) DO UPDATE SET estado=excluded.estado
        """, (rut, estado))


# =============================
# OBTENER ESTADO
# =============================
def obtener_estado(rut):
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT estado FROM estados WHERE rut = ?", (rut,))
        result = cursor.fetchone()
        return result[0] if result else None


crear_tabla()

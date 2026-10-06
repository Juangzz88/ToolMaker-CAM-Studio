# -*- coding: utf-8 -*-
import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "toolmaker_admin.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o migra la tabla de licencias en SQLite."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear tabla si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            hwid TEXT NOT NULL,
            email TEXT,
            license_key TEXT UNIQUE NOT NULL,
            days INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            exp_date TEXT NOT NULL,
            status TEXT DEFAULT 'ACTIVE'
        )
    ''')
    
    # Migración defensiva: Agregar columna hwid si la tabla existía previamente sin ella
    cursor.execute("PRAGMA table_info(licenses)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'hwid' not in columns:
        cursor.execute("ALTER TABLE licenses ADD COLUMN hwid TEXT DEFAULT 'UNKNOWN'")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Base de datos de administración actualizada correctamente.")

import sqlite3

DB_NAME = "amostras.db"

def create_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS amostras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        fabricante TEXT NOT NULL,
        processo INTEGER NOT NULL,
        data_entrada TEXT,
        tipo TEXT,
        numero_nf TEXT,
        data_retirada TEXT,
        status TEXT DEFAULT 'Em bancada',
        responsavel_cadastro TEXT NOT NULL,
        responsavel_alteracao TEXT 
    )
    """)
    conn.commit()
    conn.close()

create_table()
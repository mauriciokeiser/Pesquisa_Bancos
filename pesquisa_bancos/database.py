import os
import sqlite3

# Descobre a pasta onde o arquivo database.py está e cria o banco lá dentro
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "bancos.db")

#DB_NAME = "bancos.db"

def init_db():
    """Inicializa a tabela de bancos no SQLite."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bancos (
                ispb TEXT PRIMARY KEY,
                name TEXT,
                code INTEGER,
                fullName TEXT
            )
        """)
        conn.commit()

def save_banks(banks_list):
    """Salva a lista de dicionários vinda da API usando regras de INSERT OR REPLACE."""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        for bank in banks_list:
            ispb = bank.get("ispb", "")
            name = bank.get("name", "")
            code = bank.get("code")
            full_name = bank.get("fullName", "")
            
            cursor.execute("""
                INSERT OR REPLACE INTO bancos (ispb, name, code, fullName)
                VALUES (?, ?, ?, ?)
            """, (ispb, name, code, full_name))
        conn.commit()

def get_all_banks():
    """Recupera todos os registros convertendo as linhas mapeadas em dicionários Python."""
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT ispb, name, code, fullName FROM bancos")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
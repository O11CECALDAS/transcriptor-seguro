import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "records.db")

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            date TEXT NOT NULL,
            duration_est TEXT,
            resumen TEXT,
            puntos_clave TEXT,
            acuerdos TEXT,
            transcripcion TEXT,
            raw_full TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_record(
    title: str,
    filename: str,
    resumen: str,
    puntos_clave: str,
    acuerdos: str,
    transcripcion: str,
    raw_full: str,
    duration_est: str = ""
) -> int:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("""
        INSERT INTO records (title, filename, date, duration_est, resumen, puntos_clave, acuerdos, transcripcion, raw_full)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (title, filename, now_str, duration_est, resumen, puntos_clave, acuerdos, transcripcion, raw_full))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def get_all_records() -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM records ORDER BY id DESC")
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    return result

def get_record_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM records WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def delete_record(record_id: int):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

def search_records(query: str) -> List[Dict[str, Any]]:
    init_db()
    if not query or not query.strip():
        return get_all_records()
    q = f"%{query.strip()}%"
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM records
        WHERE title LIKE ? OR filename LIKE ? OR resumen LIKE ? OR transcripcion LIKE ? OR acuerdos LIKE ?
        ORDER BY id DESC
    """, (q, q, q, q, q))
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    conn.close()
    return result

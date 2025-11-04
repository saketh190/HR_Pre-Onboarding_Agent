import sqlite3
import os
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "employees.db")

def init_db() -> None:
    """Create the employees DB and table with only the requested 5 columns."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT,
        joined TEXT DEFAULT 'No'
    )
    """)
    conn.commit()
    conn.close()

def add_employee(email: str, name: str, role: str, joined: bool = False) -> int:
    """Insert an employee and return the new id. joined=True -> 'Yes' else 'No'."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    joined_val = "Yes" if joined else "No"
    c.execute("""
        INSERT INTO employees (email, name, role, joined)
        VALUES (?, ?, ?, ?)
    """, (email, name, role, joined_val))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id

def get_all_employees() -> List[Dict]:
    """Return all employees as list of dicts containing only the 5 columns."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, email, name, role, joined FROM employees ORDER BY id")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    print(f"Initialized DB at: {DB_PATH}")
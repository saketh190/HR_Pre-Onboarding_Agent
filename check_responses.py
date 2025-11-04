import sqlite3

DB_FILE = "candidates.db"

def init_db():
    """Initialize the database with all status columns"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS candidates(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        role TEXT,
        offer_sent TEXT DEFAULT 'No',
        accepted TEXT DEFAULT 'No',
        document_link_sent TEXT DEFAULT 'No',
        documents_verified TEXT DEFAULT 'No',
        tickets_generated TEXT DEFAULT 'No',
        policy_welcome_sent TEXT DEFAULT 'No'
    )
    ''')
    conn.commit()
    conn.close()

def add_candidate(name, email, role):
    """Add a new candidate"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO candidates (name, email, role) VALUES (?, ?, ?)",
              (name, email, role))
    conn.commit()
    conn.close()

def get_all_candidates():
    """Fetch all candidates with all statuses"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM candidates")
    rows = c.fetchall()
    conn.close()
    return rows


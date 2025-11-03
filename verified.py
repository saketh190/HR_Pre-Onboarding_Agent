import sqlite3

# Existing DB path
DB_PATH = "candidates.db"

# ✅ Mark candidate’s documents as verified
def mark_documents_verified(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        UPDATE candidates 
        SET documents_verified = 'Yes'
        WHERE email = ?
    """, (email,))

    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    test_email = "srsaketh1901@gmail.com"
    mark_documents_verified(test_email)
    print(f"Marked documents as verified for {test_email}")

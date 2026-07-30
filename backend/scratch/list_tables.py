import sqlite3

def list_tables():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for r in cursor.fetchall():
        print(r)
    conn.close()

if __name__ == "__main__":
    list_tables()

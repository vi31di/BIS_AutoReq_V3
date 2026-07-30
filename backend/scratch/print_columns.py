import sqlite3

def print_columns():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(resolution_audit_mismatches)")
    for col in cursor.fetchall():
        print(col)
    conn.close()

if __name__ == "__main__":
    print_columns()

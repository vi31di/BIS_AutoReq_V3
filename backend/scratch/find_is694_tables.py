import sqlite3

def find_is694_tables():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_address, caption_text, table_type 
        FROM tables_meta 
        WHERE document_address = 'IS694-2010'
    """)
    for r in cursor.fetchall():
        print(r)
    conn.close()

if __name__ == "__main__":
    find_is694_tables()

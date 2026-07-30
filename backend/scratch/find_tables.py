import sqlite3

def find_tables():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT table_address, caption_text, table_type, facets FROM tables_meta")
    for r in cursor.fetchall():
        print(f"Address: {r[0]} | Type: {r[2]} | Facets: {r[3]} | Caption: {r[1]}")
        
    conn.close()

if __name__ == "__main__":
    find_tables()

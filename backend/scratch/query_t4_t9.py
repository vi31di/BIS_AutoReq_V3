import sqlite3

def test_query():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    
    for table in ["IS5831-1984_T4", "IS5831-1984_T5", "IS5831-1984_T6", "IS5831-1984_T7", "IS5831-1984_T8", "IS5831-1984_T9"]:
        print(f"\n================ TABLE {table} ================")
        cursor.execute("SELECT DISTINCT col_label FROM table_cells WHERE table_address = ?", (table,))
        cols = [r[0] for r in cursor.fetchall()]
        print("Columns:", cols)
        
        cursor.execute("SELECT DISTINCT row_label FROM table_cells WHERE table_address = ?", (table,))
        rows = [r[0] for r in cursor.fetchall()]
        print("Rows:", rows)
        
        cursor.execute("SELECT cell_address, row_label, col_label, value FROM table_cells WHERE table_address = ? LIMIT 5", (table,))
        for r in cursor.fetchall():
            print(f"  {r[0]}: Row='{r[1]}', Col='{r[2]}', Val='{r[3]}'")
            
    conn.close()

if __name__ == "__main__":
    test_query()

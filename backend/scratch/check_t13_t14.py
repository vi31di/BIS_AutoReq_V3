import sqlite3

def check_t13_t14():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    
    for table in ["IS694-2010_T12", "IS694-2010_T13", "IS694-2010_T14", "IS694-2010_T15"]:
        print(f"\n================ TABLE {table} ================")
        cursor.execute("SELECT cell_address, row_label, col_label, value FROM table_cells WHERE table_address = ? LIMIT 15", (table,))
        for r in cursor.fetchall():
            print(f"Cell: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
            
    conn.close()

if __name__ == "__main__":
    check_t13_t14()

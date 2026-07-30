import sqlite3

def check_t11_cells():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cell_address, row_label, col_label, value 
        FROM table_cells 
        WHERE table_address = 'IS694-2010_T11'
        ORDER BY cell_address
        LIMIT 40
    """)
    for r in cursor.fetchall():
        print(f"Cell: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
    conn.close()

if __name__ == "__main__":
    check_t11_cells()

import sqlite3

def print_t7_t8_cells():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    for t_addr in ["IS694-2010_T7", "IS694-2010_T8"]:
        print(f"\n=== Cells for {t_addr} ===")
        cursor.execute("""
            SELECT cell_address, row_label, col_label, value 
            FROM table_cells 
            WHERE table_address = ?
        """, (t_addr,))
        for r in cursor.fetchall():
            print(f"Addr: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
    conn.close()

if __name__ == "__main__":
    print_t7_t8_cells()

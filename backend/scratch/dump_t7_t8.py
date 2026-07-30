import sqlite3

def dump_all_cells(table_name):
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    print(f"\n================ DUMPING CELLS FOR {table_name} ================")
    cursor.execute("""
        SELECT cell_address, row_label, col_label, value 
        FROM table_cells 
        WHERE table_address = ?
        ORDER BY cell_address
    """, (table_name,))
    for r in cursor.fetchall():
        print(f"Address: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
    conn.close()

if __name__ == "__main__":
    dump_all_cells("IS5831-1984_T7")
    dump_all_cells("IS5831-1984_T8")

import sqlite3

def print_t1_t4():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    for t_addr in ["IS8130-1984_T1", "IS8130-1984_T2", "IS8130-1984_T3", "IS8130-1984_T4"]:
        cursor.execute("SELECT caption_text, table_type, facets FROM tables_meta WHERE table_address = ?", (t_addr,))
        meta = cursor.fetchone()
        print(f"\nTable: {t_addr} | Meta: {meta}")
        
        cursor.execute("SELECT cell_address, row_label, col_label, value FROM table_cells WHERE table_address = ? LIMIT 10", (t_addr,))
        print("  Cells:")
        for r in cursor.fetchall():
            print(f"    Addr: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
    conn.close()

if __name__ == "__main__":
    print_t1_t4()

import sqlite3

def dump_t5_t8():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    for t_addr in ["IS5831-1984_T5", "IS5831-1984_T8"]:
        print(f"\n=== Cells for {t_addr} ===")
        cursor.execute("SELECT cell_address, row_label, col_label, value FROM table_cells WHERE table_address = ?", (t_addr,))
        rows = cursor.fetchall()
        print(f"Total cells: {len(rows)}")
        for r in rows[:15]:
            print(f"Addr: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
    conn.close()

if __name__ == "__main__":
    dump_t5_t8()

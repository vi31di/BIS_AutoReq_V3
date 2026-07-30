import sqlite3

def print_t11_t15():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    for t_addr in ["IS694-2010_T11", "IS694-2010_T12", "IS694-2010_T13", "IS694-2010_T15"]:
        print(f"\n=== Cells for {t_addr} ===")
        cursor.execute("SELECT cell_address, row_label, col_label, value FROM table_cells WHERE table_address = ?", (t_addr,))
        rows = cursor.fetchall()
        print(f"Total cells: {len(rows)}")
        for r in rows[:10]:
            print(f"Addr: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
    conn.close()

if __name__ == "__main__":
    print_t11_t15()

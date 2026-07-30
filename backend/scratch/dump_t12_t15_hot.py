import sqlite3

def dump_t12_t15_hot():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    for t_addr in ["IS5831-1984_T12", "IS5831-1984_T15"]:
        print(f"\n=== Cells for {t_addr} ===")
        cursor.execute("SELECT cell_address, row_label, col_label, value FROM table_cells WHERE table_address = ?", (t_addr,))
        for r in cursor.fetchall():
            if any(kw in str(r).lower() for kw in ["deformation", "heat", "shock", "stability", "hot", "150", "80"]):
                print(f"Addr: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
    conn.close()

if __name__ == "__main__":
    dump_t12_t15_hot()

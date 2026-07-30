import sqlite3

def inspect_t13_1_5():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cell_address, row_label, col_label, value 
        FROM table_cells 
        WHERE table_address = 'IS694-2010_T13'
          AND row_label IN (
              SELECT row_label FROM table_cells 
              WHERE table_address = 'IS694-2010_T13' AND value = '1.5'
          )
    """)
    for r in cursor.fetchall():
        print(f"Addr: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
    conn.close()

if __name__ == "__main__":
    inspect_t13_1_5()

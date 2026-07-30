import sqlite3

def find_test_rows():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cell_address, row_label, col_label, value 
        FROM table_cells 
        WHERE (table_address = 'IS694-2010_T7' OR table_address = 'IS694-2010_T8')
          AND (row_label LIKE '%wrapping%' OR row_label LIKE '%annealing%' OR row_label LIKE '%tensile%' OR row_label LIKE '%spark%')
    """)
    for r in cursor.fetchall():
        print(f"Addr: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
    conn.close()

if __name__ == "__main__":
    find_test_rows()

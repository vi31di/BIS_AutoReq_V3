import sqlite3

def print_r10_cells():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cell_address, row_label, col_label, value 
        FROM table_cells 
        WHERE table_address = 'IS5831-1984_T5' 
          AND cell_address LIKE '%_R10_%'
    """)
    for r in cursor.fetchall():
        print(r)
    conn.close()

if __name__ == "__main__":
    print_r10_cells()

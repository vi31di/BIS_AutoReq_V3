import sqlite3

def print_rows():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cell_address, row_label, col_label, value 
        FROM table_cells 
        WHERE table_address = 'IS694-2010_T7' 
          AND cell_address LIKE '%_R12_%'
    """)
    for r in cursor.fetchall():
        print(r)
    conn.close()

if __name__ == "__main__":
    print_rows()

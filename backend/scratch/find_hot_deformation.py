import sqlite3

def find_hot_deformation_temperatures():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cell_address, row_label, col_label, value 
        FROM table_cells 
        WHERE table_address LIKE 'IS5831-1984_T%'
          AND (row_label LIKE '%deformation%' OR row_label LIKE '%Deformation%')
    """)
    for r in cursor.fetchall():
        print(r)
    conn.close()

if __name__ == "__main__":
    find_hot_deformation_temperatures()

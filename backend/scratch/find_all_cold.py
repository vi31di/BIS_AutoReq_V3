import sqlite3

def find_all_cold():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cell_address, row_label, col_label, value 
        FROM table_cells 
        WHERE table_address LIKE 'IS5831-1984_T%'
          AND (row_label LIKE '%Cold%' OR value LIKE '%-15%' OR value LIKE '%-5%' OR value LIKE '%-5°C%' OR value LIKE '%-15°C%')
    """)
    for r in cursor.fetchall():
        print(r)
    conn.close()

if __name__ == "__main__":
    find_all_cold()

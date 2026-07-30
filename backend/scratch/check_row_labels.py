import sqlite3

def check_row_labels():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT row_label 
        FROM table_cells tc
        JOIN tables_meta tm ON tc.table_address = tm.table_address
        WHERE tm.table_type = 'reference_index'
    """)
    rows = [r[0] for r in cursor.fetchall()]
    print("Row labels in reference_index tables:")
    for r in sorted(rows):
        print(f" - {r}")
        
    conn.close()

if __name__ == "__main__":
    check_row_labels()

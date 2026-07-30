import sqlite3

def check_all_classes():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT class_cell.value, class_cell.table_address
        FROM table_cells class_cell
        WHERE class_cell.table_address LIKE 'IS694-2010_T%'
          AND class_cell.col_label LIKE '%Class%'
    """)
    rows = cursor.fetchall()
    print("Class values in IS 694 tables:")
    for r in sorted(rows):
        print(f" - Value: '{r[0]}' in Table: {r[1]}")
        
    conn.close()

if __name__ == "__main__":
    check_all_classes()

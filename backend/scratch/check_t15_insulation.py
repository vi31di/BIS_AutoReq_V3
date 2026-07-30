import sqlite3

def check_t15_insulation():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT area_cell.value, thick_cell.value
        FROM table_cells area_cell
        JOIN table_cells thick_cell ON area_cell.table_address = thick_cell.table_address AND area_cell.row_label = thick_cell.row_label
        WHERE area_cell.table_address = 'IS694-2010_T15'
          AND area_cell.col_label LIKE '%Area%'
          AND thick_cell.col_label LIKE '%Thickness of Insulation%'
    """)
    for r in cursor.fetchall():
        print(f"T15 Insulation Thickness: Size={r[0]} => Thickness={r[1]}")
    conn.close()

if __name__ == "__main__":
    check_t15_insulation()

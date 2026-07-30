import sqlite3

def check_all_thickness_cols():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT col_label, table_address
        FROM table_cells
        WHERE table_address LIKE 'IS694-2010_T%'
          AND col_label LIKE '%Thickness%'
    """)
    for r in cursor.fetchall():
        # count how many rows are in this table
        cursor.execute("SELECT count(*) FROM table_cells WHERE table_address = ?", (r[1],))
        cnt = cursor.fetchone()[0]
        print(f"Table: {r[1]} (cells: {cnt}) | Col: '{r[0]}'")
    conn.close()

if __name__ == "__main__":
    check_all_thickness_cols()

import sqlite3

def find_ageing_cols():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT table_address, col_label FROM table_cells WHERE col_label LIKE '%ageing%' OR col_label LIKE '%agcing%'")
    for r in cursor.fetchall():
        print(f"Table: {r[0]} | Col: '{r[1]}'")
    conn.close()

if __name__ == "__main__":
    find_ageing_cols()

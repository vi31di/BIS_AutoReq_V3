import sqlite3

def find_thickness_cells():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    print("=== Table Cells matching 'Thickness' ===")
    cursor.execute("""
        SELECT cell_address, table_address, row_label, col_label, value 
        FROM table_cells 
        WHERE row_label LIKE '%thickness%' 
           OR col_label LIKE '%thickness%'
        LIMIT 40
    """)
    for r in cursor.fetchall():
        print(f"Address: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
        
    print("\n=== Tables with 'thickness' in caption ===")
    cursor.execute("SELECT table_address, caption_text, table_type FROM tables_meta WHERE caption_text LIKE '%thickness%'")
    for r in cursor.fetchall():
        print(f"Table: {r[0]} | Type: {r[2]} | Caption: {r[1]}")

    conn.close()

if __name__ == "__main__":
    find_thickness_cells()

import sqlite3

def check_thickness_tables():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    
    # We want to check which tables in IS 694 have thickness of insulation.
    # Let's search tables_meta for IS694.
    cursor.execute("""
        SELECT table_address, caption_text, table_type, facets 
        FROM tables_meta 
        WHERE document_address = 'IS694-2010'
    """)
    tables = cursor.fetchall()
    print("Tables in IS 694:")
    for t in tables:
        # Check if the table has cells
        cursor.execute("SELECT count(*) FROM table_cells WHERE table_address = ?", (t[0],))
        count = cursor.fetchone()[0]
        print(f"Address: {t[0]} | Cells: {count} | Type: {t[2]} | Caption: {t[1]} | Facets: {t[3]}")
        
        # Let's inspect unique row labels and column labels for some of these tables to find thickness
        if count > 0 and t[0] in ["IS694-2010_T3", "IS694-2010_T4", "IS694-2010_T5", "IS694-2010_T6", "IS694-2010_T11", "IS694-2010_T12"]:
            cursor.execute("SELECT DISTINCT col_label FROM table_cells WHERE table_address = ? LIMIT 5", (t[0],))
            cols = [r[0] for r in cursor.fetchall()]
            cursor.execute("SELECT DISTINCT row_label FROM table_cells WHERE table_address = ? LIMIT 5", (t[0],))
            rows = [r[0] for r in cursor.fetchall()]
            print(f"  Col Labels: {cols}")
            print(f"  Row Labels: {rows}")
            
    conn.close()

if __name__ == "__main__":
    check_thickness_tables()

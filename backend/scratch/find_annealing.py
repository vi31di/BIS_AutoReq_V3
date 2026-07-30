import sqlite3

def find_annealing():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    
    print("=== Table Cells matching 'annealing' ===")
    cursor.execute("""
        SELECT cell_address, table_address, row_label, col_label, value 
        FROM table_cells 
        WHERE row_label LIKE '%annealing%' OR col_label LIKE '%annealing%' OR value LIKE '%annealing%'
        LIMIT 10
    """)
    for r in cursor.fetchall():
        print(r)
        
    print("\n=== Table Cells matching '6.1.2.1' or '6.2.3' ===")
    cursor.execute("""
        SELECT cell_address, table_address, row_label, col_label, value 
        FROM table_cells 
        WHERE cell_address LIKE '%6.1.2.1%' OR cell_address LIKE '%6.2.3%'
           OR row_label LIKE '%6.1.2.1%' OR row_label LIKE '%6.2.3%'
        LIMIT 10
    """)
    for r in cursor.fetchall():
        print(r)
        
    print("\n=== Table Meta matching 'IS 8130' ===")
    cursor.execute("""
        SELECT table_address, caption_text, table_type, facets 
        FROM tables_meta 
        WHERE table_address LIKE '%8130%' OR caption_text LIKE '%8130%'
        LIMIT 10
    """)
    for r in cursor.fetchall():
        print(r)
        
    conn.close()

if __name__ == "__main__":
    find_annealing()

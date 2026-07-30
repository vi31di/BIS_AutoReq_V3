import sqlite3

def print_cold_cells():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    
    # Query Table 11 & Table 13 for cold bend / cold impact
    cursor.execute("""
        SELECT cell_address, row_label, col_label, value 
        FROM table_cells 
        WHERE (table_address LIKE 'IS5831-1984_T11%' OR table_address LIKE 'IS5831-1984_T13%')
          AND (row_label LIKE '%Cold%' OR col_label LIKE '%Cold%' OR value LIKE '%-15%' OR value LIKE '%-5%')
    """)
    print("=== PVC Insulation (Table 1) Cold Cells ===")
    for r in cursor.fetchall():
        print(f"Addr: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
        
    # Query Table 14 & Table 16 for PVC Sheath (Table 2) cold bend / cold impact
    cursor.execute("""
        SELECT cell_address, row_label, col_label, value 
        FROM table_cells 
        WHERE (table_address LIKE 'IS5831-1984_T14%' OR table_address LIKE 'IS5831-1984_T16%')
          AND (row_label LIKE '%Cold%' OR col_label LIKE '%Cold%' OR value LIKE '%-15%' OR value LIKE '%-5%')
    """)
    print("\n=== PVC Sheath (Table 2) Cold Cells ===")
    for r in cursor.fetchall():
        print(f"Addr: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Val: '{r[3]}'")
        
    conn.close()

if __name__ == "__main__":
    print_cold_cells()

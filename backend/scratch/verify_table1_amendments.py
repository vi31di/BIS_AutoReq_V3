import sqlite3
import json

def verify_table1_amendments():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    
    print("======================================================================")
    print("TABLE 1 AMENDMENT 1:2012 VERIFICATION & DIFF REPORT")
    print("======================================================================")
    
    # Let's check specific rows and columns affected by the Amendment
    # 1. Sl No. (i), (f), col 4 (corresponds to row 11 in T7, col 4 or C2)
    # 2. Sl No. (i), (g), col 4 (corresponds to row 12 in T7, col 4 or C2)
    
    query = """
        SELECT cell_address, row_label, col_label, value 
        FROM table_cells 
        WHERE cell_address IN (
            'IS694-2010_T7_R11_C2', 
            'IS694-2010_T7_R12_C2'
        )
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Direct mappings from amendment text:
    # [Page 7, Table 1, Sl No. (i), (f), col 4] — Substitute 'IS 5831' for 'IS 8130'
    # [Page 7, Table 1, Sl No. (i), (g), col 4] — Substitute 'IS 5831' for 'IS 8130'
    
    expected_changes = {
        'IS694-2010_T7_R11_C2': {
            'description': 'Sl No. (i), (f) (Tensile strength and elongation at break of insulation & sheath)',
            'original_base_value': 'IS 8130',
            'amended_value': 'IS 5831'
        },
        'IS694-2010_T7_R12_C2': {
            'description': 'Sl No. (i), (g) (Loss of mass test)',
            'original_base_value': 'IS 8130',
            'amended_value': 'IS 5831'
        }
    }
    
    for cell_address, row_label, col_label, current_val in rows:
        change_info = expected_changes.get(cell_address)
        if change_info:
            orig = change_info['original_base_value']
            amended = change_info['amended_value']
            desc = change_info['description']
            
            print(f"\nCell Address: {cell_address}")
            print(f"Description:  {desc}")
            print(f"Row Label:    {row_label}")
            print(f"Col Label:    {col_label}")
            print(f"Base Value:   '{orig}' (Originally OCR'd standard)")
            print(f"Current Db:   '{current_val}'")
            print(f"Amended To:   '{amended}'")
            
            if current_val == amended:
                print(">>> STATUS: [FLAGGED] The database has been updated with the Amendment value (superseding base-table value).")
            else:
                print(">>> STATUS: [WARNING] The database still contains the base-table value or mismatch.")
                
    # Also scan all of Table 1 for standard references to print a general summary
    print("\n----------------------------------------------------------------------")
    print("Table 1 (T7 & T8) Cells with Standard References Summary:")
    print("----------------------------------------------------------------------")
    cursor.execute("""
        SELECT cell_address, row_label, value 
        FROM table_cells 
        WHERE (table_address = 'IS694-2010_T7' OR table_address = 'IS694-2010_T8')
          AND (value LIKE '%IS%' OR value LIKE '%10810%')
        ORDER BY cell_address
    """)
    for r in cursor.fetchall():
        print(f"Cell: {r[0]} | Row: {r[1][:50]:<50} | Value: {r[2]}")
        
    conn.close()

if __name__ == "__main__":
    verify_table1_amendments()

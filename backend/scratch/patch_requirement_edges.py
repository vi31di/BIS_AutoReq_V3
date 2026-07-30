import sqlite3
import json

def patch_edges():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    
    # Define edge pairs to insert: (source_address, target_address, target_facets_dict, edge_type)
    edge_pairs = [
        # spark_test
        ("IS694-2010_T7_R4_C2", "IS694-2010_S10.3", None, "requirement"),
        ("IS694-2010_T7_R4_C3", "IS10810-1984_S44", None, "method"),
        
        ("IS694-2010_T7_R13_C2", "IS694-2010_S10.3", None, "requirement"),
        ("IS694-2010_T7_R13_C3", "IS10810-1984_S44", None, "method"),
        
        ("IS694-2010_T8_R1_C3", "IS694-2010_S10.3", None, "requirement"),
        ("IS694-2010_T8_R1_C4", "IS10810-1984_S44", None, "method"),
        
        # flammability_test
        ("IS694-2010_T8_R4_C3", "IS694-2010_S10.4", None, "requirement"),
        ("IS694-2010_T8_R4_C4", "IS10810-1984_S53", None, "method"),
        
        # oxygen_index_test
        ("IS694-2010_T7_R52_C2", "IS694-2010_S10.5", None, "requirement"),
        ("IS694-2010_T7_R52_C3", "IS10810-1984_S58", None, "method"),
        
        # halogen_acid_gas_test
        ("IS694-2010_T7_R54_C2", "IS694-2010_S10.6", None, "requirement"),
        ("IS694-2010_T7_R54_C3", "IS10810-1984_S59", None, "method"),
        
        # smoke_density_test (NULL status pattern)
        ("IS694-2010_T7_R55_C2", "NULL", {"status": "under_preparation", "source": "IS694-2010_S10.8"}, "requirement"),
        ("IS694-2010_T7_R55_C3", "NULL", {"status": "under_preparation", "source": "IS694-2010_S10.8"}, "method"),
        
        # annealing_test_copper
        ("IS694-2010_T7_R6_C2", "IS8130-1984_S6.1.2.1", None, "requirement"),
        ("IS694-2010_T7_R6_C3", "IS10810-1984_S1", None, "method"),
        
        ("IS694-2010_T7_R23_C2", "IS8130-1984_S6.1.2.1", None, "requirement"),
        ("IS694-2010_T7_R23_C3", "IS10810-1984_S1", None, "method"),
        
        # annealing_test_aluminium (shaped solid vs welding cable)
        ("IS694-2010_T7_R7_C2", "IS8130-1984_S6.2.3", {"shaped_solid": "25% min", "welding_cable_wire": "12% min"}, "requirement"),
        ("IS694-2010_T7_R7_C3", "IS10810-1984_S1", None, "method"),
        
        # wrapping_test
        ("IS694-2010_T7_R8_C2", "IS8130-1984_S6.2.2", {"pass_fail": "shall not break"}, "requirement"),
        ("IS694-2010_T7_R8_C3", "IS10810-1984_S3", None, "method"),
        
        ("IS694-2010_T7_R25_C2", "IS8130-1984_S6.2.2", {"pass_fail": "shall not break"}, "requirement"),
        ("IS694-2010_T7_R25_C3", "IS10810-1984_S3", None, "method")
    ]
    
    # Delete conflicting edges first
    sources = set(p[0] for p in edge_pairs)
    for src in sources:
        cursor.execute("DELETE FROM edges WHERE source_address = ? AND edge_type IN ('requirement', 'method')", (src,))
    
    # Insert new edges
    inserted_count = 0
    for src_addr, tgt_addr, facets, edge_type in edge_pairs:
        facets_json = json.dumps(facets) if facets else None
        cursor.execute("""
            INSERT INTO edges (source_address, target_address, target_facets, edge_type)
            VALUES (?, ?, ?, ?)
        """, (src_addr, tgt_addr, facets_json, edge_type))
        inserted_count += 1
        
    # Update Table 1 R12_C2 cell value to 'IS 5831' to correct base-table reference per Amendment 1:2012
    cursor.execute("""
        UPDATE table_cells 
        SET value = 'IS 5831' 
        WHERE cell_address = 'IS694-2010_T7_R12_C2'
    """)
    print("Table cell IS694-2010_T7_R12_C2 successfully updated to 'IS 5831'.")
        
    conn.commit()
    conn.close()
    print(f"Edges patched: deleted existing and inserted {inserted_count} requirement/method edges.")

if __name__ == "__main__":
    patch_edges()

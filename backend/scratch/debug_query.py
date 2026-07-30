import sqlite3

def debug_query():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    
    print("=== All requirement edges in DB ===")
    cursor.execute("SELECT source_address, target_address, edge_type FROM edges WHERE edge_type = 'requirement'")
    reqs = cursor.fetchall()
    print(f"Total requirement edges: {len(reqs)}")
    for r in reqs[:5]:
        print(r)
        
    print("\n=== Check if source addresses exist in table_cells ===")
    if reqs:
        sample_src = reqs[0][0]
        cursor.execute("SELECT cell_address, value FROM table_cells WHERE cell_address = ?", (sample_src,))
        cell = cursor.fetchone()
        print(f"Sample source '{sample_src}' in table_cells: {cell}")
        
    print("\n=== All method edges in DB ===")
    cursor.execute("SELECT source_address, target_address, edge_type FROM edges WHERE edge_type = 'method'")
    meths = cursor.fetchall()
    print(f"Total method edges: {len(meths)}")
    for r in meths[:5]:
        print(r)
        
    print("\n=== Intersection test ===")
    cursor.execute("""
        SELECT e1.source_address, e1.target_address, e2.target_address
        FROM edges e1
        JOIN edges e2 ON e1.source_address = e2.source_address
        WHERE e1.edge_type = 'requirement' AND e2.edge_type = 'method'
    """)
    rows = cursor.fetchall()
    print(f"Intersection count: {len(rows)}")
    for r in rows[:5]:
        print(r)
        
    conn.close()

if __name__ == "__main__":
    debug_query()

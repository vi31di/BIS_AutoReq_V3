import sqlite3

def find_edges_for_cells():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.edge_id, e.source_address, e.target_address, e.edge_type 
        FROM edges e 
        WHERE e.source_address LIKE 'IS694-2010_T7%' 
           OR e.source_address LIKE 'IS694-2010_T8%'
    """)
    for r in cursor.fetchall():
        print(r)
    conn.close()

if __name__ == "__main__":
    find_edges_for_cells()

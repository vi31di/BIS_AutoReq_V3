import sqlite3

def inspect_edges():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(edges)")
    for col in cursor.fetchall():
        print(col)
        
    print("\n=== Sample Edges ===")
    cursor.execute("SELECT source_address, target_address, edge_type FROM edges LIMIT 30")
    for r in cursor.fetchall():
        print(r)
        
    print("\n=== Distinct Edge Types ===")
    cursor.execute("SELECT DISTINCT edge_type FROM edges")
    for r in cursor.fetchall():
        print(r)
        
    conn.close()

if __name__ == "__main__":
    inspect_edges()

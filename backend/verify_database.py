import sqlite3
import json

db_path = "bis_database.db"

def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== Database Table Counts ===")
    tables = ["is_documents", "clauses_meta", "tables_meta", "table_cells", "edges"]
    for t in tables:
        cursor.execute(f"SELECT count(*) FROM {t}")
        count = cursor.fetchone()[0]
        print(f"Table '{t}': {count} rows")
        
    print("\n=== Sample Document Addresses ===")
    cursor.execute("SELECT document_address, is_number, revision_label FROM is_documents")
    for r in cursor.fetchall():
        print(f" - {r[0]} ({r[1]} version {r[2]})")
        
    print("\n=== Sample Clauses ===")
    cursor.execute("SELECT clause_address, heading_text, section_number, length(body_text) FROM clauses_meta LIMIT 5")
    for r in cursor.fetchall():
        print(f" - Address: {r[0]} | Heading: {r[1]} | Section: {r[2]} | Body Length: {r[3]} chars")
        
    print("\n=== Sample Tables ===")
    cursor.execute("SELECT table_address, table_type, facets, caption_text FROM tables_meta LIMIT 5")
    for r in cursor.fetchall():
        print(f" - Address: {r[0]} | Type: {r[1]} | Facets: {r[2]} | Caption: {r[3]}")
        
    print("\n=== Sample Cells ===")
    cursor.execute("SELECT cell_address, row_label, col_label, value FROM table_cells LIMIT 10")
    for r in cursor.fetchall():
        print(f" - Cell: {r[0]} | Row: '{r[1]}' | Col: '{r[2]}' | Value: '{r[3]}'")
        
    print("\n=== Reference Edges ===")
    cursor.execute("SELECT count(*), edge_type FROM edges GROUP BY edge_type")
    for r in cursor.fetchall():
        print(f" - Edge Type: '{r[1]}' | Count: {r[0]}")
        
    print("\n=== Sample Edges ===")
    cursor.execute("SELECT source_address, target_address, edge_type FROM edges LIMIT 10")
    for r in cursor.fetchall():
        print(f" - Source: {r[0]} -> Target: {r[1]} ({r[2]})")
        
    conn.close()

if __name__ == "__main__":
    main()

import sqlite3

def print_mismatches():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT test_name, category, size_mm2, wire_class, 
               expected_value, actual_value, expected_path, actual_path
        FROM resolution_audit_mismatches
        WHERE run_id = 26
        LIMIT 10
    """)
    for r in cursor.fetchall():
        print(f"\nQuery: Test='{r[0]}' | Cat='{r[1]}' | Size={r[2]} | Class='{r[3]}'")
        print(f"  Old Value: {r[4]}")
        print(f"  New Value: {r[5]}")
        print(f"  Old Path: {r[6]}")
        print(f"  New Path: {r[7]}")
    conn.close()

if __name__ == "__main__":
    print_mismatches()

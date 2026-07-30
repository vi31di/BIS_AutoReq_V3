import sqlite3
import json

def print_mismatches():
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT query, production_result, oracle_result, reason_code 
        FROM resolution_audit_mismatches
        WHERE run_id = 26
        LIMIT 10
    """)
    for r in cursor.fetchall():
        payload = json.loads(r[0])
        print(f"\nQuery: {payload}")
        print(f"  Old Engine (Production): {r[1]}")
        print(f"  New Engine (Oracle): {r[2]}")
        print(f"  Reason Code: {r[3]}")
    conn.close()

if __name__ == "__main__":
    print_mismatches()

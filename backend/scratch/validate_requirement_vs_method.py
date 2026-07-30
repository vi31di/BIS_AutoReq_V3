import sqlite3
import json
import asyncio
from api.db import DBConnection, init_db_connection
from api.resolve.resolver import resolve_lookup

async def main():
    print("======================================================================")
    print("REQUIREMENT VS METHOD RESOLUTION VALIDATION REPORT")
    print("======================================================================")
    
    conn = sqlite3.connect("bis_database.db")
    cursor = conn.cursor()
    
    # 1. Fetch requirement and method edges
    cursor.execute("""
        SELECT source_address, target_address, edge_type 
        FROM edges 
        WHERE edge_type IN ('requirement', 'method')
    """)
    edges = cursor.fetchall()
    
    rows_dict = {}
    for src_addr, tgt_addr, edge_type in edges:
        row_addr = src_addr.rsplit("_", 1)[0]
        if row_addr not in rows_dict:
            rows_dict[row_addr] = {}
        rows_dict[row_addr][edge_type] = tgt_addr
        
    print(f"Found {len(rows_dict)} test rows with requirement or method edges.\n")
    
    mismatches = 0
    passed = 0
    
    for row_addr, targets in rows_dict.items():
        req_target = targets.get("requirement")
        meth_target = targets.get("method")
        
        if not req_target or not meth_target:
            continue
            
        # Fetch row label
        cursor.execute("SELECT value FROM table_cells WHERE cell_address = ?", (f"{row_addr}_C0",))
        row_val = cursor.fetchone()
        test_name = row_val[0] if row_val else row_addr
        
        # Extract document/standard prefixes (e.g. 'IS694', 'IS8130', 'IS10810')
        req_doc = req_target.split("_")[0] if req_target else "NULL"
        meth_doc = meth_target.split("_")[0] if meth_target else "NULL"
        
        print(f"Test Row:    {row_addr}")
        print(f"Test Name:   {test_name}")
        print(f"  - REQUIREMENT: {req_target} (Standard: {req_doc})")
        print(f"  - METHOD:      {meth_target} (Standard: {meth_doc})")
        
        if req_doc == meth_doc and req_doc != "NULL":
            print(f">>> VALIDATION: [FAILED] REQUIREMENT and METHOD point to the same standard: {req_doc} (Not fully decomposed!)")
            mismatches += 1
        else:
            print(">>> VALIDATION: [PASSED] REQUIREMENT and METHOD point to different standards.")
            passed += 1
        print("-" * 70)
        
    print(f"\nEdge separation summary: {passed} passed, {mismatches} failed.")
    
    # 2. Let's verify that we can resolve the correct values of these tests via resolve_lookup
    print("\n======================================================================")
    print("VERIFYING RESOLUTION CORRECTNESS OF RESOLVED PATH VALUES")
    print("======================================================================")
    
    # Setup database connection context
    await init_db_connection()
    async with DBConnection() as db:
        test_queries = [
            {
                "description": "Spark test (up to 1.0mm thickness)",
                "payload": {
                    "test_name": "High voltage test or Spark test",
                    "size_mm2": 1.5  # maps to 0.7mm insulation thickness
                },
                "expected_substrings": ["6 kV (rms)"]
            },
            {
                "description": "Flammability test",
                "payload": {
                    "test_name": "Flammability test"
                },
                "expected_substrings": ["shall not exceed 60 seconds", "at least 50 mm"]
            },
            {
                "description": "Oxygen index test",
                "payload": {
                    "test_name": "Oxygen index test",
                    "category": "FR"
                },
                "expected_substrings": ["Min 29"]
            },
            {
                "description": "Halogen acid gas test",
                "payload": {
                    "test_name": "Test for halogen acid gas evaluation",
                    "category": "FR-LSH"
                },
                "expected_substrings": ["Max 20% by weight"]
            },
            {
                "description": "Smoke density test (Null status check)",
                "payload": {
                    "test_name": "Test for smoke density rating",
                    "category": "FR-LSH"
                },
                "expected_substrings": ["Under preparation"]
            },
            {
                "description": "Annealing test (Copper, 0.80mm)",
                "payload": {
                    "test_name": "Annealing test (for copper)",
                    "material": "Copper",
                    "size_mm2": 0.80
                },
                "expected_substrings": ["18.0%"]
            },
            {
                "description": "Annealing test (Aluminium)",
                "payload": {
                    "test_name": "Annealing test (for copper)",
                    "material": "Aluminium"
                },
                "expected_substrings": ["25 percent", "12 percent"]
            },
            {
                "description": "Wrapping test",
                "payload": {
                    "test_name": "Wrapping test (for aluminium)"
                },
                "expected_substrings": ["shall not break", "8 turns"]
            }
        ]
        
        failed_resolutions = 0
        for item in test_queries:
            desc = item["description"]
            payload = item["payload"]
            expected = item["expected_substrings"]
            
            print(f"Testing resolution for: {desc}...")
            res = await resolve_lookup(db, payload)
            val = res.get("value", "")
            print(f"  Resolved Value: '{val}'")
            print(f"  Path Taken:     {res.get('resolution_path')}")
            
            all_ok = True
            for substr in expected:
                if substr not in val:
                    all_ok = False
                    print(f"  >>> Error: Expected substring '{substr}' not found in resolved value.")
                    
            if all_ok:
                print("  >>> STATUS: [SUCCESS]")
            else:
                print("  >>> STATUS: [FAILURE]")
                failed_resolutions += 1
            print("-" * 70)
            
        print(f"\nResolution verification summary: {len(test_queries) - failed_resolutions} succeeded, {failed_resolutions} failed.")
        
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())

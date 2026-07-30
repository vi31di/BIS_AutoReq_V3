import asyncio
import json
import sqlite3
from api.db import DBConnection, init_db_connection
from api.resolve.resolver import get_dropdown_options, resolve_lookup

async def verify_options():
    print("Testing dynamic dropdown options...")
    async with DBConnection() as db:
        options = await get_dropdown_options(db)
        print("Dynamic Options retrieved:")
        print(f" - Classes count: {len(options['classes'])} (Sample: {options['classes'][:3]})")
        print(f" - Materials count: {len(options['materials'])} (Sample: {options['materials'][:3]})")
        print(f" - Test Types count: {len(options['test_types'])} (Sample: {options['test_types'][:3]})")
        assert len(options['classes']) > 0
        assert len(options['test_types']) > 0

async def verify_resolution_matrix():
    print("\nTesting B3 Resolution Loop - Conductor Resistance test (Class 5, size 2.5mm²)...")
    payload = {
        "test_name": "Conductor resistance test",
        "is_number": "IS 694",
        "class": "Class 5",
        "size_mm2": 2.5,
        "material": "Plain Copper",
        "category": "Cables for indoor installation"
    }
    async with DBConnection() as db:
        result = await resolve_lookup(db, payload)
        print("Resolution Output:")
        print(" - Value:", result.get("value"))
        print(" - Needs Re-verification:", result.get("needs_reverification"))
        print(" - Resolution Path Hops:")
        for idx, step in enumerate(result.get("resolution_path", [])):
            print(f"    * Step {idx+1}: Address={step['address']} | Type={step['type']}")
            
        assert "7.98" in result.get("value")
        assert result.get("needs_reverification") is False

async def verify_resolution_relational():
    print("\nTesting B3 Resolution Loop - Conductor Resistance test (Class 2, size 1.5mm²)...")
    payload = {
        "test_name": "Conductor resistance test",
        "is_number": "IS 694",
        "class": "Class 2",
        "size_mm2": 1.5,
        "material": "Plain Copper",
        "category": "Cables for indoor installation"
    }
    async with DBConnection() as db:
        result = await resolve_lookup(db, payload)
        print("Resolution Output:")
        print(" - Value:", result.get("value"))
        print(" - Resolution Path Hops:")
        for idx, step in enumerate(result.get("resolution_path", [])):
            print(f"    * Step {idx+1}: Address={step['address']} | Type={step['type']}")
            
        assert "12" in result.get("value")
        assert result.get("needs_reverification") is False

async def verify_supersession_caching():
    print("\nTesting B4 Cache & Version Invalidations...")
    payload = {
        "test_name": "Conductor resistance test",
        "is_number": "IS 694",
        "class": "Class 2",
        "size_mm2": 1.5,
        "material": "Plain Copper",
        "category": "Cables for indoor installation"
    }
    
    async with DBConnection() as db:
        # First lookup (populates cache)
        print(" - Run 1 (Cache Miss)...")
        res1 = await resolve_lookup(db, payload)
        
        # Second lookup (hits cache)
        print(" - Run 2 (Cache Hit)...")
        res2 = await resolve_lookup(db, payload)
        assert res1["value"] == res2["value"]
        
        # Mock supersede IS694-2010 document version
        print(" - Mocking IS694-2010 supersession by newer version IS694-2026...")
        await db.execute("UPDATE is_documents SET is_current = FALSE, superseded_by = 'IS694-2026' WHERE document_address = 'IS694-2010'")
        
        # Third lookup (cache invalid check triggers miss)
        print(" - Run 3 (Post-supersede Invalidation - Cache Miss)...")
        res3 = await resolve_lookup(db, payload)
        # Should now resolve to unverified/re-verification since IS694-2010 is superseded
        print(" - Post-supersede Value:", res3.get("value"))
        assert res3.get("needs_reverification") is True
        
        # Reset database state
        await db.execute("UPDATE is_documents SET is_current = TRUE, superseded_by = NULL WHERE document_address = 'IS694-2010'")

async def main():
    await init_db_connection()
    await verify_options()
    await verify_resolution_matrix()
    await verify_resolution_relational()
    await verify_supersession_caching()
    print("\nAll backend services successfully validated!")

if __name__ == "__main__":
    asyncio.run(main())

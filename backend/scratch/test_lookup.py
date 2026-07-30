import asyncio
import json
from api.db import DBConnection, init_db_connection
from api.resolve.resolver import resolve_lookup

async def test():
    await init_db_connection()
    async with DBConnection() as db:
        # Ageing test
        payload = {
            "test_name": "Ageing in air oven",
            "is_number": "IS 5831",
            "class": "Class 1",
            "size_mm2": 1.5,
            "material": "Plain Copper",
            "category": "Type A",
            "component": "Insulation"
        }
        res = await resolve_lookup(db, payload)
        print("Ageing in air oven:", json.dumps(res, indent=2))
        
        # Loss of mass test
        payload = {
            "test_name": "Loss of mass test",
            "is_number": "IS 5831",
            "class": "Class 1",
            "size_mm2": 1.5,
            "material": "Plain Copper",
            "category": "Type A",
            "component": "Insulation"
        }
        res = await resolve_lookup(db, payload)
        print("Loss of mass test:", json.dumps(res, indent=2))
        
        # Shrinkage test
        payload = {
            "test_name": "Shrinkage test",
            "is_number": "IS 5831",
            "class": "Class 1",
            "size_mm2": 1.5,
            "material": "Plain Copper",
            "category": "Type A",
            "component": "Insulation"
        }
        res = await resolve_lookup(db, payload)
        print("Shrinkage test:", json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(test())

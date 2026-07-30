import asyncio
import json
from api.db import DBConnection, init_db_connection
from api.resolve.resolver import resolve_lookup

async def test():
    await init_db_connection()
    async with DBConnection() as db:
        payload = {
            "test_name": "Insulation resistance test",
            "is_number": "IS 5831",
            "class": "Class 2",
            "size_mm2": 1.5,
            "material": "Plain Copper",
            "category": "Type A",
            "component": "Insulation"
        }
        res = await resolve_lookup(db, payload)
        print("IR Test:", json.dumps(res, indent=2))

if __name__ == "__main__":
    asyncio.run(test())

import asyncio
from api.db import DBConnection, init_db_connection
from api.resolve.resolver import get_dropdown_options

async def main():
    await init_db_connection()
    async with DBConnection() as db:
        options = await get_dropdown_options(db)
        print("Dropdown Options:")
        print(options)

if __name__ == "__main__":
    asyncio.run(main())

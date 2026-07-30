import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/bis_database")
    
    print("=== T4 (PVC Insulation) Distinct Columns ===")
    t4_cols = await conn.fetch("SELECT DISTINCT col_label FROM table_cells WHERE table_address = 'IS5831-1984_T4'")
    for c in t4_cols:
        print(c['col_label'])
        
    print("\n=== T7 (PVC Sheath) Distinct Columns ===")
    t7_cols = await conn.fetch("SELECT DISTINCT col_label FROM table_cells WHERE table_address = 'IS5831-1984_T7'")
    for c in t7_cols:
        print(c['col_label'])

    print("\n=== T4 Row Labels and Values ===")
    t4_rows = await conn.fetch("SELECT row_label, col_label, value FROM table_cells WHERE table_address = 'IS5831-1984_T4' LIMIT 40")
    for r in t4_rows:
        print(f"Row: {r['row_label']} | Col: {r['col_label']} | Val: {r['value']}")

    print("\n=== T7 Row Labels and Values ===")
    t7_rows = await conn.fetch("SELECT row_label, col_label, value FROM table_cells WHERE table_address = 'IS5831-1984_T7' LIMIT 40")
    for r in t7_rows:
        print(f"Row: {r['row_label']} | Col: {r['col_label']} | Val: {r['value']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

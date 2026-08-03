import sqlite3
import json
import asyncio
import asyncpg
import os
import datetime

sqlite_db_path = "bis_database.db"
postgres_dsn = os.environ.get("DATABASE_URL")
if not postgres_dsn or not (postgres_dsn.startswith("postgresql://") or postgres_dsn.startswith("postgres://")):
    print("\n[Error] Invalid or empty DATABASE_URL environment variable.")
    print("Please specify a valid PostgreSQL DSN connection string.")
    print("\nUsage Example:")
    print("  DATABASE_URL=\"postgresql://postgres:password@host:port/database\" PYTHONPATH=. ./.venv/bin/python migrate_to_postgres.py\n")
    import sys
    sys.exit(1)
schema_path = "db/schema.sql"

async def migrate():
    print(f"Reading schema from {schema_path}...")
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    # 1. Connect to Postgres and execute schema
    print("Connecting to PostgreSQL...")
    conn_pg = await asyncpg.connect(postgres_dsn)
    print("Initializing schema and indexes...")
    # Split sql script into individual commands to avoid asyncpg DDL issues
    for command in schema_sql.split(";"):
        cmd_clean = command.strip()
        if cmd_clean:
            try:
                await conn_pg.execute(cmd_clean)
            except Exception as e:
                print(f"Warning: DDL command failed: {cmd_clean[:50]}... -> {e}")
    print("PostgreSQL schema initialization finished.")

    # 2. Connect to SQLite
    conn_sl = sqlite3.connect(sqlite_db_path)
    conn_sl.row_factory = sqlite3.Row
    cursor_sl = conn_sl.cursor()

    tables = ["is_documents", "clauses_meta", "tables_meta", "table_cells", "edges"]

    for table in tables:
        print(f"Migrating table '{table}'...")
        cursor_sl.execute(f"SELECT * FROM {table}")
        rows = cursor_sl.fetchall()
        if not rows:
            print(f"Table '{table}' has no rows to migrate.")
            continue

        columns = list(rows[0].keys())
        col_list = ", ".join(columns)
        
        placeholders = []
        for i, col in enumerate(columns):
            if table == "tables_meta" and col == "facets":
                placeholders.append(f"${i+1}::jsonb")
            elif table == "table_cells" and col == "bbox":
                placeholders.append(f"${i+1}::jsonb")
            elif table == "edges" and col == "target_facets":
                placeholders.append(f"${i+1}::jsonb")
            else:
                placeholders.append(f"${i+1}")
        placeholders_str = ", ".join(placeholders)
        
        insert_sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders_str}) ON CONFLICT DO NOTHING"
        
        data_list = []
        for r in rows:
            row_data = []
            for col in columns:
                val = r[col]
                
                # Parse date strings to datetime.date objects for Postgres DATE columns
                if col in ["valid_from", "valid_to"] and isinstance(val, str) and val:
                    try:
                        val = datetime.date.fromisoformat(val.split(" ")[0])
                    except ValueError:
                        val = None
                
                # Convert SQLite boolean integer to Python bool
                if col == "is_current" and val is not None:
                    val = bool(val)
                        
                row_data.append(val)
            data_list.append(row_data)

        # Execute insert on pg
        try:
            await conn_pg.executemany(insert_sql, data_list)
            print(f"Successfully migrated {len(data_list)} rows to table '{table}'.")
        except Exception as e:
            print(f"Error inserting into table '{table}': {e}")

    conn_sl.close()
    await conn_pg.close()
    print("Migration finished!")

if __name__ == "__main__":
    asyncio.run(migrate())

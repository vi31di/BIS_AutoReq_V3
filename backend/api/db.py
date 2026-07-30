import os
import json
import sqlite3
import asyncio
from typing import Any, List, Dict, Optional

# Database connection details
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///bis_database.db")
IS_POSTGRES = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

# Global variables for connection pools
pg_pool = None

async def init_db_connection():
    """
    Initializes PostgreSQL pool if configured.
    """
    global pg_pool
    if IS_POSTGRES:
        import asyncpg
        pg_pool = await asyncpg.create_pool(DATABASE_URL)
        print("Connected to PostgreSQL pool.")
    else:
        print("Using local SQLite database.")

class DBConnection:
    """
    Unified database connection wrapper supporting both asyncpg (PostgreSQL) and sqlite3.
    """
    def __init__(self):
        self.sqlite_conn = None
        self.pg_conn = None
        
    async def __aenter__(self):
        if IS_POSTGRES:
            global pg_pool
            if pg_pool is None:
                await init_db_connection()
            self.pg_conn = await pg_pool.acquire()
        else:
            # SQLite connection
            db_file = DATABASE_URL.replace("sqlite:///", "")
            # Run blocking sqlite3 connection in thread pool
            loop = asyncio.get_running_loop()
            self.sqlite_conn = await loop.run_in_executor(None, lambda: sqlite3.connect(db_file, check_same_thread=False))
            self.sqlite_conn.row_factory = sqlite3.Row
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if IS_POSTGRES:
            if self.pg_conn:
                global pg_pool
                await pg_pool.release(self.pg_conn)
        else:
            if self.sqlite_conn:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.sqlite_conn.commit)
                await loop.run_in_executor(None, self.sqlite_conn.close)

    async def execute(self, query: str, *args: Any):
        """
        Executes a query (INSERT/UPDATE/DELETE).
        """
        # Convert Postgres placeholder '$1, $2' to SQLite '?' if using SQLite
        if not IS_POSTGRES:
            query = self._to_sqlite_placeholders(query)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self.sqlite_conn.execute(query, args))
        else:
            await self.pg_conn.execute(query, *args)

    async def fetch(self, query: str, *args: Any) -> List[Dict[str, Any]]:
        """
        Fetches all records.
        """
        if not IS_POSTGRES:
            query = self._to_sqlite_placeholders(query)
            loop = asyncio.get_running_loop()
            cursor = await loop.run_in_executor(None, lambda: self.sqlite_conn.execute(query, args))
            rows = await loop.run_in_executor(None, cursor.fetchall)
            return [dict(row) for row in rows]
        else:
            records = await self.pg_conn.fetch(query, *args)
            return [dict(r) for r in records]

    async def fetchrow(self, query: str, *args: Any) -> Optional[Dict[str, Any]]:
        """
        Fetches a single row.
        """
        if not IS_POSTGRES:
            query = self._to_sqlite_placeholders(query)
            loop = asyncio.get_running_loop()
            cursor = await loop.run_in_executor(None, lambda: self.sqlite_conn.execute(query, args))
            row = await loop.run_in_executor(None, cursor.fetchone)
            return dict(row) if row else None
        else:
            record = await self.pg_conn.fetchrow(query, *args)
            return dict(record) if record else None

    async def fetchval(self, query: str, *args: Any) -> Any:
        """
        Fetches a single scalar value.
        """
        if not IS_POSTGRES:
            query = self._to_sqlite_placeholders(query)
            loop = asyncio.get_running_loop()
            cursor = await loop.run_in_executor(None, lambda: self.sqlite_conn.execute(query, args))
            row = await loop.run_in_executor(None, cursor.fetchone)
            return row[0] if row else None
        else:
            return await self.pg_conn.fetchval(query, *args)

    async def executemany(self, query: str, args_list: List[Any]):
        """
        Executes a query against multiple parameter tuples.
        """
        if not IS_POSTGRES:
            query = self._to_sqlite_placeholders(query)
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self.sqlite_conn.executemany(query, args_list))
        else:
            await self.pg_conn.executemany(query, args_list)

    def _to_sqlite_placeholders(self, query: str) -> str:
        """
        Converts $1, $2, etc., to ?1, ?2, etc. and ILIKE to LIKE for SQLite.
        """
        import re
        query = re.sub(r"\$(\d+)", r"?\1", query)
        query = re.sub(r"\bILIKE\b", "LIKE", query, flags=re.IGNORECASE)
        query = re.sub(r"\bNOT\s+ILIKE\b", "NOT LIKE", query, flags=re.IGNORECASE)
        return query

import re

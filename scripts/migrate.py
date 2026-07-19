"""
Run SQL migrations against the database.

Usage:
    python scripts/migrate.py

Reads and executes all .sql files from src/persistence/migrations/ in order.
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "src" / "persistence" / "migrations"


async def main():
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/agente_ia")
    engine = create_async_engine(db_url)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("No migration files found.")
        return

    async with engine.begin() as conn:
        for mf in migration_files:
            print(f"Running {mf.name}...")
            sql = mf.read_text()
            await conn.execute(text(sql))
            print("  Done.")

    print("All migrations applied.")


if __name__ == "__main__":
    asyncio.run(main())

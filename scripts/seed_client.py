"""
Seed a test client into the database.

Usage:
    python scripts/seed_client.py --client-id demo --phone 123456789 --prompt "Eres un asistente..."
"""

import argparse
import asyncio
import os

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

load_dotenv()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--phone", required=True)
    parser.add_argument("--name", default="Demo Client")
    parser.add_argument("--prompt", default="You are a helpful assistant.")
    parser.add_argument("--tools", nargs="*", default=["get_weather"])
    args = parser.parse_args()

    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5433/agente_ia")
    engine = create_async_engine(db_url)

    async with engine.begin() as conn:
        await conn.execute(
            text("""
                INSERT INTO clients (id, name, phone_number_id, system_prompt)
                VALUES (:id, :name, :phone, :prompt)
                ON CONFLICT(id) DO UPDATE SET
                    name = EXCLUDED.name,
                    system_prompt = EXCLUDED.system_prompt
            """),
            {"id": args.client_id, "name": args.name, "phone": args.phone, "prompt": args.prompt},
        )

        for tool_id in args.tools:
            await conn.execute(
                text("""
                    INSERT INTO client_tools (client_id, tool_id, enabled)
                    VALUES (:cid, :tid, TRUE)
                    ON CONFLICT(client_id, tool_id) DO NOTHING
                """),
                {"cid": args.client_id, "tid": tool_id},
            )

    print(f"Client {args.client_id} seeded successfully.")


if __name__ == "__main__":
    asyncio.run(main())

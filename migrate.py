import asyncio
import os
from pathlib import Path

import asyncpg


async def migrate():
    conn = await asyncpg.connect(
        host=os.getenv("POSTGRES_HOST", "db"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        database=os.environ["POSTGRES_DB"],
    )

    try:
        async with conn.transaction():
            await conn.execute("SELECT pg_advisory_xact_lock(123456)")

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY
                )
            """)

            folder = Path(__file__).parent / "migrations"

            for file in sorted(folder.glob("*.sql")):
                applied = await conn.fetchval(
                    "SELECT 1 FROM schema_migrations WHERE version = $1",
                    file.name,
                )

                if not applied:
                    await conn.execute(file.read_text(encoding="utf-8"))
                    await conn.execute(
                        "INSERT INTO schema_migrations VALUES ($1)",
                        file.name,
                    )
                    print(f"Applied: {file.name}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())

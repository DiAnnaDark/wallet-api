
import os

import asyncpg
import httpx
import pytest

from app import app
from migrate import migrate


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def prepared_db(anyio_backend):
    if os.environ.get("POSTGRES_DB") != "wallet_test_db":
        raise RuntimeError("Tests require wallet_test_db")

    conn = await asyncpg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        database=os.environ["POSTGRES_DB"],
    )

    try:
        database = await conn.fetchval("SELECT current_database()")
        if database != "wallet_test_db":
            raise RuntimeError("Unexpected database")

        await conn.execute(
            "DROP TABLE IF EXISTS wallets, schema_migrations"
        )
    finally:
        await conn.close()

    await migrate()


@pytest.fixture
async def client(prepared_db):
    async with app.router.lifespan_context(app):
        async with app.state.db.acquire() as conn:
            await conn.execute("TRUNCATE TABLE wallets")

        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as http_client:
            yield http_client

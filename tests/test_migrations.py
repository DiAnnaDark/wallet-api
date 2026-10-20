
import asyncpg
import pytest

from app import app
from migrate import migrate

pytestmark = pytest.mark.anyio


async def test_multiple_sql_statements(client, tmp_path):
    migration_name = "900_probe_multiple.sql"

    migration_file = tmp_path / migration_name
    migration_file.write_text(
        "CREATE TABLE migration_probe (value INTEGER NOT NULL);\n"
        "INSERT INTO migration_probe (value) VALUES (7);\n",
        encoding="utf-8",
    )

    try:
        await migrate(tmp_path)
        await migrate(tmp_path)

        async with app.state.db.acquire() as conn:
            count = await conn.fetchval(
                "SELECT COUNT(*) FROM migration_probe"
            )
            applied = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM schema_migrations
                WHERE version = $1
                """,
                migration_name,
            )

        assert count == 1
        assert applied == 1

    finally:
        async with app.state.db.acquire() as conn:
            await conn.execute(
                "DROP TABLE IF EXISTS migration_probe"
            )
            await conn.execute(
                "DELETE FROM schema_migrations WHERE version = $1",
                migration_name,
            )


async def test_migration_rollback_on_error(client, tmp_path):
    first = tmp_path / "910_probe_create.sql"
    second = tmp_path / "911_probe_fail.sql"

    first.write_text(
        "CREATE TABLE migration_rollback_probe (value INTEGER);",
        encoding="utf-8",
    )

    second.write_text(
        """
        INSERT INTO migration_rollback_probe (missing_column)
        VALUES (1);
        """,
        encoding="utf-8",
    )

    try:
        with pytest.raises(asyncpg.exceptions.UndefinedColumnError):
            await migrate(tmp_path)

        async with app.state.db.acquire() as conn:
            table = await conn.fetchval(
                "SELECT to_regclass('public.migration_rollback_probe')"
            )
            applied = await conn.fetchval(
                """
                SELECT COUNT(*)
                FROM schema_migrations
                WHERE version IN ($1, $2)
                """,
                first.name,
                second.name,
            )

        assert table is None
        assert applied == 0

    finally:
        async with app.state.db.acquire() as conn:
            await conn.execute(
                "DROP TABLE IF EXISTS migration_rollback_probe"
            )
            await conn.execute(
                """
                DELETE FROM schema_migrations
                WHERE version IN ($1, $2)
                """,
                first.name,
                second.name,
            )

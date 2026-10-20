
from decimal import Decimal
from uuid import UUID

import asyncpg


async def get_balance(
    conn: asyncpg.Connection,
    wallet_uuid: UUID,
) -> Decimal | None:
    return await conn.fetchval(
        "SELECT balance FROM wallets WHERE id = $1",
        wallet_uuid,
    )


async def deposit(
    conn: asyncpg.Connection,
    wallet_uuid: UUID,
    amount: Decimal,
    max_balance: Decimal,
) -> Decimal | None:
    if amount > max_balance:
        return None

    return await conn.fetchval(
        """
        INSERT INTO wallets (id, balance)
        VALUES ($1, $2)
        ON CONFLICT (id) DO UPDATE
        SET balance = wallets.balance + EXCLUDED.balance
        WHERE wallets.balance <= $3 - EXCLUDED.balance
        RETURNING balance
        """,
        wallet_uuid,
        amount,
        max_balance,
    )


async def withdraw(
    conn: asyncpg.Connection,
    wallet_uuid: UUID,
    amount: Decimal,
) -> Decimal | None:
    return await conn.fetchval(
        """
        UPDATE wallets
        SET balance = balance - $2
        WHERE id = $1 AND balance >= $2
        RETURNING balance
        """,
        wallet_uuid,
        amount,
    )


async def wallet_exists(
    conn: asyncpg.Connection,
    wallet_uuid: UUID,
) -> bool:
    exists = await conn.fetchval(
        "SELECT 1 FROM wallets WHERE id = $1",
        wallet_uuid,
    )
    return bool(exists)

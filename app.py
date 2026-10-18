import os
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Literal
from uuid import UUID

import asyncpg
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

MAX_BALANCE = Decimal("9999999999999999.99")


class Operation(BaseModel):
    operation_type: Literal["DEPOSIT", "WITHDRAW"]
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "db"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        database=os.environ["POSTGRES_DB"],
    )
    try:
        yield
    finally:
        await app.state.db.close()


app = FastAPI(lifespan=lifespan)


@app.get("/api/v1/wallets/{wallet_uuid}")
async def get_balance(wallet_uuid: UUID, request: Request):
    async with request.app.state.db.acquire() as conn:
        balance = await conn.fetchval(
            "SELECT balance FROM wallets WHERE id = $1",
            wallet_uuid,
        )

    if balance is None:
        raise HTTPException(404, "Wallet not found")

    return {"balance": str(balance)}


@app.post("/api/v1/wallets/{wallet_uuid}/operation")
async def change_balance(
    wallet_uuid: UUID,
    operation: Operation,
    request: Request,
):
    async with request.app.state.db.acquire() as conn:
        if operation.operation_type == "DEPOSIT":
            balance = await conn.fetchval(
                """
                INSERT INTO wallets (id, balance)
                VALUES ($1, $2)
                ON CONFLICT (id) DO UPDATE
                SET balance = wallets.balance + EXCLUDED.balance
                WHERE wallets.balance <= $3 - EXCLUDED.balance
                RETURNING balance
                """,
                wallet_uuid,
                operation.amount,
                MAX_BALANCE,
            )
            if balance is None:
                raise HTTPException(409, "Balance limit exceeded")
        else:
            balance = await conn.fetchval(
                """
                UPDATE wallets
                SET balance = balance - $2
                WHERE id = $1 AND balance >= $2
                RETURNING balance
                """,
                wallet_uuid,
                operation.amount,
            )
            if balance is None:
                exists = await conn.fetchval(
                    "SELECT 1 FROM wallets WHERE id = $1",
                    wallet_uuid,
                )
                if not exists:
                    raise HTTPException(404, "Wallet not found")
                raise HTTPException(409, "Insufficient funds")

    return {"balance": str(balance)}

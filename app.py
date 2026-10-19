import os
from contextlib import asynccontextmanager
from uuid import UUID

import asyncpg
from fastapi import FastAPI, HTTPException, Request

from wallets import service
from wallets.schemas import Operation


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
    try:
        balance = await service.get_balance(
            request.app.state.db,
            wallet_uuid,
        )
    except service.WalletNotFoundError:
        raise HTTPException(404, "Wallet not found") from None

    return {"balance": str(balance)}


@app.post("/api/v1/wallets/{wallet_uuid}/operation")
async def change_balance(
    wallet_uuid: UUID,
    operation: Operation,
    request: Request,
):
    try:
        balance = await service.change_balance(
            request.app.state.db,
            wallet_uuid,
            operation,
        )
    except service.WalletNotFoundError:
        raise HTTPException(404, "Wallet not found") from None
    except service.InsufficientFundsError:
        raise HTTPException(409, "Insufficient funds") from None
    except service.BalanceLimitExceededError:
        raise HTTPException(409, "Balance limit exceeded") from None

    return {"balance": str(balance)}

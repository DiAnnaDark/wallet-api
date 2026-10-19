
from decimal import Decimal
from uuid import UUID

import asyncpg

from wallets import repository
from wallets.schemas import Operation

MAX_BALANCE = Decimal("9999999999999999.99")


class WalletNotFoundError(Exception):
    pass


class InsufficientFundsError(Exception):
    pass


class BalanceLimitExceededError(Exception):
    pass


async def get_balance(
    pool: asyncpg.Pool,
    wallet_uuid: UUID,
) -> Decimal:
    async with pool.acquire() as conn:
        balance = await repository.get_balance(conn, wallet_uuid)

    if balance is None:
        raise WalletNotFoundError()

    return balance


async def change_balance(
    pool: asyncpg.Pool,
    wallet_uuid: UUID,
    operation: Operation,
) -> Decimal:
    async with pool.acquire() as conn:
        if operation.operation_type == "DEPOSIT":
            balance = await repository.deposit(
                conn,
                wallet_uuid,
                operation.amount,
                MAX_BALANCE,
            )

            if balance is None:
                raise BalanceLimitExceededError()

        else:
            balance = await repository.withdraw(
                conn,
                wallet_uuid,
                operation.amount,
            )

            if balance is None:
                exists = await repository.wallet_exists(conn, wallet_uuid)

                if not exists:
                    raise WalletNotFoundError()

                raise InsufficientFundsError()

    return balance

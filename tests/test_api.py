
import asyncio
from uuid import uuid4

import pytest

pytestmark = pytest.mark.anyio


def wallet_url(wallet_id):
    return f"/api/v1/wallets/{wallet_id}"


async def operation(client, wallet_id, kind, amount):
    return await client.post(
        wallet_url(wallet_id) + "/operation",
        json={"operation_type": kind, "amount": amount},
        timeout=20,
    )


async def test_wallet_operations(client):
    wallet_id = str(uuid4())

    response = await client.get(wallet_url(wallet_id))
    assert response.status_code == 404

    response = await operation(client, wallet_id, "DEPOSIT", 1000)
    assert response.status_code == 200
    assert response.json()["balance"] == "1000.00"

    response = await operation(client, wallet_id, "WITHDRAW", 300)
    assert response.status_code == 200
    assert response.json()["balance"] == "700.00"

    response = await client.get(wallet_url(wallet_id))
    assert response.json()["balance"] == "700.00"


async def test_insufficient_funds(client):
    wallet_id = str(uuid4())

    response = await operation(client, wallet_id, "DEPOSIT", 100)
    assert response.status_code == 200

    response = await operation(client, wallet_id, "WITHDRAW", 200)
    assert response.status_code == 409

    response = await client.get(wallet_url(wallet_id))
    assert response.json()["balance"] == "100.00"


async def test_validation(client):
    wallet_id = str(uuid4())

    response = await operation(client, wallet_id, "DEPOSIT", -100)
    assert response.status_code == 422

    response = await operation(client, wallet_id, "TRANSFER", 100)
    assert response.status_code == 422

    response = await client.get(wallet_url("invalid-uuid"))
    assert response.status_code == 422


async def test_parallel_withdrawals(client):
    wallet_id = str(uuid4())

    response = await operation(client, wallet_id, "DEPOSIT", 100)
    assert response.status_code == 200

    responses = await asyncio.gather(
        *(
            operation(client, wallet_id, "WITHDRAW", 10)
            for _ in range(20)
        )
    )

    success = sum(r.status_code == 200 for r in responses)
    conflicts = sum(r.status_code == 409 for r in responses)

    assert success == 10
    assert conflicts == 10

    response = await client.get(wallet_url(wallet_id))
    assert response.json()["balance"] == "0.00"

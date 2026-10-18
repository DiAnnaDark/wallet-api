from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import httpx

BASE_URL = "http://127.0.0.1:8001"


def wallet_url(wallet_id):
    return f"{BASE_URL}/api/v1/wallets/{wallet_id}"


def operation(wallet_id, kind, amount):
    return httpx.post(
        wallet_url(wallet_id) + "/operation",
        json={"operation_type": kind, "amount": amount},
        timeout=20,
    )


def test_wallet_operations():
    wallet_id = str(uuid4())

    response = httpx.get(wallet_url(wallet_id))
    assert response.status_code == 404

    response = operation(wallet_id, "DEPOSIT", 1000)
    assert response.status_code == 200
    assert response.json()["balance"] == "1000.00"

    response = operation(wallet_id, "WITHDRAW", 300)
    assert response.status_code == 200
    assert response.json()["balance"] == "700.00"

    response = httpx.get(wallet_url(wallet_id))
    assert response.json()["balance"] == "700.00"


def test_insufficient_funds():
    wallet_id = str(uuid4())

    operation(wallet_id, "DEPOSIT", 100)

    response = operation(wallet_id, "WITHDRAW", 200)
    assert response.status_code == 409

    response = httpx.get(wallet_url(wallet_id))
    assert response.json()["balance"] == "100.00"


def test_validation():
    wallet_id = str(uuid4())

    response = operation(wallet_id, "DEPOSIT", -100)
    assert response.status_code == 422

    response = operation(wallet_id, "TRANSFER", 100)
    assert response.status_code == 422

    response = httpx.get(wallet_url("invalid-uuid"))
    assert response.status_code == 422


def test_parallel_withdrawals():
    wallet_id = str(uuid4())
    operation(wallet_id, "DEPOSIT", 100)

    with ThreadPoolExecutor(max_workers=20) as executor:
        responses = list(
            executor.map(
                lambda _: operation(wallet_id, "WITHDRAW", 10),
                range(20),
            )
        )

    success = sum(r.status_code == 200 for r in responses)
    conflicts = sum(r.status_code == 409 for r in responses)

    assert success == 10
    assert conflicts == 10

    response = httpx.get(wallet_url(wallet_id))
    assert response.json()["balance"] == "0.00"

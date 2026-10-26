from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from src.database import SessionLocal
from src.models.account import Account
from src.models.transaction import Transaction
from src.server.server import app

client = TestClient(app)


def create_account(name: str = "Test account", balance: float = 100.0) -> dict:
    response = client.post("/accounts/", json={"name": name, "balance": balance})

    assert response.status_code == 200
    return response.json()


def delete_account(account_id: int) -> None:
    delete_transactions(account_id)
    client.delete(f"/accounts/{account_id}")


def delete_transactions(account_id: int) -> None:
    database = SessionLocal()

    try:
        database.query(Transaction).filter(Transaction.account_id == account_id).delete()
        database.commit()
    finally:
        database.close()


def create_transaction(
    account_id: int,
    amount: float = 10.0,
    transaction_type: str = "Income",
    description: str = "Test transaction",
) -> dict:
    response = client.post(
        "/transactions/",
        json={
            "description": description,
            "amount": amount,
            "account_id": account_id,
            "transaction_type": transaction_type,
        },
    )

    assert response.status_code == 201
    return response.json()


def get_balance(account_id: int) -> Decimal:
    database = SessionLocal()

    try:
        account = database.query(Account).filter(Account.id == account_id).one()
        return account.balance
    finally:
        database.close()


def as_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def test_list_transactions():
    account = create_account()
    transaction = create_transaction(account["id"])

    try:
        response = client.get("/transactions/")

        assert response.status_code == 200
        assert any(item["id"] == transaction["id"] for item in response.json())
    finally:
        delete_account(account["id"])


def test_get_transaction_by_id():
    account = create_account()
    transaction = create_transaction(account["id"])

    try:
        response = client.get(f"/transactions/{transaction['id']}")

        assert response.status_code == 200
        assert response.json() == transaction
    finally:
        delete_account(account["id"])


def test_get_transaction_by_id_returns_404():
    response = client.get("/transactions/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Transaction not found!"}


def test_list_account_transactions():
    account = create_account()
    transaction = create_transaction(account["id"])

    try:
        response = client.get(f"/transactions/account/{account['id']}")

        assert response.status_code == 200
        assert [item["id"] for item in response.json()] == [transaction["id"]]
    finally:
        delete_account(account["id"])


def test_list_account_transactions_returns_empty_list():
    account = create_account()

    try:
        response = client.get(f"/transactions/account/{account['id']}")

        assert response.status_code == 200
        assert response.json() == []
    finally:
        delete_account(account["id"])


def test_list_account_transactions_returns_404_when_account_not_found():
    response = client.get("/transactions/account/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found!"}


def test_create_income_transaction_increases_balance():
    account = create_account(balance=100.0)

    try:
        transaction = create_transaction(account["id"], amount=25.0, transaction_type="Income")

        assert transaction["account_id"] == account["id"]
        assert Decimal(transaction["amount"]) == Decimal("25.00")
        assert transaction["transaction_type"] == "Income"
        assert transaction["description"] == "Test transaction"
        assert transaction["date"] is not None
        assert get_balance(account["id"]) == Decimal("125.00")
    finally:
        delete_account(account["id"])


def test_create_outcome_transaction_decreases_balance():
    account = create_account(balance=100.0)

    try:
        create_transaction(account["id"], amount=40.0, transaction_type="Outcome")

        assert get_balance(account["id"]) == Decimal("60.00")
    finally:
        delete_account(account["id"])


def test_create_transaction_with_explicit_date():
    account = create_account()

    try:
        transaction = create_transaction(account["id"])
        response = client.post(
            "/transactions/",
            json={
                "date": "2026-01-15T08:30:00+00:00",
                "description": "Old transaction",
                "amount": 10.0,
                "account_id": account["id"],
                "transaction_type": "Income",
            },
        )

        assert response.status_code == 201
        assert as_utc(response.json()["date"]) == datetime(2026, 1, 15, 8, 30, tzinfo=UTC)
        assert response.json()["id"] != transaction["id"]
    finally:
        delete_account(account["id"])


def test_create_outcome_transaction_with_insufficient_funds():
    account = create_account(balance=10.0)

    try:
        response = client.post(
            "/transactions/",
            json={
                "description": "Purchase",
                "amount": 50.0,
                "account_id": account["id"],
                "transaction_type": "Outcome",
            },
        )

        assert response.status_code == 409
        assert response.json() == {"detail": "Insufficient funds!"}
        assert get_balance(account["id"]) == Decimal("10.00")
        assert client.get(f"/transactions/account/{account['id']}").json() == []
    finally:
        delete_account(account["id"])


def test_create_transaction_returns_404_when_account_not_found():
    response = client.post(
        "/transactions/",
        json={
            "description": "Purchase",
            "amount": 10.0,
            "account_id": 999999,
            "transaction_type": "Income",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found!"}


def test_transaction_not_created_with_non_positive_amount():
    account = create_account()

    try:
        response = client.post(
            "/transactions/",
            json={
                "description": "Purchase",
                "amount": 0,
                "account_id": account["id"],
                "transaction_type": "Income",
            },
        )

        assert response.status_code == 422
        assert client.get(f"/transactions/account/{account['id']}").json() == []
    finally:
        delete_account(account["id"])


def test_transaction_not_created_with_invalid_type():
    account = create_account()

    try:
        response = client.post(
            "/transactions/",
            json={
                "description": "Purchase",
                "amount": 10.0,
                "account_id": account["id"],
                "transaction_type": "Invalid",
            },
        )

        assert response.status_code == 422
    finally:
        delete_account(account["id"])

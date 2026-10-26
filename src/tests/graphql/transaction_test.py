from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from src.database import SessionLocal
from src.models.account import Account
from src.models.transaction import Transaction
from src.server.server import app

client = TestClient(app)


def execute(query: str, variables: dict | None = None) -> dict:
    response = client.post(
        "/graphql/transaction",
        json={"query": query, "variables": variables},
    )

    assert response.status_code == 200
    return response.json()


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
    transaction_type: str = "INCOME",
    description: str = "Test transaction",
    date: str = "2026-10-26T10:00:00+00:00",
) -> dict:
    body = execute(
        """
            mutation CreateTransaction($input: TransactionCreate!) {
                createTransaction(input: $input) {
                    id
                    date
                    description
                    amount
                    accountId
                    transactionType
                }
            }
        """,
        {
            "input": {
                "date": date,
                "description": description,
                "amount": amount,
                "accountId": account_id,
                "transactionType": transaction_type,
            }
        },
    )

    assert body.get("errors") is None
    return body["data"]["createTransaction"]


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
        body = execute("{ transactions { id description amount accountId transactionType } }")

        assert body.get("errors") is None
        assert any(item["id"] == transaction["id"] for item in body["data"]["transactions"])
    finally:
        delete_account(account["id"])


def test_get_transaction_by_id():
    account = create_account()
    transaction = create_transaction(account["id"])

    try:
        body = execute(
            """
                query Transaction($id: Int!) {
                    transaction(id: $id) {
                        id
                        description
                        amount
                        accountId
                        transactionType
                    }
                }
            """,
            {"id": transaction["id"]},
        )

        assert body.get("errors") is None
        assert body["data"]["transaction"] == {
            "id": transaction["id"],
            "description": "Test transaction",
            "amount": transaction["amount"],
            "accountId": account["id"],
            "transactionType": "INCOME",
        }
    finally:
        delete_account(account["id"])


def test_get_transaction_returns_null_when_not_found():
    body = execute(
        """
            query Transaction($id: Int!) {
                transaction(id: $id) {
                    id
                }
            }
        """,
        {"id": 999999},
    )

    assert body.get("errors") is None
    assert body["data"]["transaction"] is None


def test_transactions_by_account():
    account = create_account()
    other_account = create_account(name="Other account")
    transaction = create_transaction(account["id"])
    create_transaction(other_account["id"])

    try:
        body = execute(
            """
                query TransactionsByAccount($accountId: Int!) {
                    transactionsByAccount(accountId: $accountId) {
                        id
                        accountId
                    }
                }
            """,
            {"accountId": account["id"]},
        )

        assert body.get("errors") is None
        assert body["data"]["transactionsByAccount"] == [
            {"id": transaction["id"], "accountId": account["id"]}
        ]
    finally:
        delete_account(account["id"])
        delete_account(other_account["id"])


def test_transactions_by_account_returns_empty_list():
    account = create_account()

    try:
        body = execute(
            """
                query TransactionsByAccount($accountId: Int!) {
                    transactionsByAccount(accountId: $accountId) {
                        id
                    }
                }
            """,
            {"accountId": account["id"]},
        )

        assert body.get("errors") is None
        assert body["data"]["transactionsByAccount"] == []
    finally:
        delete_account(account["id"])


def test_transactions_by_account_returns_error_when_account_not_found():
    body = execute(
        """
            query TransactionsByAccount($accountId: Int!) {
                transactionsByAccount(accountId: $accountId) {
                    id
                }
            }
        """,
        {"accountId": 999999},
    )

    assert "Account not found!" in body["errors"][0]["message"]


def test_create_income_transaction_increases_balance():
    account = create_account(balance=100.0)

    try:
        transaction = create_transaction(account["id"], amount=25.0, transaction_type="INCOME")

        assert transaction["accountId"] == account["id"]
        assert Decimal(transaction["amount"]) == Decimal("25.00")
        assert transaction["transactionType"] == "INCOME"
        assert transaction["description"] == "Test transaction"
        assert as_utc(transaction["date"]) == datetime(2026, 10, 26, 10, 0, tzinfo=UTC)
        assert get_balance(account["id"]) == Decimal("125.00")
    finally:
        delete_account(account["id"])


def test_create_outcome_transaction_decreases_balance():
    account = create_account(balance=100.0)

    try:
        create_transaction(account["id"], amount=40.0, transaction_type="OUTCOME")

        assert get_balance(account["id"]) == Decimal("60.00")
    finally:
        delete_account(account["id"])


def test_create_outcome_transaction_with_insufficient_funds():
    account = create_account(balance=10.0)

    try:
        body = execute(
            """
                mutation CreateTransaction($input: TransactionCreate!) {
                    createTransaction(input: $input) {
                        id
                    }
                }
            """,
            {
                "input": {
                    "date": "2026-10-26T10:00:00",
                    "description": "Purchase",
                    "amount": 50.0,
                    "accountId": account["id"],
                    "transactionType": "OUTCOME",
                }
            },
        )

        assert "Insufficient funds!" in body["errors"][0]["message"]
        assert get_balance(account["id"]) == Decimal("10.00")
        assert client.get(f"/transactions/account/{account['id']}").json() == []
    finally:
        delete_account(account["id"])


def test_create_transaction_returns_error_when_account_not_found():
    body = execute(
        """
            mutation CreateTransaction($input: TransactionCreate!) {
                createTransaction(input: $input) {
                    id
                }
            }
        """,
        {
            "input": {
                "date": "2026-10-26T10:00:00",
                "description": "Purchase",
                "amount": 10.0,
                "accountId": 999999,
                "transactionType": "INCOME",
            }
        },
    )

    assert "Account not found!" in body["errors"][0]["message"]


def test_transaction_not_created_with_non_positive_amount():
    account = create_account()

    try:
        body = execute(
            """
                mutation CreateTransaction($input: TransactionCreate!) {
                    createTransaction(input: $input) {
                        id
                    }
                }
            """,
            {
                "input": {
                    "date": "2026-10-26T10:00:00",
                    "description": "Purchase",
                    "amount": 0,
                    "accountId": account["id"],
                    "transactionType": "INCOME",
                }
            },
        )

        assert "Amount must be greater than 0" in body["errors"][0]["message"]
        assert client.get(f"/transactions/account/{account['id']}").json() == []
    finally:
        delete_account(account["id"])

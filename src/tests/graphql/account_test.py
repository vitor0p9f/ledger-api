from fastapi.testclient import TestClient

from src.server.server import app

client = TestClient(app)


def execute(query: str, variables: dict | None = None) -> dict:
    response = client.post(
        "/graphql/account",
        json={"query": query, "variables": variables},
    )

    assert response.status_code == 200
    return response.json()


def create_account(name: str = "Conta teste", balance: float = 100.0) -> dict:
    body = execute(
        """
            mutation CreateAccount($input: AccountCreate!) {
                createAccount(input: $input) {
                    id
                    name
                    balance
                }
            }
        """,
        {"input": {"name": name, "balance": balance}},
    )

    assert body.get("errors") is None
    return body["data"]["createAccount"]


def delete_account(account_id: int) -> None:
    execute(
        """
            mutation DeleteAccount($accountId: Int!) {
                deleteAccount(accountId: $accountId)
            }
        """,
        {"accountId": account_id},
    )


def test_list_accounts():
    account = create_account()

    try:
        body = execute("{ accounts { id name balance } }")

        assert body.get("errors") is None
        assert any(
            item["id"] == account["id"]
            for item in body["data"]["accounts"]
        )
    finally:
        delete_account(account["id"])


def test_get_account_by_id():
    account = create_account()

    try:
        body = execute(
            """
                query Account($accountId: Int!) {
                    account(accountId: $accountId) {
                        id
                        name
                        balance
                    }
                }
            """,
            {"accountId": account["id"]},
        )

        assert body.get("errors") is None
        assert body["data"]["account"] == {
            "id": account["id"],
            "name": account["name"],
            "balance": account["balance"],
        }
    finally:
        delete_account(account["id"])


def test_create_account():
    account = create_account(name="Conta teste", balance=100.0)

    try:
        assert account["name"] == "Conta teste"
        assert account["balance"] == 100.0
    finally:
        delete_account(account["id"])


def test_account_not_be_created_with_negative_balance():
    body = execute(
        """
            mutation CreateAccount($input: AccountCreate!) {
                createAccount(input: $input) {
                    name
                    balance
                }
            }
        """,
        {"input": {"name": "Conta teste", "balance": -100.0}},
    )

    assert body["data"]["createAccount"] is None
    assert "Balance must be greater than or equal to 0" in body["errors"][0]["message"]


def test_update_account_name():
    account = create_account(name="Conta A", balance=10.0)

    try:
        body = execute(
            """
                mutation UpdateAccount($accountId: Int!, $input: AccountUpdate!) {
                    updateAccount(accountId: $accountId, input: $input) {
                        name
                    }
                }
            """,
            {
                "accountId": account["id"],
                "input": {"name": "Novo nome"},
            },
        )

        assert body.get("errors") is None
        assert body["data"]["updateAccount"]["name"] == "Novo nome"
    finally:
        delete_account(account["id"])


def test_update_account_cannot_change_balance():
    account = create_account(name="Conta A", balance=10.0)

    try:
        body = execute(
            """
                mutation UpdateAccount($accountId: Int!, $input: AccountUpdate!) {
                    updateAccount(accountId: $accountId, input: $input) {
                        name
                    }
                }
            """,
            {
                "accountId": account["id"],
                "input": {"name": "Novo nome", "balance": 999.0},
            },
        )

        assert body["data"] is None
        assert "unknown field 'balance'" in body["errors"][0]["message"]
    finally:
        delete_account(account["id"])


def test_update_account_returns_null_when_not_found():
    body = execute(
        """
            mutation UpdateAccount($accountId: Int!, $input: AccountUpdate!) {
                updateAccount(accountId: $accountId, input: $input) {
                    name
                }
            }
        """,
        {
            "accountId": 999999,
            "input": {"name": "Novo nome"},
        },
    )

    assert body.get("errors") is None
    assert body["data"]["updateAccount"] is None


def test_delete_account():
    account = create_account()

    body = execute(
        """
            mutation DeleteAccount($accountId: Int!) {
                deleteAccount(accountId: $accountId)
            }
        """,
        {"accountId": account["id"]},
    )

    assert body.get("errors") is None
    assert body["data"]["deleteAccount"] is True

    body = execute(
        """
            query Account($accountId: Int!) {
                account(accountId: $accountId) {
                    id
                }
            }
        """,
        {"accountId": account["id"]},
    )

    assert body["data"]["account"] is None


def test_delete_account_returns_false_when_not_found():
    body = execute(
        """
            mutation DeleteAccount($accountId: Int!) {
                deleteAccount(accountId: $accountId)
            }
        """,
        {"accountId": 999999},
    )

    assert body.get("errors") is None
    assert body["data"]["deleteAccount"] is False

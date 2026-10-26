from fastapi.testclient import TestClient

from src.server.server import app

client = TestClient(app)


def create_account(name: str = "Conta teste", balance: float = 100.0) -> dict:
    response = client.post("/accounts/", json={"name": name, "balance": balance})

    assert response.status_code == 200
    return response.json()


def delete_account(account_id: int) -> None:
    client.delete(f"/accounts/{account_id}")


def test_list_accounts():
    account = create_account()

    try:
        response = client.get("/accounts/")

        assert response.status_code == 200
        assert any(item["id"] == account["id"] for item in response.json())
    finally:
        delete_account(account["id"])


def test_get_account_by_id():
    account = create_account()

    try:
        response = client.get(f"/accounts/{account['id']}")

        assert response.status_code == 200
        assert response.json() == account
    finally:
        delete_account(account["id"])


def test_get_account_by_id_returns_404():
    response = client.get("/accounts/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found!"}


def test_create_account():
    response = client.post(
        "/accounts/",
        json={"name": "Conta teste", "balance": 100.0},
    )

    assert response.status_code == 200

    data = response.json()

    try:
        assert data["name"] == "Conta teste"
        assert data["balance"] == 100.0
    finally:
        delete_account(data["id"])


def test_account_not_be_created_with_negative_balance():
    response = client.post(
        "/accounts/",
        json={"name": "Conta teste", "balance": -100.0},
    )

    assert response.status_code == 422


def test_update_account_name():
    account = create_account(name="Conta A", balance=10.0)

    try:
        response = client.patch(
            f"/accounts/{account['id']}",
            json={"name": "Novo nome"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Novo nome"
    finally:
        delete_account(account["id"])


def test_update_account_cannot_change_balance():
    account = create_account(name="Conta A", balance=10.0)

    try:
        response = client.patch(
            f"/accounts/{account['id']}",
            json={"name": "Novo nome", "balance": 999.0},
        )

        assert response.status_code == 200
        assert response.json()["balance"] == 10.0
    finally:
        delete_account(account["id"])


def test_update_account_returns_404():
    response = client.patch(
        "/accounts/999999",
        json={"name": "Novo nome"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found!"}


def test_delete_account():
    account = create_account()

    response = client.delete(f"/accounts/{account['id']}")

    assert response.status_code == 204
    assert client.get(f"/accounts/{account['id']}").status_code == 404


def test_delete_account_returns_404():
    response = client.delete("/accounts/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Account not found!"}

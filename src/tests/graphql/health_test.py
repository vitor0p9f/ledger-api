from fastapi.testclient import TestClient

from src.server.server import app

client = TestClient(app)


def test_health_route_returns_message():
    response = client.post(
        "/graphql",
        json={"query": "{ health { message } }"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "health": {
                "message": "API is healthy and running!",
            }
        }
    }

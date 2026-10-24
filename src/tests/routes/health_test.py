from fastapi.testclient import TestClient
from src.server.server import app

client = TestClient(app)

def test_if_health_route_returns_200():
    response = client.get("/health")
    
    assert response.status_code == 200

def test_if_health_route_returns_correct_body():
    response = client.get("/health")

    assert response.json() == {"message": "API is healthy and running!"}


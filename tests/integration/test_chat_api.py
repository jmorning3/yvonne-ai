from fastapi.testclient import TestClient


def test_chat_endpoint():
    from backend.app.main import app
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"userId": "u", "message": "Hello"})
    assert response.status_code == 200
    assert response.json()["data"]["provider"] == "mock"

def test_health_endpoint():
    from backend.app.main import app
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200

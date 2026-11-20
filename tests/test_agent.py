import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import init_db, SessionLocal, RefundRequest

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    # Cleanup if needed

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "OpsPilot" in response.json()["message"]

def test_order_status_inquiry():
    response = client.post("/agent/process", json={
        "customer_email": "alice@example.com",
        "message": "My order was supposed to arrive yesterday. I still haven't received it.",
        "order_number": "ORD-1001"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "order_status"
    assert data["order_number"] == "ORD-1001"
    assert "delayed" in data["response_text"].lower()
    assert not data["requires_human"]

def test_eligible_refund_creates_approval():
    response = client.post("/agent/process", json={
        "customer_email": "alice@example.com",
        "message": "I want a refund please",
        "order_number": "ORD-1001"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "refund_request"
    assert data["requires_human"] is True
    assert "refund_request_id" in data["evidence"]

def test_pending_refunds_endpoint():
    # First create one
    client.post("/agent/process", json={
        "customer_email": "alice@example.com",
        "message": "refund request",
        "order_number": "ORD-1001"
    })
    response = client.get("/refunds/pending")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Verify system info and ISO compliance status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert "Solanka Digital Tourism" in data["organization"]
    assert "ISO 9001:2015" in data["compliance"]
    assert "ISO/IEC 27001:2022" in data["compliance"]

def test_health_check():
    """Verify health endpoint used by Jenkins & Ansible gates."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["database"] == "CONNECTED"
    assert "timestamp" in data

def test_list_destinations():
    """Verify destination catalog returns destinations."""
    response = client.get("/api/v1/destinations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 5
    assert len(data["destinations"]) >= 5

def test_get_single_destination_valid():
    """Verify fetching destination by ID."""
    response = client.get("/api/v1/destinations/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Sigiriya Ancient Rock Fortress"

def test_get_single_destination_not_found():
    """Verify 404 response for invalid destination."""
    response = client.get("/api/v1/destinations/9999")
    assert response.status_code == 404

def test_create_booking_valid():
    """Verify booking creation and price calculation."""
    payload = {
        "customer_name": "Kasun Perera",
        "customer_email": "kasun.perera@example.com",
        "destination_id": 1,
        "num_passengers": 2,
        "travel_date": "2026-11-20"
    }
    response = client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["customer_name"] == "Kasun Perera"
    assert data["total_cost_usd"] == 72.0  # 36.0 * 2
    assert data["status"] == "CONFIRMED"
    assert "SLK-" in data["booking_id"]

def test_create_booking_invalid_destination():
    """Verify rejection of booking with nonexistent destination."""
    payload = {
        "customer_name": "Kasun Perera",
        "customer_email": "kasun.perera@example.com",
        "destination_id": 9999,
        "num_passengers": 2,
        "travel_date": "2026-11-20"
    }
    response = client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 400

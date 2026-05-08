import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app, _items

client = TestClient(app)


def setup_function():
    _items.clear()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_list_items_empty():
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json() == []


def test_create_item():
    payload = {"name": "Widget", "description": "A test widget", "price": 9.99}
    response = client.post("/items", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Widget"
    assert body["price"] == 9.99
    assert "id" in body


def test_get_item():
    payload = {"name": "Gadget", "price": 4.99}
    created = client.post("/items", json=payload).json()
    response = client.get(f"/items/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_list_items_after_create():
    client.post("/items", json={"name": "A", "price": 1.0})
    client.post("/items", json={"name": "B", "price": 2.0})
    response = client.get("/items")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_nonexistent_item():
    response = client.get("/items/does-not-exist")
    assert response.status_code == 404

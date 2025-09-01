import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))


@pytest.fixture()
def client(monkeypatch):
    # Set required environment variable before importing the app
    monkeypatch.setenv("ENCRYPTION_PASSWORD", "test")

    from main import app
    from app.services.playwright_service import playwright_service

    async def fake_start():
        pass

    async def fake_stop():
        pass

    monkeypatch.setattr(playwright_service, "start", fake_start)
    monkeypatch.setattr(playwright_service, "stop", fake_stop)
    monkeypatch.setattr(playwright_service, "is_available", lambda: True)

    with TestClient(app) as client:
        yield client


def test_health(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["playwright_available"] is True


def test_transform_success(client):
    payload = {
        "data": "hello",
        "transformation_rules": {"uppercase": True},
    }
    response = client.post("/transform", json=payload)
    assert response.status_code == 200
    assert response.json()["transformed_data"] == "HELLO"


def test_transform_missing_data(client):
    response = client.post(
        "/transform", json={"transformation_rules": {"uppercase": True}}
    )
    assert response.status_code == 422


def test_extract_from_source_data(client):
    payload = {
        "source_data": {"name": "Alice", "age": 30},
        "extraction_config": {"extract_keys": ["name"]},
    }
    response = client.post("/extract", json=payload)
    assert response.status_code == 200
    assert response.json()["extracted_data"] == {"name": "Alice"}


def test_extract_missing_source(client):
    response = client.post("/extract", json={})
    assert response.status_code == 400


def test_transfer_to_file(client, tmp_path):
    target = tmp_path / "output.json"
    payload = {
        "data": {"foo": "bar"},
        "destination": "file",
        "transfer_config": {"file_path": str(target)},
    }
    response = client.post("/transfer", json=payload)
    assert response.status_code == 200
    assert target.exists()
    content = json.loads(target.read_text())
    assert content["data"] == {"foo": "bar"}


def test_transfer_missing_file_path(client):
    payload = {"data": {"foo": "bar"}, "destination": "file"}
    response = client.post("/transfer", json=payload)
    assert response.status_code == 400

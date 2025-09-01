import json
import pytest
import sys
from pathlib import Path
import os
import asyncio

# Ensure the application package is importable
sys.path.append(str(Path(__file__).resolve().parents[2]))

# Provide required environment variable for encryption service during import
os.environ.setdefault("ENCRYPTION_PASSWORD", "test")

from app.services.transfer_service import TransferService


class MockResponse:
    def __init__(self, status_code=200, text="ok"):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        pass


class MockAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def post(self, *args, **kwargs):
        return MockResponse()

    async def put(self, *args, **kwargs):
        return MockResponse()


def test_transfer_to_webhook_post(monkeypatch):
    monkeypatch.setattr("app.services.transfer_service.httpx.AsyncClient", MockAsyncClient)

    data = {"foo": "bar"}
    config = {"webhook_url": "http://example.com", "method": "POST"}

    result = asyncio.run(TransferService._transfer_to_webhook(data, config, "t1"))

    assert result["webhook_url"] == config["webhook_url"]
    assert result["status_code"] == 200
    assert result["response_body"] == "ok"


def test_transfer_to_webhook_put(monkeypatch):
    monkeypatch.setattr("app.services.transfer_service.httpx.AsyncClient", MockAsyncClient)

    data = {"foo": "bar"}
    config = {"webhook_url": "http://example.com", "method": "PUT"}

    result = asyncio.run(TransferService._transfer_to_webhook(data, config, "t1"))

    assert result["webhook_url"] == config["webhook_url"]
    assert result["status_code"] == 200
    assert result["response_body"] == "ok"


def test_transfer_to_webhook_missing_url():
    with pytest.raises(ValueError):
        asyncio.run(TransferService._transfer_to_webhook({}, {}, "t1"))


def test_transfer_to_file_json(tmp_path):
    file_path = tmp_path / "out.json"
    data = {"foo": "bar"}
    config = {"file_path": str(file_path), "format": "json"}

    result = asyncio.run(TransferService._transfer_to_file(data, config, "t1"))

    assert file_path.exists()
    with open(file_path) as f:
        content = json.load(f)
    assert content["data"] == data
    assert result["file_path"] == str(file_path)
    assert result["file_format"] == "json"


def test_transfer_to_file_csv(tmp_path):
    file_path = tmp_path / "out.csv"
    data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
    config = {"file_path": str(file_path), "format": "csv"}

    result = asyncio.run(TransferService._transfer_to_file(data, config, "t1"))

    assert file_path.exists()
    with open(file_path) as f:
        lines = f.read().strip().splitlines()
    assert lines[0] == "a,b"
    assert lines[1] == "1,2"
    assert lines[2] == "3,4"
    assert result["file_path"] == str(file_path)
    assert result["file_format"] == "csv"


def test_transfer_data_unknown_destination():
    with pytest.raises(ValueError):
        asyncio.run(TransferService.transfer_data({}, "unknown"))

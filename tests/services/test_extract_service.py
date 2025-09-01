import pytest
from unittest.mock import patch
import sys
from pathlib import Path
import os
import asyncio

sys.path.append(str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("ENCRYPTION_PASSWORD", "test-password")

from app.services.extract_service import ExtractService


def test_extract_data_with_extract_keys():
    source_data = {"name": "Alice", "age": 30, "city": "Berlin"}
    config = {"extract_keys": ["name", "age"]}

    result = asyncio.run(
        ExtractService.extract_data(source_data=source_data, config=config)
    )

    assert result["extracted_data"] == {"name": "Alice", "age": 30}
    assert result["source"] == "provided_data"


def test_extract_data_with_extract_paths():
    source_data = {"user": {"name": "Bob", "details": {"age": 25}}}
    config = {"extract_paths": {"username": "user.name", "age": "user.details.age"}}

    result = asyncio.run(
        ExtractService.extract_data(source_data=source_data, config=config)
    )

    assert result["extracted_data"] == {"username": "Bob", "age": 25}


def test_extract_data_with_regex_patterns():
    source_text = "Order: #12345 Price: $9.99"
    config = {
        "regex_patterns": {
            "order_id": r"#(\d+)",
            "price": r"\$(\d+\.\d{2})",
        }
    }

    result = asyncio.run(
        ExtractService.extract_data(source_data=source_text, config=config)
    )

    assert result["extracted_data"] == {"order_id": ["12345"], "price": ["9.99"]}


def test_extract_data_source_url_without_browser_raises():
    with patch("app.services.extract_service.playwright_service.is_available", return_value=False):
        with pytest.raises(RuntimeError):
            asyncio.run(
                ExtractService.extract_data(source_url="http://example.com")
            )


def test_extract_from_data_list_filter():
    data = [
        {"type": "fruit", "name": "apple"},
        {"type": "vegetable", "name": "carrot"},
        {"type": "fruit", "name": "banana"},
    ]
    config = {
        "extract_list": {
            "filter": {"field_equals": {"field": "type", "value": "fruit"}}
        }
    }

    result = ExtractService._extract_from_data(data, config)

    assert result == [
        {"type": "fruit", "name": "apple"},
        {"type": "fruit", "name": "banana"},
    ]


def test_extract_from_data_json_path():
    data = {"store": {"bicycle": {"color": "red"}}}
    config = {"json_path": "$.store.bicycle.color"}

    result = ExtractService._extract_from_data(data, config)

    assert result == "red"

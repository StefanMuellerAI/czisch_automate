import os, sys
os.environ.setdefault("ENCRYPTION_PASSWORD", "test")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.transform_service import TransformService
from app.database.models import etl_db
from app.services.html_transform_service import HTMLToXMLTransformService


def test_transform_with_database_rule_calls_html_transform(monkeypatch):
    mock_rule = SimpleNamespace(description="desc", rules={"some": "rule"})
    get_rule_mock = MagicMock(return_value=mock_rule)
    transform_html_mock = MagicMock(return_value="<xml></xml>")

    monkeypatch.setattr(etl_db, "get_transform_rule", get_rule_mock)
    monkeypatch.setattr(
        HTMLToXMLTransformService, "transform_html_to_xml", transform_html_mock
    )

    result = TransformService._transform_with_database_rule("<html></html>", "rule1")

    assert result == "<xml></xml>"
    get_rule_mock.assert_called_once_with("rule1")
    transform_html_mock.assert_called_once_with("<html></html>", mock_rule.rules)


def test_transform_with_database_rule_raises_when_rule_missing(monkeypatch):
    get_rule_mock = MagicMock(return_value=None)
    transform_html_mock = MagicMock()

    monkeypatch.setattr(etl_db, "get_transform_rule", get_rule_mock)
    monkeypatch.setattr(
        HTMLToXMLTransformService, "transform_html_to_xml", transform_html_mock
    )

    with pytest.raises(ValueError):
        TransformService._transform_with_database_rule("<html></html>", "missing")

    get_rule_mock.assert_called_once_with("missing")
    transform_html_mock.assert_not_called()

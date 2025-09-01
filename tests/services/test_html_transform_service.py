import sys
from pathlib import Path

import pytest

# Ensure the application package is importable when running tests directly
sys.path.append(str(Path(__file__).resolve().parents[2]))
from app.services.html_transform_service import HTMLToXMLTransformService


def test_transform_html_to_xml_with_extract_and_wrap():
    html = "<html><body><p>Hello World</p></body></html>"
    rules = [
        {"action": "extract_text", "target": "p", "output": "content"},
        {"action": "wrap_xml", "root_element": "document", "content_element": "content"},
    ]

    result = HTMLToXMLTransformService.transform_html_to_xml(html, rules)

    expected = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<document>\n<content>Hello World</content>\n</document>"
    )
    assert result == expected


def test_wrap_xml_with_add_metadata():
    data = {"content": "Hello World"}
    rule = {
        "root_element": "doc",
        "content_element": "content",
        "add_metadata": {"timestamp": "2021-01-01T00:00:00", "length": "auto"},
    }

    result = HTMLToXMLTransformService._wrap_xml(data, rule)

    expected = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<doc>\n<metadata>\n<timestamp>2021-01-01T00:00:00</timestamp>\n"
        "<length>11</length>\n</metadata>\n<content>Hello World</content>\n</doc>"
    )
    assert result == expected

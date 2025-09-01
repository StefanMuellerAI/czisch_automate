import os
import sys
from pathlib import Path
import pytest
import re

sys.path.append(str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("ENCRYPTION_PASSWORD", "test-password")

from app.services.transform_service import TransformService


def test_apply_string_transformations_uppercase_regex_prefix():
    data = "hello world"
    rules = {
        "uppercase": True,
        "regex_replace": {"pattern": "WORLD", "replacement": "universe"},
        "prefix": "Say: ",
    }
    result = TransformService._apply_string_transformations(data, rules)
    assert result == "Say: HELLO universe"


def test_apply_numeric_transformations_multiply():
    result = TransformService._apply_numeric_transformations(
        5, {"multiply": True, "multiply_by": 3}
    )
    assert result == 15


def test_apply_numeric_transformations_divide_by_zero():
    result = TransformService._apply_numeric_transformations(
        5, {"divide": True, "divide_by": 0}
    )
    assert result == 5


def test_apply_dict_transformations_filter_rename_flatten():
    data = {"keep": 1, "remove": 2, "nested": {"a": 3}}
    rules = {
        "filter_keys": True,
        "allowed_keys": ["keep", "nested"],
        "rename_keys": True,
        "key_mapping": {"keep": "kept"},
        "flatten": True,
    }
    result = TransformService._apply_dict_transformations(data, rules)
    assert result == {"kept": 1, "nested.a": 3}


def test_apply_list_transformations_sort_limit_unique():
    data = [3, 1, 2, 3, 2]
    rules = {"sort": True, "limit": True, "limit_size": 3, "unique": True}
    result = TransformService._apply_list_transformations(data, rules)
    assert result == [1, 2]


def test_transform_data_valid_and_invalid_rules():
    assert TransformService.transform_data("hello", {"uppercase": True}) == "HELLO"

    with pytest.raises(re.error):
        TransformService.transform_data(
            "hello", {"regex_replace": {"pattern": "["}}
        )

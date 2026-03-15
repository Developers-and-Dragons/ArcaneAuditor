#!/usr/bin/env python3
"""Tests for shared orchestration path/location helpers."""

import pytest
from parser.rules.structure.shared.orchestration_path_utils import (
    format_location_fallback,
    get_expression_source,
    resolve_ui_location,
)


def _raw_value_with_create_json_mapping(path_value: str, expr_source: str):
    """Build minimal flow: one CreateJson step with one Mapping (path, expr)."""
    return {
        "nodes": {
            "_type": ["List", "Node"],
            "_value": [
                {
                    "_type": "CreateJson",
                    "_value": {
                        "name": {"_type": "Identifier", "_value": "CreateJSON"},
                        "values": {
                            "_type": ["List", "Mapping"],
                            "_value": [
                                {
                                    "_type": "Mapping",
                                    "_value": {
                                        "path": {"_type": "JsonPath", "_value": path_value},
                                        "expr": {
                                            "_type": ["Expr", "Number"],
                                            "_value": {
                                                "type": {"_type": "Type", "_value": "Number"},
                                                "source": {"_type": "String", "_value": expr_source},
                                            },
                                        },
                                    },
                                }
                            ],
                        },
                    },
                }
            ],
        }
    }


class TestResolveUiLocationCreateJsonMapping:
    """resolve_ui_location for CreateJson mapping expressions."""

    def test_createjson_mapping_path_strips_leading_dollar_dot(self):
        """Path inside values -> mapping -> expr: location is StepName -> path label ($. stripped)."""
        raw = _raw_value_with_create_json_mapping("$.jsonNumberNoDefault", "data.asJSON().numberAtJsonPath(\"$.x\")")
        path = ("nodes", "_value", 0, "_value", "values", "_value", 0, "_value", "expr", "_value")
        loc = resolve_ui_location(raw, path)
        assert loc == "CreateJSON -> jsonNumberNoDefault"

    def test_createjson_mapping_path_nested_jsonpath_unchanged(self):
        """Path like $.myList[0].foo: only leading $. stripped, rest unchanged."""
        raw = _raw_value_with_create_json_mapping("$.myList[0].foo", "data.asJSON().numberAtJsonPath(\"$.n\")")
        path = ("nodes", "_value", 0, "_value", "values", "_value", 0, "_value", "expr", "_value")
        loc = resolve_ui_location(raw, path)
        assert loc == "CreateJSON -> myList[0].foo"

    def test_createjson_mapping_path_without_dollar_dot_unchanged(self):
        """Path without $. prefix is used as-is."""
        raw = _raw_value_with_create_json_mapping("someKey", "1")
        path = ("nodes", "_value", 0, "_value", "values", "_value", 0, "_value", "expr", "_value")
        loc = resolve_ui_location(raw, path)
        assert loc == "CreateJSON -> someKey"

    def test_sublocation_same_as_step_name_not_duplicated(self):
        """When resolved sublocation equals the step name, return only the step name (e.g. CTT_XmlInput not CTT_XmlInput -> CTT_XmlInput)."""
        raw = {
            "nodes": {
                "_type": ["List", "Node"],
                "_value": [
                    {
                        "_type": "CreateTextTemplate",
                        "_value": {
                            "name": {"_type": "Identifier", "_value": "CTT_XmlInput"},
                            "message": {"_type": "TextTemplate", "_value": "{{x}}"},
                        },
                    }
                ],
            }
        }
        path = ("nodes", "_value", 0, "_value", "message")
        loc = resolve_ui_location(raw, path)
        assert loc == "CTT_XmlInput"


class TestFormatLocationFallback:
    """format_location_fallback does not leak internal tokens."""

    def test_fallback_does_not_contain_expr(self):
        """Fallback should not emit raw 'expr'; use 'value' or similar."""
        path = ("nodes", "_value", 0, "_value", "values", "_value", 0, "_value", "expr")
        result = format_location_fallback(path)
        assert "expr" not in result
        assert "value" in result or "assignment" in result

    def test_fallback_emits_user_facing_labels(self):
        """Fallback uses node N, branch N, assignment N style."""
        path = ("nodes", "_value", 0, "_value", "condition", "_value")
        result = format_location_fallback(path)
        assert "condition" in result
        assert "node 1" in result or "value" in result or result


class TestGetExpressionSource:
    """get_expression_source from path_utils."""

    def test_returns_source_string(self):
        expr = {
            "_type": ["Expr", "String"],
            "_value": {"type": {"_type": "Type", "_value": "String"}, "source": {"_type": "String", "_value": "  foo()  "}},
        }
        assert get_expression_source(expr) == "foo()"

    def test_returns_none_for_missing_source(self):
        expr = {"_type": ["Expr", "String"], "_value": {}}
        assert get_expression_source(expr) is None

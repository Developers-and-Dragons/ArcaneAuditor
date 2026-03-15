#!/usr/bin/env python3
"""Unit tests for OrchestratePreferExplicitDefaultAccessor."""

import pytest
from parser.rules.structure.validation.orchestrate_prefer_explicit_default_accessor import (
    OrchestratePreferExplicitDefaultAccessor,
)
from parser.models import ProjectContext, OrchestrationModel


def _expr(source: str, expr_type: str = "String"):
    """Build a minimal expression object with source (any type)."""
    return {
        "_type": ["Expr", expr_type],
        "_value": {
            "type": {"_type": "Type", "_value": expr_type},
            "source": {"_type": "String", "_value": source},
        },
    }


def _raw_value_with_expr(expr_obj, key: str = "expr"):
    """Put a single expression under key in a minimal flow (nodes -> first node -> key)."""
    return {
        "nodes": {
            "_type": ["List", "Node"],
            "_value": [
                {
                    "_type": "CreateValues",
                    "_value": {
                        "name": {"_type": "Identifier", "_value": "CV"},
                        "values": {
                            "_type": ["List", "Assignment"],
                            "_value": [
                                {
                                    "_type": "Assignment",
                                    "_value": {
                                        "name": {"_type": "Identifier", "_value": "x"},
                                        key: expr_obj,
                                    },
                                }
                            ],
                        },
                    },
                }
            ],
        }
    }


class TestOrchestratePreferExplicitDefaultAccessor:
    """Test cases for OrchestratePreferExplicitDefaultAccessor."""

    def setup_method(self):
        self.rule = OrchestratePreferExplicitDefaultAccessor()
        self.context = ProjectContext()

    def _run(self, raw_value: dict, file_path: str = "test.orchestration"):
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="test-id",
            name="testOrch",
            security_domains=None,
            raw_value=raw_value,
            file_path=file_path,
            source_content="",
        )
        self.context.orchestrations["test-id"] = orch
        return list(self.rule.analyze(self.context))

    # --- Positive: each unsafe function ---

    def test_positive_boolean_at_json_path(self):
        raw = _raw_value_with_expr(_expr('data.asJSON().booleanAtJsonPath("/foo")'))
        findings = self._run(raw)
        assert len(findings) >= 1
        assert "booleanAtJsonPath" in findings[0].message
        assert "booleanAtJsonPathWithDefault" in findings[0].message

    def test_positive_number_at_json_path(self):
        raw = _raw_value_with_expr(_expr('data.asJSON().numberAtJsonPath("/count")'))
        findings = self._run(raw)
        assert len(findings) >= 1
        assert "numberAtJsonPath" in findings[0].message
        assert "numberAtJsonPathWithDefault" in findings[0].message

    def test_positive_object_at_json_path(self):
        raw = _raw_value_with_expr(_expr('data.asJSON().objectAtJsonPath("/obj")'))
        findings = self._run(raw)
        assert len(findings) >= 1
        assert "objectAtJsonPath" in findings[0].message
        assert "objectAtJsonPathWithDefault" in findings[0].message

    def test_positive_string_at_json_path(self):
        raw = _raw_value_with_expr(_expr('data.asJSON().stringAtJsonPath("/name")'))
        findings = self._run(raw)
        assert len(findings) >= 1
        assert "stringAtJsonPath" in findings[0].message
        assert "stringAtJsonPathWithDefault" in findings[0].message
        assert "stringAtJsonPathOrEmptyString" in findings[0].message

    def test_positive_big_decimal_at_x_path(self):
        raw = _raw_value_with_expr(_expr('data.asXML().bigDecimalAtXPath("//amount")'))
        findings = self._run(raw)
        assert len(findings) >= 1
        assert "bigDecimalAtXPath" in findings[0].message
        assert "bigDecimalAtXPathWithDefault" in findings[0].message

    def test_positive_boolean_at_x_path(self):
        raw = _raw_value_with_expr(_expr('data.asXML().booleanAtXPath("//flag")'))
        findings = self._run(raw)
        assert len(findings) >= 1
        assert "booleanAtXPath" in findings[0].message
        assert "booleanAtXPathWithDefault" in findings[0].message

    def test_positive_date_at_x_path(self):
        raw = _raw_value_with_expr(_expr('data.asXML().dateAtXPath("//dob")'))
        findings = self._run(raw)
        assert len(findings) >= 1
        assert "dateAtXPath" in findings[0].message
        assert "dateAtXPathWithDefault" in findings[0].message

    def test_positive_date_time_at_x_path(self):
        raw = _raw_value_with_expr(_expr('data.asXML().dateTimeAtXPath("//ts")'))
        findings = self._run(raw)
        assert len(findings) >= 1
        assert "dateTimeAtXPath" in findings[0].message
        assert "dateTimeAtXPathWithDefault" in findings[0].message

    def test_positive_number_at_x_path(self):
        raw = _raw_value_with_expr(_expr('data.asXML().numberAtXPath("//n")'))
        findings = self._run(raw)
        assert len(findings) >= 1
        assert "numberAtXPath" in findings[0].message
        assert "numberAtXPathWithDefault" in findings[0].message

    def test_positive_string_at_x_path(self):
        raw = _raw_value_with_expr(_expr('data.asXML().stringAtXPath("//text")'))
        findings = self._run(raw)
        assert len(findings) >= 1
        assert "stringAtXPath" in findings[0].message
        assert "stringAtXPathWithDefault" in findings[0].message
        assert "stringAtXPathOrEmptyString" in findings[0].message

    def test_positive_xml_string(self):
        raw = _raw_value_with_expr(_expr('data.asXML().xmlString()'))
        findings = self._run(raw)
        assert len(findings) >= 1
        assert "xmlString" in findings[0].message
        assert "xmlStringWithDefault" in findings[0].message

    def test_positive_zoned_date_time_at_x_path(self):
        raw = _raw_value_with_expr(_expr('data.asXML().zonedDateTimeAtXPath("//zdt")'))
        findings = self._run(raw)
        assert len(findings) >= 1
        assert "zonedDateTimeAtXPath" in findings[0].message
        assert "zonedDateTimeAtXPathWithDefault" in findings[0].message

    # --- Negative: safe alternatives not flagged ---

    def test_negative_string_at_json_path_with_default(self):
        raw = _raw_value_with_expr(_expr('data.asJSON().stringAtJsonPathWithDefault("/name", "")'))
        findings = self._run(raw)
        assert len(findings) == 0

    def test_negative_string_at_json_path_or_empty_string(self):
        raw = _raw_value_with_expr(_expr('data.asJSON().stringAtJsonPathOrEmptyString("/name")'))
        findings = self._run(raw)
        assert len(findings) == 0

    def test_negative_string_at_x_path_with_default(self):
        raw = _raw_value_with_expr(_expr('data.asXML().stringAtXPathWithDefault("//text", "")'))
        findings = self._run(raw)
        assert len(findings) == 0

    def test_negative_string_at_x_path_or_empty_string(self):
        raw = _raw_value_with_expr(_expr('data.asXML().stringAtXPathOrEmptyString("//text")'))
        findings = self._run(raw)
        assert len(findings) == 0

    def test_negative_boolean_at_json_path_with_default(self):
        raw = _raw_value_with_expr(_expr('data.asJSON().booleanAtJsonPathWithDefault("/foo", false)'))
        findings = self._run(raw)
        assert len(findings) == 0

    def test_negative_number_at_x_path_with_default(self):
        raw = _raw_value_with_expr(_expr('data.asXML().numberAtXPathWithDefault("//n", 0)'))
        findings = self._run(raw)
        assert len(findings) == 0

    def test_negative_big_decimal_at_json_path_not_in_mapping(self):
        """bigDecimalAtJsonPath has no default-capable alternative; must not be flagged."""
        raw = _raw_value_with_expr(_expr('data.asJSON().bigDecimalAtJsonPath("/amount")'))
        findings = self._run(raw)
        assert len(findings) == 0

    # --- Message format: single vs dual alternative ---

    def test_message_single_alternative(self):
        """Single-alternative: Prefer \"X\" (no second alternative)."""
        raw = _raw_value_with_expr(_expr('data.asJSON().booleanAtJsonPath("/x")'))
        findings = self._run(raw)
        assert len(findings) == 1
        msg = findings[0].message
        assert "booleanAtJsonPath" in msg
        assert "booleanAtJsonPathWithDefault" in msg
        assert 'Prefer "booleanAtJsonPathWithDefault"' in msg
        assert "stringAtJsonPathOrEmptyString" not in msg  # only for string dual-alternative
        assert "throws an exception when the target value is not found" in msg
        assert "missing values are handled explicitly" in msg
        assert "validate first if the value is required" in msg

    def test_message_dual_alternative(self):
        """Dual-alternative: Prefer \"X\" or \"Y\"."""
        raw = _raw_value_with_expr(_expr('data.asJSON().stringAtJsonPath("/x")'))
        findings = self._run(raw)
        assert len(findings) == 1
        msg = findings[0].message
        assert "stringAtJsonPath" in msg
        assert '"stringAtJsonPathWithDefault" or "stringAtJsonPathOrEmptyString"' in msg
        assert "throws an exception when the target value is not found" in msg
        assert "validate first if the value is required" in msg

    # --- CreateJson mapping location ---

    def test_createjson_mapping_location_shows_path_label(self):
        """Finding inside CreateJson mapping expr shows step name and mapping path (e.g. CreateJSON -> jsonNumberNoDefault)."""
        raw = {
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
                                            "path": {"_type": "JsonPath", "_value": "$.jsonNumberNoDefault"},
                                            "expr": _expr("data.asJSON().numberAtJsonPath(\"$.x\")"),
                                        },
                                    }
                                ],
                            },
                        },
                    }
                ],
            }
        }
        findings = self._run(raw)
        assert len(findings) == 1
        assert "CreateJSON -> jsonNumberNoDefault" in findings[0].message
        assert "-> line " not in findings[0].message

    def test_create_text_template_multi_line_locations(self):
        """CreateTextTemplate body with two unsafe calls on different lines yields findings with template-local line numbers."""
        body = (
            "line1 {{ data.asXML().stringAtXPath(\"//a\") }}\n"
            "line2\n"
            "line3 {{ data.asXML().stringAtXPath(\"//b\") }}"
        )
        raw = {
            "nodes": {
                "_type": ["List", "Node"],
                "_value": [
                    {
                        "_type": "CreateTextTemplate",
                        "_value": {
                            "name": {"_type": "Identifier", "_value": "CTT_XmlInput"},
                            "message": {"_type": "TextTemplate", "_value": body},
                        },
                    }
                ],
            }
        }
        findings = self._run(raw)
        assert len(findings) == 2
        messages = [f.message for f in findings]
        assert any("-> line 1" in m for m in messages)
        assert any("-> line 3" in m for m in messages)
        assert all("CTT_XmlInput" in m for m in messages)
        assert {f.line for f in findings} == {1, 3}

    # --- Severity ---

    def test_severity_is_advice(self):
        raw = _raw_value_with_expr(_expr('data.asJSON().stringAtJsonPath("/x")'))
        findings = self._run(raw)
        assert len(findings) == 1
        assert findings[0].rule.SEVERITY == "ADVICE"

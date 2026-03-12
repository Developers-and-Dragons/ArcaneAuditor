#!/usr/bin/env python3
"""Unit tests for OrchestrationVerboseBooleanCheckRule."""

import pytest
from parser.rules.structure.validation.orchestration_verbose_boolean_check_rule import (
    OrchestrationVerboseBooleanCheckRule,
    _is_redundant_boolean_wrapper,
)
from parser.models import ProjectContext, OrchestrationModel


def _bool_expr(source: str, is_boolean: bool = True):
    """Build a minimal expression object. By default Boolean; set is_boolean=False for non-Boolean (e.g. String)."""
    type_val = ["Expr", "Boolean"] if is_boolean else ["Expr", "String"]
    return {
        "_type": type_val,
        "_value": {
            "type": {"_type": "Type", "_value": "Boolean" if is_boolean else "String"},
            "source": {"_type": "String", "_value": source},
        },
    }


def _raw_value_with_expr(expr_obj, key: str = "condition"):
    """Put a single expression under a key inside a minimal flow-like structure (nodes -> first node -> key)."""
    return {
        "nodes": {
            "_type": ["List", "Node"],
            "_value": [
                {
                    "_type": "BranchOnConditions",
                    "_value": {
                        "name": {"_type": "Identifier", "_value": "BoC"},
                        key: expr_obj,
                        "ifBranches": {"_type": ["List", "WhenBranch"], "_value": []},
                        "elseBranch": {"_type": "ImplicitGroup", "_value": {"nodes": {"_type": ["List", "Node"], "_value": []}}},
                    },
                }
            ],
        }
    }


class TestOrchestrationVerboseBooleanCheckRule:
    """Test cases for OrchestrationVerboseBooleanCheckRule."""

    def setup_method(self):
        self.rule = OrchestrationVerboseBooleanCheckRule()
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

    # --- Positive ---

    def test_positive_if_x_true_else_false(self):
        """Positive 1: if (X) true else false yields one finding with location."""
        raw = _raw_value_with_expr(_bool_expr("(if ((data.foo == true)) true else false)"))
        findings = self._run(raw)
        assert len(findings) == 1
        assert "true else false" in findings[0].message
        assert "Location:" in findings[0].message
        # UI-style location: step reference name and field (e.g. "BoC -> Condition")
        assert "BoC" in findings[0].message and "Condition" in findings[0].message

    def test_positive_if_x_false_else_true(self):
        """Positive 2: if (X) false else true yields one finding."""
        raw = _raw_value_with_expr(_bool_expr("(if ((someBooleanExpr)) false else true)"))
        findings = self._run(raw)
        assert len(findings) == 1
        assert "false else true" in findings[0].message

    def test_positive_complex_x(self):
        """Positive 3: complex nested X with true else false yields one finding."""
        source = (
            "(if (((data.CreateValues.myBool.and(true) == true) && "
            '(data.start.request.asJSON().stringAtJsonPath("fdaf") == "fffd"))) true else false)'
        )
        raw = _raw_value_with_expr(_bool_expr(source))
        findings = self._run(raw)
        assert len(findings) == 1

    # --- Negative ---

    def test_negative_just_true(self):
        """Negative 4: Boolean expression source is just 'true' -> no finding."""
        raw = _raw_value_with_expr(_bool_expr("true"))
        findings = self._run(raw)
        assert len(findings) == 0

    def test_negative_non_boolean_expression(self):
        """Negative 5: non-Boolean expression whose source resembles the pattern -> no finding."""
        raw = _raw_value_with_expr(_bool_expr("(if ((x)) true else false)", is_boolean=False))
        findings = self._run(raw)
        assert len(findings) == 0

    def test_negative_substring_in_other_context(self):
        """Negative 6: 'true else false' only inside another context; entire expression not the wrapper -> no finding."""
        # Entire source is a string literal or different structure, not the top-level wrapper
        raw = _raw_value_with_expr(_bool_expr("something (if (x) true else false) tail"))
        findings = self._run(raw)
        assert len(findings) == 0

    def test_negative_just_false(self):
        """Boolean source just 'false' -> no finding."""
        raw = _raw_value_with_expr(_bool_expr("false"))
        findings = self._run(raw)
        assert len(findings) == 0

    # --- Generic detection in different parts of flow ---

    def test_generic_detection_different_keys(self):
        """Generic 7: redundant wrapper under different keys (condition vs expr) both detected."""
        expr_condition = _bool_expr("(if ((a)) true else false)")
        expr_expr = _bool_expr("(if ((b)) false else true)")
        raw = {
            "nodes": {
                "_type": ["List", "Node"],
                "_value": [
                    {
                        "_type": "BranchOnConditions",
                        "_value": {
                            "name": {"_type": "Identifier", "_value": "BoC1"},
                            "condition": expr_condition,
                            "ifBranches": {"_type": ["List", "WhenBranch"], "_value": []},
                            "elseBranch": {"_type": "ImplicitGroup", "_value": {"nodes": {"_type": ["List", "Node"], "_value": []}}},
                        },
                    },
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
                                            "expr": expr_expr,
                                        },
                                    }
                                ],
                            },
                        },
                    },
                ],
            }
        }
        findings = self._run(raw)
        assert len(findings) == 2

    def test_generic_nested_nodes_step_chain(self):
        """Nested nodes: location includes outer and inner step names (e.g. Loop -> InnerStep -> key)."""
        inner_expr = _bool_expr("(if ((x)) true else false)")
        raw = {
            "nodes": {
                "_type": ["List", "Node"],
                "_value": [
                    {
                        "_type": "Loop",
                        "_value": {
                            "name": {"_type": "Identifier", "_value": "Loop"},
                            "filter": {"_type": ["Opt", ["Expr", "Boolean"]], "_value": None},
                            "group": {
                                "_type": "ImplicitGroup",
                                "_value": {
                                    "nodes": {
                                        "_type": ["List", "Node"],
                                        "_value": [
                                            {
                                                "_type": "CreateValues",
                                                "_value": {
                                                    "name": {"_type": "Identifier", "_value": "CreateValues_1"},
                                                    "values": {
                                                        "_type": ["List", "Assignment"],
                                                        "_value": [
                                                            {
                                                                "_type": "Assignment",
                                                                "_value": {
                                                                    "param": {
                                                                        "_type": "Parameter",
                                                                        "_value": {
                                                                            "name": {"_type": "Identifier", "_value": "fdafdsf"},
                                                                            "type": {"_type": "Type", "_value": "Boolean"},
                                                                            "default": {"_type": ["Opt", "Any"], "_value": None},
                                                                        },
                                                                    },
                                                                    "expr": inner_expr,
                                                                },
                                                            }
                                                        ],
                                                    },
                                                },
                                            }
                                        ],
                                    }
                                },
                            },
                        },
                    }
                ],
            }
        }
        findings = self._run(raw)
        assert len(findings) == 1
        assert "Location:" in findings[0].message
        assert "Loop -> CreateValues_1 -> fdafdsf" in findings[0].message

    def test_severity_is_advice(self):
        """Finding severity is ADVICE."""
        raw = _raw_value_with_expr(_bool_expr("(if ((x)) true else false)"))
        findings = self._run(raw)
        assert len(findings) == 1
        assert findings[0].rule.SEVERITY == "ADVICE"


class TestIsRedundantBooleanWrapper:
    """Tests for _is_redundant_boolean_wrapper helper."""

    def test_accepts_with_outer_parens(self):
        assert _is_redundant_boolean_wrapper("(if ((x)) true else false)") is True

    def test_accepts_without_outer_parens(self):
        assert _is_redundant_boolean_wrapper("if ((x)) true else false") is True

    def test_accepts_false_else_true(self):
        assert _is_redundant_boolean_wrapper("if ((y)) false else true") is True

    def test_rejects_just_true(self):
        assert _is_redundant_boolean_wrapper("true") is False

    def test_rejects_substring(self):
        assert _is_redundant_boolean_wrapper("prefix if (x) true else false suffix") is False

    def test_rejects_empty(self):
        assert _is_redundant_boolean_wrapper("") is False

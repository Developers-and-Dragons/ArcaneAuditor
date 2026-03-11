#!/usr/bin/env python3
"""Unit tests for OrchestrationBranchOnConditionsNestingRule."""

import pytest
from parser.rules.structure.validation.orchestration_branch_on_conditions_nesting import (
    OrchestrationBranchOnConditionsNestingRule,
)
from parser.models import ProjectContext, OrchestrationModel


def _ident(name: str):
    return {"_type": "Identifier", "_value": name}


def _nodes_list(nodes: list):
    return {"_type": ["List", "Node"], "_value": nodes}


def _when_branch(branch_name: str, inner_nodes: list):
    """One when-branch with name and group containing inner_nodes."""
    return {
        "_type": "WhenBranch",
        "_value": {
            "name": _ident(branch_name),
            "condition": {"_type": ["Expr", "Boolean"], "_value": {"type": {"_type": "Type", "_value": "Boolean"}, "source": {"_type": "String", "_value": "true"}, "isAuto": {"_type": "Boolean", "_value": False}}},
            "group": {
                "_type": "ImplicitGroup",
                "_value": {
                    "name": _ident("_group"),
                    "nodes": _nodes_list(inner_nodes),
                },
            },
        },
    }


def _else_branch(inner_nodes: list):
    return {
        "_type": "ImplicitGroup",
        "_value": {
            "name": _ident("_else"),
            "nodes": _nodes_list(inner_nodes),
        },
    }


def _boc(name: str, if_branch_nodes: list, else_branch_nodes: list = None):
    """Build a BranchOnConditions node. if_branch_nodes is the list inside the first (and only) ifBranch's group."""
    if else_branch_nodes is None:
        else_branch_nodes = []
    return {
        "_type": "BranchOnConditions",
        "_value": {
            "name": _ident(name),
            "isDisabled": {"_type": "Boolean", "_value": False},
            "errorHandler": {"_type": ["Opt", "ErrorHandler"], "_value": None},
            "ifBranches": {"_type": ["List", "WhenBranch"], "_value": [_when_branch("IF", if_branch_nodes)]},
            "elseBranch": _else_branch(else_branch_nodes),
        },
    }


def _chain_boc(depth: int, prefix: str = "BoC"):
    """Build a chain of depth-many BoCs, each in the previous one's IF branch. Returns the top-level node."""
    if depth <= 0:
        return None
    inner = [] if depth == 1 else [_chain_boc(depth - 1, f"{prefix}_{depth - 1}")]
    return _boc(f"{prefix}_{depth}", inner)


def _raw_value(nodes: list):
    return {"nodes": _nodes_list(nodes)}


class TestOrchestrationBranchOnConditionsNestingRule:
    """Test cases for OrchestrationBranchOnConditionsNestingRule."""

    def setup_method(self):
        self.rule = OrchestrationBranchOnConditionsNestingRule()
        self.context = ProjectContext()

    def _run(self, flow_type: str, raw_value: dict, file_path: str = "test.orchestration"):
        orch = OrchestrationModel(
            flow_type=flow_type,
            id="test-id",
            name="testOrch",
            security_domains=None,
            raw_value=raw_value,
            file_path=file_path,
            source_content="",
        )
        self.context.orchestrations["test-id"] = orch
        return list(self.rule.analyze(self.context))

    def test_boc_depth_1_no_finding(self):
        """Single BoC at depth 1 (no nested BoC) yields no finding."""
        raw = _raw_value([_boc("BoC_1", [])])
        findings = self._run(".maya.FlowSync", raw)
        assert len(findings) == 0

    def test_boc_depth_2_no_finding(self):
        """Two levels of BoC yields no finding."""
        raw = _raw_value([_boc("BoC_1", [_boc("BoC_2", [])])])
        findings = self._run(".maya.FlowSync", raw)
        assert len(findings) == 0

    def test_boc_depth_3_no_finding(self):
        """Three levels of BoC yields no finding."""
        raw = _raw_value([_chain_boc(3)])
        findings = self._run(".maya.FlowSync", raw)
        assert len(findings) == 0

    def test_boc_depth_4_one_finding(self):
        """One branch that goes to 4 levels yields one finding stating 4 levels."""
        raw = _raw_value([_chain_boc(4)])
        findings = self._run(".maya.FlowSync", raw)
        assert len(findings) == 1
        assert "4 levels" in findings[0].message
        assert "suborchestration" in findings[0].message.lower()
        assert self.rule.SEVERITY == "ADVICE"

    def test_boc_depth_6_one_finding_states_six(self):
        """One branch that goes to 6 levels yields one finding stating 6 levels (not 4)."""
        raw = _raw_value([_chain_boc(6)])
        findings = self._run(".maya.FlowSync", raw)
        assert len(findings) == 1
        assert "6 levels" in findings[0].message
        assert "4 levels" not in findings[0].message

    def test_two_distinct_branches_two_findings(self):
        """Two distinct top-level branches (one at 4, one at 5 levels) yield two findings."""
        # Two top-level BoCs: first has 4-level chain, second has 5-level chain (sibling branches)
        raw = _raw_value([_chain_boc(4, "First"), _chain_boc(5, "Second")])
        findings = self._run(".maya.FlowSync", raw)
        assert len(findings) == 2
        levels = []
        for f in findings:
            if "4 levels" in f.message:
                levels.append(4)
            elif "5 levels" in f.message:
                levels.append(5)
        assert 4 in levels and 5 in levels

    def test_suborchestration_not_skipped(self):
        """Suborchestration (FlowSubflow) with branch at 4 levels yields one finding (rule applies)."""
        raw = _raw_value([_chain_boc(4)])
        findings = self._run(".maya.FlowSubflow", raw)
        assert len(findings) == 1
        assert "4 levels" in findings[0].message

    def test_finding_severity_is_advice(self):
        """Finding severity is ADVICE."""
        raw = _raw_value([_chain_boc(4)])
        findings = self._run(".maya.FlowSync", raw)
        assert len(findings) == 1
        assert findings[0].rule.SEVERITY == "ADVICE"


if __name__ == "__main__":
    pytest.main([__file__])

#!/usr/bin/env python3
"""Unit tests for OrchestrationApiStepErrorHandlerRule."""

import pytest
from parser.rules.structure.validation.orchestration_api_step_error_handler import (
    OrchestrationApiStepErrorHandlerRule,
)
from parser.models import ProjectContext, OrchestrationModel


def _node(name_val: str, node_type: str, has_error_handler: bool):
    """Build a single node with optional errorHandler."""
    err_val = {"_type": "ErrorHandler", "_value": {"name": {"_type": "Identifier", "_value": f"_err_{name_val}"}}} if has_error_handler else None
    return {
        "_type": node_type,
        "_value": {
            "name": {"_type": "Identifier", "_value": name_val},
            "errorHandler": {"_type": ["Opt", "ErrorHandler"], "_value": err_val},
        },
    }


def _nodes_list(nodes):
    """Wrap nodes in the List envelope."""
    return {"_type": ["List", "Node"], "_value": list(nodes)}


def _raw_value_main_nodes(nodes):
    """Flow raw_value with given top-level nodes."""
    return {"nodes": _nodes_list(nodes)}


def _implicit_group_nodes(nodes):
    """ImplicitGroup _value with nodes."""
    return {
        "name": {"_type": "Identifier", "_value": "_group"},
        "nodes": _nodes_list(nodes),
    }


def _loop_with_body_nodes(inner_nodes):
    """One Loop node whose group contains inner_nodes."""
    loop_value = {
        "name": {"_type": "Identifier", "_value": "Loop"},
        "errorHandler": {"_type": ["Opt", "ErrorHandler"], "_value": None},
        "group": {
            "_type": "ImplicitGroup",
            "_value": _implicit_group_nodes(inner_nodes),
        },
    }
    return {"_type": "Loop", "_value": loop_value}


def _branch_with_if_nodes(if_branch_nodes):
    """One BranchOnConditions with single if-branch containing if_branch_nodes."""
    when_branch = {
        "_type": "WhenBranch",
        "_value": {
            "name": {"_type": "Identifier", "_value": "IF"},
            "group": {
                "_type": "ImplicitGroup",
                "_value": _implicit_group_nodes(if_branch_nodes),
            },
        },
    }
    else_group = {
        "_type": "ImplicitGroup",
        "_value": {"name": {"_type": "Identifier", "_value": "_else"}, "nodes": _nodes_list([])},
    }
    branch_value = {
        "name": {"_type": "Identifier", "_value": "BranchonConditions"},
        "errorHandler": {"_type": ["Opt", "ErrorHandler"], "_value": None},
        "ifBranches": {"_type": ["List", "WhenBranch"], "_value": [when_branch]},
        "elseBranch": else_group,
    }
    return {"_type": "BranchOnConditions", "_value": branch_value}


class TestOrchestrationApiStepErrorHandlerRule:
    """Test cases for OrchestrationApiStepErrorHandlerRule."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rule = OrchestrationApiStepErrorHandlerRule()
        self.context = ProjectContext()

    def test_api_step_with_local_error_handler_no_finding(self):
        """API step (SendHttpRequest) with local error handler yields no finding."""
        raw = _raw_value_main_nodes([_node("SendHTTPRequest", "SendHttpRequest", True)])
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="o1",
            name="myOrch",
            security_domains=None,
            raw_value=raw,
            file_path="myOrch.orchestration",
            source_content="",
        )
        self.context.orchestrations["o1"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0

    def test_api_step_without_local_error_handler_yields_finding(self):
        """API step (SendWwsPaginationApiRequest) without local error handler yields one finding."""
        raw = _raw_value_main_nodes([_node("SendPagedWorkdaySOAPCall", "SendWwsPaginationApiRequest", False)])
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="o2",
            name="myOrch",
            security_domains=None,
            raw_value=raw,
            file_path="myOrch.orchestration",
            source_content="",
        )
        self.context.orchestrations["o2"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert "local" in findings[0].message.lower() or "error handler" in findings[0].message.lower()
        assert "API" in findings[0].message or "SendPagedWorkdaySOAPCall" in findings[0].message

    def test_non_api_step_without_error_handler_no_finding(self):
        """Non-API step (CreateValues) without error handler yields no finding."""
        raw = _raw_value_main_nodes([_node("CreateValues", "CreateValues", False)])
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="o3",
            name="myOrch",
            security_domains=None,
            raw_value=raw,
            file_path="myOrch.orchestration",
            source_content="",
        )
        self.context.orchestrations["o3"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0

    def test_multiple_api_steps_one_missing_yields_one_finding(self):
        """Two API steps, one with handler one without -> one finding."""
        raw = _raw_value_main_nodes([
            _node("SendHTTPRequest", "SendHttpRequest", False),
            _node("SendWorkdayAPIRequest", "SendWorkdayApiRequest", True),
        ])
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="o4",
            name="myOrch",
            security_domains=None,
            raw_value=raw,
            file_path="myOrch.orchestration",
            source_content="",
        )
        self.context.orchestrations["o4"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1

    def test_suborchestration_api_step_without_handler_yields_finding(self):
        """Suborchestration (FlowSubflow) with API step without handler yields one finding."""
        raw = _raw_value_main_nodes([_node("SendHTTPRequest", "SendHttpRequest", False)])
        orch = OrchestrationModel(
            flow_type=".maya.FlowSubflow",
            id="sub1",
            name="mySuborch",
            security_domains=None,
            raw_value=raw,
            file_path="mySuborch.suborchestration",
            source_content="",
        )
        self.context.orchestrations["sub1"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1

    def test_api_step_inside_loop_without_handler_yields_finding(self):
        """API step inside Loop body without handler yields one finding."""
        inner_nodes = [_node("SendHTTPRequest_1", "SendHttpRequest", False)]
        loop_node = _loop_with_body_nodes(inner_nodes)
        raw = _raw_value_main_nodes([loop_node])
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="o5",
            name="myOrch",
            security_domains=None,
            raw_value=raw,
            file_path="myOrch.orchestration",
            source_content="",
        )
        self.context.orchestrations["o5"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert "SendHTTPRequest_1" in findings[0].message or "API" in findings[0].message

    def test_api_step_inside_branch_without_handler_yields_finding(self):
        """API step inside Branch if-branch without handler yields one finding."""
        branch_node = _branch_with_if_nodes([_node("SendHTTPRequest_2", "SendHttpRequest", False)])
        raw = _raw_value_main_nodes([branch_node])
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="o6",
            name="myOrch",
            security_domains=None,
            raw_value=raw,
            file_path="myOrch.orchestration",
            source_content="",
        )
        self.context.orchestrations["o6"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert "SendHTTPRequest_2" in findings[0].message or "API" in findings[0].message

    def test_finding_severity_is_action(self):
        """Finding severity is ACTION."""
        raw = _raw_value_main_nodes([_node("SendHTTPRequest", "SendHttpRequest", False)])
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="o7",
            name="myOrch",
            security_domains=None,
            raw_value=raw,
            file_path="myOrch.orchestration",
            source_content="",
        )
        self.context.orchestrations["o7"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert self.rule.SEVERITY == "ACTION"
        assert findings[0].rule.SEVERITY == "ACTION"


if __name__ == "__main__":
    pytest.main([__file__])

#!/usr/bin/env python3
"""Unit tests for OrchestrationGlobalErrorHandlerRule."""

import pytest
from parser.rules.structure.validation.orchestration_global_error_handler import (
    OrchestrationGlobalErrorHandlerRule,
)
from parser.models import ProjectContext, OrchestrationModel


def _raw_value_without_global_handler():
    """Flow-level errorHandler null (no global handler)."""
    return {"errorHandler": {"_type": ["Opt", "ErrorHandler"], "_value": None}}


def _raw_value_with_global_handler():
    """Flow-level errorHandler present (has global handler)."""
    return {
        "errorHandler": {
            "_type": ["Opt", "ErrorHandler"],
            "_value": {"_type": "ErrorHandler", "_value": {"name": {"_type": "Identifier", "_value": "globalErr"}}},
        }
    }


def _raw_value_sync_with_err_hnd_style():
    """Like syncWithErrHnd.orchestration: FlowSync, global null, node has errorHandler."""
    return {
        "errorHandler": {"_type": ["Opt", "ErrorHandler"], "_value": None},
        "nodes": {
            "_type": ["List", "Node"],
            "_value": [
                {
                    "_type": "CreateValues",
                    "_value": {
                        "name": {"_type": "Identifier", "_value": "CreateValues"},
                        "errorHandler": {
                            "_type": ["Opt", "ErrorHandler"],
                            "_value": {"_type": "ErrorHandler", "_value": {"name": {"_type": "Identifier", "_value": "_errorHandler_CreateValues"}}},
                        },
                    },
                }
            ],
        },
    }


class TestOrchestrationGlobalErrorHandlerRule:
    """Test cases for OrchestrationGlobalErrorHandlerRule."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rule = OrchestrationGlobalErrorHandlerRule()
        self.context = ProjectContext()

    def test_sync_without_global_error_handler_yields_finding(self):
        """Sync flow with no global error handler yields a finding."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="sync-1",
            name="mySync",
            security_domains=None,
            raw_value=_raw_value_without_global_handler(),
            file_path="mySync.orchestration",
            source_content="",
        )
        self.context.orchestrations["sync-1"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert "global" in findings[0].message.lower() or "error handler" in findings[0].message.lower()
        assert findings[0].line == 1
        assert self.rule.SEVERITY == "ACTION"

    def test_sync_with_global_error_handler_no_finding(self):
        """Sync flow with global error handler yields nothing."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="sync-2",
            name="syncWithGlobal",
            security_domains=None,
            raw_value=_raw_value_with_global_handler(),
            file_path="syncWithGlobal.orchestration",
            source_content="",
        )
        self.context.orchestrations["sync-2"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0

    def test_sync_with_err_hnd_style_node_only_handler_yields_finding(self):
        """Sync with node-level error handler but no global handler yields finding (syncWithErrHnd case)."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="sync-3",
            name="syncWithErrHnd",
            security_domains=None,
            raw_value=_raw_value_sync_with_err_hnd_style(),
            file_path="syncWithErrHnd.orchestration",
            source_content="",
        )
        self.context.orchestrations["sync-3"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert "global" in findings[0].message.lower() or "error handler" in findings[0].message.lower()

    def test_async_without_global_yields_finding(self):
        """Async flow with no global error handler yields a finding."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowAsync",
            id="async-1",
            name="myAsync",
            security_domains=None,
            raw_value=_raw_value_without_global_handler(),
            file_path="myAsync.orchestration",
            source_content="",
        )
        self.context.orchestrations["async-1"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1

    def test_async_with_global_no_finding(self):
        """Async flow with global error handler yields nothing."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowAsync",
            id="async-2",
            name="asyncFull",
            security_domains=None,
            raw_value=_raw_value_with_global_handler(),
            file_path="asyncFull.orchestration",
            source_content="",
        )
        self.context.orchestrations["async-2"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0

    def test_suborchestration_skipped_no_finding(self):
        """Suborchestration (FlowSubflow) with no global handler yields no finding (rule skipped)."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowSubflow",
            id="sub-1",
            name="mySubflow",
            security_domains=None,
            raw_value=_raw_value_without_global_handler(),
            file_path="mySubflow.suborchestration",
            source_content="",
        )
        self.context.orchestrations["sub-1"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0

    def test_bpt_without_global_yields_finding(self):
        """BPT flow with no global error handler yields a finding."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowBusinessProcessTriggered",
            id="bp-1",
            name="myBP",
            security_domains=None,
            raw_value=_raw_value_without_global_handler(),
            file_path="myBP.orchestration",
            source_content="",
        )
        self.context.orchestrations["bp-1"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1

    def test_bpt_with_global_no_finding(self):
        """BPT flow with global error handler yields nothing."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowBusinessProcessTriggered",
            id="bp-2",
            name="bpWithGlobal",
            security_domains=None,
            raw_value=_raw_value_with_global_handler(),
            file_path="bpWithGlobal.orchestration",
            source_content="",
        )
        self.context.orchestrations["bp-2"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0

    def test_integration_without_global_yields_finding(self):
        """Integration flow with no global error handler yields a finding."""
        orch = OrchestrationModel(
            flow_type=".maya.IntegrationFrameworkTrigger",
            id="o4i-1",
            name="myIntegration",
            security_domains=None,
            raw_value=_raw_value_without_global_handler(),
            file_path="o4i.orchestration",
            source_content="",
        )
        self.context.orchestrations["o4i-1"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1

    def test_integration_with_global_no_finding(self):
        """Integration flow with global error handler yields nothing."""
        orch = OrchestrationModel(
            flow_type=".maya.IntegrationFrameworkTrigger",
            id="o4i-2",
            name="integrationWithGlobal",
            security_domains=None,
            raw_value=_raw_value_with_global_handler(),
            file_path="integrationWithGlobal.orchestration",
            source_content="",
        )
        self.context.orchestrations["o4i-2"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0

    def test_finding_severity_is_action(self):
        """Finding severity is ACTION."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="sev",
            name="sevTest",
            security_domains=None,
            raw_value=_raw_value_without_global_handler(),
            file_path="sev.orchestration",
            source_content="",
        )
        self.context.orchestrations["sev"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert findings[0].rule.SEVERITY == "ACTION"


if __name__ == "__main__":
    pytest.main([__file__])

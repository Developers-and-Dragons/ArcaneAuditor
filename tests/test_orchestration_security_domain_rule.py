#!/usr/bin/env python3
"""Unit tests for OrchestrationSecurityDomainRule."""

import pytest
from parser.rules.structure.validation.orchestration_security_domain import OrchestrationSecurityDomainRule
from parser.models import ProjectContext, OrchestrationModel


class TestOrchestrationSecurityDomainRule:
    """Test cases for OrchestrationSecurityDomainRule."""

    def setup_method(self):
        """Set up test fixtures."""
        self.rule = OrchestrationSecurityDomainRule()
        self.context = ProjectContext()

    def test_sync_empty_security_domains_yields_finding(self):
        """Sync flow with missing or empty securityDomains yields a finding."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="sync-1",
            name="mySync",
            security_domains=None,
            raw_value={},
            file_path="mySync.orchestration",
            source_content="",
        )
        self.context.orchestrations["sync-1"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert "security" in findings[0].message.lower() or "securityDomains" in findings[0].message
        assert findings[0].line in (0, 1)
        assert "mySync" in findings[0].message or "orchestration" in findings[0].message.lower()

    def test_sync_non_empty_security_domains_no_finding(self):
        """Sync flow with non-empty securityDomains yields nothing."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowSync",
            id="sync-2",
            name="syncWithDomains",
            security_domains=["SomeDomain"],
            raw_value={},
            file_path="syncWithDomains.orchestration",
            source_content="",
        )
        self.context.orchestrations["sync-2"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0

    def test_async_empty_security_domains_yields_finding(self):
        """Async flow with empty securityDomains yields a finding."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowAsync",
            id="async-1",
            name="myAsync",
            security_domains=[],
            raw_value={},
            file_path="myAsync.orchestration",
            source_content="",
        )
        self.context.orchestrations["async-1"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1

    def test_async_non_empty_security_domains_no_finding(self):
        """Async flow with non-empty securityDomains yields nothing."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowAsync",
            id="async-2",
            name="asyncFull",
            security_domains=["OrchSecurityDomain"],
            raw_value={},
            file_path="asyncFull.orchestration",
            source_content="",
        )
        self.context.orchestrations["async-2"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0

    def test_bp_flow_ignored_regardless_of_security_domains(self):
        """Business Process Triggered flow yields no finding even with empty securityDomains."""
        orch = OrchestrationModel(
            flow_type=".maya.FlowBusinessProcessTriggered",
            id="bp-1",
            name="myBP",
            security_domains=None,
            raw_value={},
            file_path="myBP.orchestration",
            source_content="",
        )
        self.context.orchestrations["bp-1"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0

    def test_integration_flow_ignored_regardless_of_security_domains(self):
        """Integration flow yields no finding even with empty securityDomains."""
        orch = OrchestrationModel(
            flow_type=".maya.IntegrationFrameworkTrigger",
            id="o4i-1",
            name="myIntegration",
            security_domains=None,
            raw_value={},
            file_path="o4i.orchestration",
            source_content="",
        )
        self.context.orchestrations["o4i-1"] = orch
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0


if __name__ == "__main__":
    pytest.main([__file__])

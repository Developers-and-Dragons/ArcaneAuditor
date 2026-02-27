#!/usr/bin/env python3
"""Integration tests for all structure rules."""

import pytest
from parser.rules.structure.widgets.widget_id_required import WidgetIdRequiredRule
from parser.rules.structure.widgets.widget_id_lower_camel_case import WidgetIdLowerCamelCaseRule
from parser.rules.structure.endpoints.endpoint_name_lower_camel_case import EndpointNameLowerCamelCaseRule
from parser.rules.structure.endpoints.endpoint_fail_on_status_codes import EndpointFailOnStatusCodesRule
from parser.rules.structure.endpoints.endpoint_url_base_url_type import EndpointBaseUrlTypeRule
from parser.rules.structure.validation.footer_pod_required import FooterPodRequiredRule
from parser.rules.structure.validation.string_boolean import StringBooleanRule
from parser.rules.structure.validation.hardcoded_wid import HardcodedWidRule
from parser.rules.structure.validation.pmd_security_domain import PMDSecurityDomainRule
from parser.rules.structure.validation.orchestration_security_domain import OrchestrationSecurityDomainRule
from parser.rules.base import Finding
from parser.models import ProjectContext, PMDModel, PMDPresentation


class TestAllStructureRulesIntegration:
    """Integration tests for all structure rules."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.context = ProjectContext()
        
        # Create a PMD model with various structure violations
        self.pmd_model = PMDModel(
            pageId="test-page",
            presentation=PMDPresentation(
                body={"children": [{"type": "text", "value": "test"}]}
            ),
            inboundEndpoints=[{"name": "GetData", "url": "test"}],
            outboundEndpoints=[{"name": "PostData", "url": "test"}],
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = self.pmd_model
    
    def test_all_rules_can_be_instantiated(self):
        """Test that all structure rules can be instantiated."""
        rules = [
            WidgetIdRequiredRule(),
            WidgetIdLowerCamelCaseRule(),
            EndpointNameLowerCamelCaseRule(),
            EndpointFailOnStatusCodesRule(),
            EndpointBaseUrlTypeRule(),
            FooterPodRequiredRule(),
            StringBooleanRule(),
            HardcodedWidRule(),
            PMDSecurityDomainRule(),
            OrchestrationSecurityDomainRule(),
        ]
        
        # Test that all rules have required attributes
        for rule in rules:
            assert hasattr(rule, 'ID')
            assert hasattr(rule, 'DESCRIPTION')
            assert hasattr(rule, 'SEVERITY')
            assert hasattr(rule, 'analyze')
            # ID is now either RULE000 (base class) or class name (ValidationRule)
            assert rule.ID in ('RULE000', 'WidgetIdLowerCamelCaseRule', 'EndpointNameLowerCamelCaseRule', 'HardcodedWidRule', 'OrchestrationSecurityDomainRule')
    
    def test_all_rules_analyze_method(self):
        """Test that all rules can analyze without errors."""
        rules = [
            WidgetIdRequiredRule(),
            WidgetIdLowerCamelCaseRule(),
            EndpointNameLowerCamelCaseRule(),
            EndpointFailOnStatusCodesRule(),
            EndpointBaseUrlTypeRule(),
            FooterPodRequiredRule(),
            StringBooleanRule(),
            HardcodedWidRule(),
            PMDSecurityDomainRule(),
            OrchestrationSecurityDomainRule(),
        ]
        
        # Test that all rules can analyze without throwing exceptions
        for rule in rules:
            try:
                findings = list(rule.analyze(self.context))
                # Should return a list of Finding objects or empty list
                assert isinstance(findings, list)
                for finding in findings:
                    assert isinstance(finding, Finding)
            except Exception as e:
                pytest.fail(f"Rule {rule.ID} failed to analyze: {e}")


if __name__ == '__main__':
    pytest.main([__file__])

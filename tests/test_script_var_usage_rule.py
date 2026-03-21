#!/usr/bin/env python3
"""Unit tests for ScriptVarUsageRule."""

import pytest
from parser.rules.script.core.var_usage import ScriptVarUsageRule
from parser.models import ProjectContext, PMDModel, ScriptModel, WQLQueryModel


class TestScriptVarUsageRule:
    """Test cases for ScriptVarUsageRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptVarUsageRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "var" in self.rule.DESCRIPTION.lower()
    
    def test_analyze_no_pmds(self):
        """Test analysis when no PMD models exist."""
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0
    
    def test_analyze_pmd_with_var_declaration(self):
        """Test analysis when PMD contains 'var' declarations."""
        pmd_model = PMDModel(
            pageId="test-page",
            script="<% var x = 1; var y = 2; %>",
            file_path="test.pmd"
        )
        self.context.pmds["test-page"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 2
        assert all(f.rule_id == "ScriptVarUsageRule" for f in findings)

    def test_analyze_standalone_script_with_var_declaration(self):
        """Test analysis when standalone script contains 'var' declarations."""
        script_content = """var getCurrentTime = function() {
    return date:now();
};

var helper = function() {
    return "helper";
};

{
  "getCurrentTime": getCurrentTime,
  "helper": helper
}"""
        
        script_model = ScriptModel(source=script_content, file_path="util.script")
        self.context.scripts["util.script"] = script_model
        
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 2  # Should find both var declarations
        assert all(f.rule_id == "ScriptVarUsageRule" for f in findings)
        assert all("var" in f.message.lower() for f in findings)
        assert all("const" in f.message.lower() or "let" in f.message.lower() for f in findings)

    def test_analyze_wqlquery_offset_with_var_declaration(self):
        """Test analysis when a WQL query offset contains 'var' declarations."""
        wql_model = WQLQueryModel(
            id="getWorkersHiredAfter",
            parameters=["offsetParam"],
            query="SELECT worker FROM workersForHCMReporting(dataSourceFilter=allActiveWorkers)",
            offset="<% var offset = offsetParam; offset %>",
            limit="<% offsetParam %>",
            file_path="getWorkersHiredAfter.wqlquery",
            source_content='{"id":"getWorkersHiredAfter","offset":"<% var offset = offsetParam; offset %>"}'
        )
        self.context.wqlqueries["getWorkersHiredAfter"] = wql_model

        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert findings[0].rule_id == "ScriptVarUsageRule"


if __name__ == '__main__':
    pytest.main([__file__])

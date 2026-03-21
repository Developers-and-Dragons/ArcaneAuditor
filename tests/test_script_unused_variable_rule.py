#!/usr/bin/env python3
"""Unit tests for ScriptUnusedVariableRule."""

import pytest
from parser.rules.script.unused_code.unused_variables import ScriptUnusedVariableRule
from parser.models import ProjectContext, PMDModel


class TestScriptUnusedVariableRule:
    """Test cases for ScriptUnusedVariableRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = ScriptUnusedVariableRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "RULE000"  # Base class default
        assert self.rule.SEVERITY == "ADVICE"
        assert "variable" in self.rule.DESCRIPTION.lower()
    
    def test_unused_variable_in_onsend_script(self):
        """Test that unused variables in onSend scripts are detected."""
        script_content = """<%
            const isFoo = true;
        %>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"outboundEndpoints": [{"name": "postData", "onSend": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}]}',
            outboundEndpoints=[{
                "name": "postData",
                "onSend": script_content
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find unused variable isFoo
        assert len(findings) >= 1
        assert any("isFoo" in f.message for f in findings)
    
    def test_unused_variable_in_main_script(self):
        """Test that unused variables in main script field are detected."""
        script_content = """<%
            const unusedVar = 42;
            const usedVar = 10;
            console.debug(usedVar);
        %>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find unused variable unusedVar
        assert len(findings) >= 1
        assert any("unusedVar" in f.message for f in findings)
    
    def test_used_variables_not_flagged(self):
        """Test that used variables are not flagged."""
        script_content = """<%
            const maxLength = 10;
            const result = getData(maxLength);
            return result;
        %>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations - all variables are used
        assert len(findings) == 0

    def test_variable_used_in_handlebar_syntax_not_flagged(self):
        """Test that variables used in handlebar syntax ({{variable}}) are not flagged as unused."""
        script_content = """<%
            const foo = 1;
            const bar = `The number is {{foo}}`;
            return bar;
        %>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations - foo is used in the template literal, bar is returned
        assert len(findings) == 0, f"Expected no findings, but got: {[f.message for f in findings]}"

    def test_variable_used_in_handlebar_syntax_complex(self):
        """Test that variables used in handlebar syntax with property access are not flagged."""
        script_content = """<%
            const user = { name: "John" };
            const message = `Hello {{user.name}}`;
            return message;
        %>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations - user is used in the template literal, message is returned
        assert len(findings) == 0, f"Expected no findings, but got: {[f.message for f in findings]}"
    
    def test_variable_used_in_handlebar_but_container_unused(self):
        """Test that variables used in handlebar syntax are not flagged even if the containing variable is unused."""
        script_content = """<%
            const foo = 1;
            const bar = `The number is {{foo}}`;
        %>"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content='{"script": "' + script_content.replace('\n', '\\n').replace('"', '\\"') + '"}'
        )
        pmd_model.script = script_content
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # foo should NOT be flagged (it's used in the template literal)
        # bar may be flagged (it's unused), but that's correct behavior
        foo_findings = [f for f in findings if 'foo' in f.message]
        assert len(foo_findings) == 0, f"Expected 'foo' not to be flagged, but got: {[f.message for f in foo_findings]}"


if __name__ == '__main__':
    pytest.main([__file__])

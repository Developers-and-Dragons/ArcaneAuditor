#!/usr/bin/env python3
"""Unit tests for HardcodedWidRule."""

import pytest
from parser.rules.structure.validation.hardcoded_wid import HardcodedWidRule
from parser.models import ProjectContext, PMDModel


class TestHardcodedWidRule:
    """Test cases for HardcodedWidRule class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rule = HardcodedWidRule()
        self.context = ProjectContext()
    
    def test_rule_metadata(self):
        """Test rule metadata is correctly set."""
        assert self.rule.ID == "HardcodedWidRule"  # ValidationRule uses class name
        assert self.rule.SEVERITY == "ADVICE"
        assert "wid" in self.rule.DESCRIPTION.lower()
    
    def test_hardcoded_wid_in_script(self):
        """Test that hardcoded WIDs in scripts are detected."""
        source_content = """{
  "id": "testPage",
  "script": "<%
    const workerWid = '1a2b3c4d5e6f7890abcdef1234567890';
    const jobWid = 'f0e1d2c3b4a59687abcd1234ef567890';
  %>"
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            script="<%\n    const workerWid = '1a2b3c4d5e6f7890abcdef1234567890';\n    const jobWid = 'f0e1d2c3b4a59687abcd1234ef567890';\n  %>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find both WIDs
        assert len(findings) == 2
        wid_messages = [f.message for f in findings]
        assert any('1a2b3c4d5e6f7890abcdef1234567890' in msg for msg in wid_messages)
        assert any('f0e1d2c3b4a59687abcd1234ef567890' in msg for msg in wid_messages)
    
    def test_hardcoded_wid_in_endpoint_url(self):
        """Test that hardcoded WIDs in endpoint URLs are detected."""
        source_content = """{
  "id": "testPage",
  "inboundEndpoints": [{
    "name": "getWorker",
    "url": "/workers/a1b2c3d4e5f6708192a3b4c5d6e7f890"
  }]
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            inboundEndpoints=[{
                "name": "getWorker",
                "url": "/workers/a1b2c3d4e5f6708192a3b4c5d6e7f890"
            }]
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find the WID in URL
        assert len(findings) == 1
        assert 'a1b2c3d4e5f6708192a3b4c5d6e7f890' in findings[0].message
    
    def test_no_hardcoded_wids(self):
        """Test that PMD without hardcoded WIDs has no violations."""
        source_content = """{
  "id": "testPage",
  "script": "<%
    const workerWid = appAttr.defaultWorkerWid;
    const result = getData(workerWid);
  %>"
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            script="<%\n    const workerWid = appAttr.defaultWorkerWid;\n    const result = getData(workerWid);\n  %>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations
        assert len(findings) == 0
    
    def test_short_hex_strings_not_flagged(self):
        """Test that short hex strings (not 32 chars) are not flagged as WIDs."""
        source_content = """{
  "id": "testPage",
  "script": "<%
    const shortId = 'abc123';
    const color = '#ff00ff';
  %>"
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            script="<%\n    const shortId = 'abc123';\n    const color = '#ff00ff';\n  %>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations - these aren't 32-character WIDs
        assert len(findings) == 0
    
    def test_wid_in_widget_values(self):
        """Test that hardcoded WIDs in widget values are detected."""
        source_content = """{
  "id": "testPage",
  "presentation": {
    "body": {
      "type": "text",
      "value": "Worker ID: 9f8e7d6c5b4a3210fedcba0987654321"
    }
  }
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            presentation={
                "body": {
                    "type": "text",
                    "value": "Worker ID: 9f8e7d6c5b4a3210fedcba0987654321"
                }
            }
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find the WID in widget value
        assert len(findings) == 1
        assert '9f8e7d6c5b4a3210fedcba0987654321' in findings[0].message
    
    def test_commented_wids_not_flagged(self):
        """Test that WIDs in comments are not flagged (AST ignores comments)."""
        source_content = """{
  "id": "testPage",
  "script": "<%
    // Old approach: const oldWid = '1a2b3c4d5e6f7890abcdef1234567890';
    /* Legacy: const legacyWid = 'f0e1d2c3b4a59687abcd1234ef567890'; */
    
    const workerWid = appAttr.workerWid;
  %>"
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            script="<%\n    // Old approach: const oldWid = '1a2b3c4d5e6f7890abcdef1234567890';\n    /* Legacy: const legacyWid = 'f0e1d2c3b4a59687abcd1234ef567890'; */\n    \n    const workerWid = appAttr.workerWid;\n  %>"
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should have no violations - WIDs are in comments
        assert len(findings) == 0
    
    def test_wid_in_instance_list(self):
        """Test that WIDs in instanceList JSON values are detected."""
        source_content = """{
  "id": "testPage",
  "presentation": {
    "body": {
      "type": "instanceList",
      "instanceList": [
        {"id": "a1b2c3d4e5f6708192a3b4c5d6e7f890", "descriptor": "USA"},
        {"id": "b2c3d4e5f6a70819f3e4d5c6b7a89012", "descriptor": "Canada"}
      ]
    }
  }
}"""
        
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            presentation={
                "body": {
                    "type": "instanceList",
                    "instanceList": [
                        {"id": "a1b2c3d4e5f6708192a3b4c5d6e7f890", "descriptor": "USA"},
                        {"id": "b2c3d4e5f6a70819f3e4d5c6b7a89012", "descriptor": "Canada"}
                    ]
                }
            }
        )
        self.context.pmds["testPage"] = pmd_model
        
        findings = list(self.rule.analyze(self.context))
        
        # Should find both WIDs in instanceList
        assert len(findings) == 2
        wid_messages = [f.message for f in findings]
        assert any('a1b2c3d4e5f6708192a3b4c5d6e7f890' in msg for msg in wid_messages)
        assert any('b2c3d4e5f6a70819f3e4d5c6b7a89012' in msg for msg in wid_messages)

    def test_wid_field_returns_finding_by_default(self):
        """By default, hardcoded WID in task/report link 'wid' field is reported."""
        source_content = '{"id": "testPage", "presentation": {"body": {"type": "taskLink", "wid": "a1b2c3d4e5f6708192a3b4c5d6e7f890"}}}'
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            presentation={"body": {"type": "taskLink", "wid": "a1b2c3d4e5f6708192a3b4c5d6e7f890"}},
        )
        self.context.pmds["testPage"] = pmd_model
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert "a1b2c3d4e5f6708192a3b4c5d6e7f890" in findings[0].message

    def test_wid_field_ignored_when_allow_task_report_link_wids_true(self):
        """When allow_wid_in_task_report_link_fields is True, WIDs in 'wid' field are not reported."""
        source_content = '{"id": "testPage", "presentation": {"body": {"type": "taskLink", "wid": "a1b2c3d4e5f6708192a3b4c5d6e7f890"}}}'
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            presentation={"body": {"type": "taskLink", "wid": "a1b2c3d4e5f6708192a3b4c5d6e7f890"}},
        )
        self.context.pmds["testPage"] = pmd_model
        self.rule.apply_settings({"allow_wid_in_task_report_link_fields": True})
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 0

    def test_other_fields_still_checked_when_allow_task_report_link_wids_true(self):
        """When allow_wid_in_task_report_link_fields is True, only 'wid' field is exempt; other fields still report."""
        source_content = '{"id": "testPage", "presentation": {"body": {"type": "section", "children": [{"type": "text", "value": "WID: b2c3d4e5f6a70819f3e4d5c6b7a89012"}]}, "wid": "a1b2c3d4e5f6708192a3b4c5d6e7f890"}}'
        pmd_model = PMDModel(
            pageId="testPage",
            file_path="test.pmd",
            source_content=source_content,
            presentation={
                "body": {
                    "type": "section",
                    "children": [{"type": "text", "value": "WID: b2c3d4e5f6a70819f3e4d5c6b7a89012"}],
                },
                "wid": "a1b2c3d4e5f6708192a3b4c5d6e7f890",
            },
        )
        self.context.pmds["testPage"] = pmd_model
        self.rule.apply_settings({"allow_wid_in_task_report_link_fields": True})
        findings = list(self.rule.analyze(self.context))
        # Should still report the WID in body.children[0].value, not the one in "wid"
        assert len(findings) == 1
        assert "b2c3d4e5f6a70819f3e4d5c6b7a89012" in findings[0].message

    def test_hardcoded_wid_in_wqlquery(self):
        """Test that hardcoded WIDs in WQL query files are detected."""
        from parser.models import WQLQueryModel
        wql_model = WQLQueryModel(
            id="getWorkersHiredAfter",
            parameters=["locationId"],
            query='SELECT worker FROM workers WHERE countryWid = "a1b2c3d4e5f6708192a3b4c5d6e7f890"',
            offset="<% offsetParam %>",
            limit="<% limitParam %>",
            file_path="getWorkersHiredAfter.wqlquery",
            source_content='{"id":"getWorkersHiredAfter","query":"SELECT worker FROM workers WHERE countryWid = \\"a1b2c3d4e5f6708192a3b4c5d6e7f890\\""}',
        )
        self.context.wqlqueries["getWorkersHiredAfter"] = wql_model
        findings = list(self.rule.analyze(self.context))
        assert len(findings) == 1
        assert "a1b2c3d4e5f6708192a3b4c5d6e7f890" in findings[0].message
        assert "wqlquery" in findings[0].file_path


if __name__ == '__main__':
    pytest.main([__file__])

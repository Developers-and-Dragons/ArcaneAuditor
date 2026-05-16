"""
Unit tests for the ModelParser class.
"""
import pytest
import json
from unittest.mock import Mock
from parser.app_parser import ModelParser
from parser.models import ProjectContext


class TestModelParser:
    """Test cases for ModelParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ModelParser()
        self.mock_source_file = Mock()
        self.mock_source_file.content = "test content"
    
    def test_init(self):
        """Test parser initialization."""
        assert self.parser.supported_extensions == {'.pmd', '.script', '.amd', '.pod', '.smd', '.wqlquery', '.orchestration', '.suborchestration'}
    
    def test_parse_files_empty_map(self):
        """Test parsing empty source files map."""
        result = self.parser.parse_files({})
        assert isinstance(result, ProjectContext)
        assert len(result.pmds) == 0
        assert len(result.scripts) == 0
        assert result.amd is None
    
    def test_parse_pmd_file_json_success(self):
        """Test successful JSON parsing of PMD file with sample.pmd structure."""
        # Mock PMD content as JSON matching sample.pmd structure
        pmd_content = json.dumps({
            "id": "testPage",
            "securityDomains": ["domain1"],
            "endPoints": [
                {
                    "name": "getCurrentWorker",
                    "url": "/workers/me"
                }
            ],
            "presentation": {
                "title": {
                    "type": "title",
                    "label": "Test Page"
                },
                "body": {
                    "type": "section",
                    "children": [
                        {
                            "type": "text",
                            "id": "hello",
                            "label": "Hello World!",
                            "value": "Welcome!"
                        }
                    ]
                },
                "footer": {
                    "type": "footer",
                    "children": [
                        {
                            "type": "richText",
                            "value": "Powered By Workday Extend"
                        }
                    ]
                }
            },
            "onLoad": "<% pageVariables.isTrue = true; %>",
            "script": "<% const y = 2; %>",
            "include": ["util.script"],
            "outboundData": {
                "outboundEndPoints": [
                    {
                        "name": "postData",
                        "url": "/api/data"
                    }
                ]
            }
        })
        
        mock_file = Mock()
        mock_file.content = pmd_content
        
        context = ProjectContext()
        self.parser._parse_pmd_file("test.pmd", mock_file, context)
        
        assert "test.pmd" in context.pmds
        pmd_model = context.pmds["test.pmd"]
        assert pmd_model.pageId == "testPage"
        assert pmd_model.securityDomains == ["domain1"]
        assert pmd_model.inboundEndpoints == [{"name": "getCurrentWorker", "url": "/workers/me"}]
        assert pmd_model.outboundEndpoints == [{"name": "postData", "url": "/api/data"}]
        assert pmd_model.onLoad == "<% pageVariables.isTrue = true; %>"
        assert pmd_model.script == "<% const y = 2; %>"
        
        # Check presentation structure
        assert pmd_model.presentation is not None
        
        # title
        assert pmd_model.presentation.title["type"] == "title"
        assert pmd_model.presentation.title["label"] == "Test Page"
        
        # body
        assert len(pmd_model.presentation.body.get("children")) == 1  # body children
        assert pmd_model.presentation.body.get("type") == "section"
        
        children = pmd_model.presentation.body.get("children")
        assert len(children) == 1
        assert children[0].get("type") == "text"
        assert children[0].get("label") == "Hello World!"
        assert children[0].get("value") == "Welcome!"
        
        # footer 
        assert pmd_model.presentation.footer["children"][0]["type"] == "richText"

        # Check includes
        assert pmd_model.includes is not None
        assert pmd_model.includes.scripts == ["util.script"]
    
    def test_parse_pmd_file_minimal_structure(self):
        """Test PMD file parsing with minimal structure."""
        # Mock PMD content with minimal required fields
        pmd_content = json.dumps({
            "id": "minimalPage",
            "presentation": {
                "body": {
                    "type": "section",
                    "children": [
                        {
                            "type": "text",
                            "id": "hello",
                            "label": "Hello World!",
                            "value": "Welcome!"
                        }
                    ]
                }
            }
        })
        
        mock_file = Mock()
        mock_file.content = pmd_content
        
        context = ProjectContext()
        self.parser._parse_pmd_file("minimal.pmd", mock_file, context)
        
        assert "minimal.pmd" in context.pmds
        pmd_model = context.pmds["minimal.pmd"]
        assert pmd_model.pageId == "minimalPage"
        assert pmd_model.presentation is not None
        assert pmd_model.presentation.body.get("type") == "section"
        assert len(pmd_model.presentation.body.get("children")) == 1
        assert pmd_model.presentation.body.get("children")[0].get("type") == "text"
        assert pmd_model.presentation.body.get("children")[0].get("label") == "Hello World!"
        assert pmd_model.presentation.body.get("children")[0].get("value") == "Welcome!"
    
    def test_parse_pmd_file_json_fallback(self):
        """Test PMD file parsing fails when JSON is invalid."""
        # Mock PMD content as plain text
        pmd_content = "This is not JSON\nonLoad: <% pageVariables.isTrue = true; %>\nscript: <% const y = 2; %>"
        
        mock_file = Mock()
        mock_file.content = pmd_content
        
        context = ProjectContext()
        
        # Should raise JSONDecodeError when JSON parsing fails
        with pytest.raises(json.JSONDecodeError):
            self.parser._parse_pmd_file("test.pmd", mock_file, context)
    
    def test_parse_script_file(self):
        """Test script file parsing."""
        script_content = "var x = 1;\nfunction test() { return x; }"
        
        mock_file = Mock()
        mock_file.content = script_content
        
        context = ProjectContext()
        self.parser._parse_script_file("utils.script", mock_file, context)
        
        assert "utils.script" in context.scripts
        script_model = context.scripts["utils.script"]
        assert script_model.source == script_content
        assert script_model.file_path == "utils.script"
    
    def test_parse_script_file_with_export(self):
        """Test script file parsing with JSON export structure like util.script."""
        script_content = """const getCurrentTime = function() {
  return date:getTodaysDate(date:getDateTimeZone('US/Pacific'));
};

{
  "getCurrentTime": getCurrentTime
}"""
        
        mock_file = Mock()
        mock_file.content = script_content
        
        context = ProjectContext()
        self.parser._parse_script_file("util.script", mock_file, context)
        
        assert "util.script" in context.scripts
        script_model = context.scripts["util.script"]
        assert script_model.source == script_content
        assert script_model.file_path == "util.script"
    
    def test_parse_amd_file_json_success(self):
        """Test successful JSON parsing of AMD file."""
        amd_content = json.dumps({
            "routes": {
                "main": {"pageId": "mainPage", "parameters": []}
            },
            "baseUrls": {"api": "/api/v1"}
        })
        
        mock_file = Mock()
        mock_file.content = amd_content
        
        context = ProjectContext()
        self.parser._parse_amd_file("app.amd", mock_file, context)
        
        assert context.amd is not None
        assert context.amd.routes["main"].pageId == "mainPage"
        assert context.amd.baseUrls["api"] == "/api/v1"
    
    def test_parse_amd_file_json_fallback(self):
        """Test AMD file parsing fails when JSON is invalid."""
        amd_content = "This is not valid JSON"
        
        mock_file = Mock()
        mock_file.content = amd_content
        
        context = ProjectContext()
        
        # Should raise JSONDecodeError when JSON parsing fails
        with pytest.raises(json.JSONDecodeError):
            self.parser._parse_amd_file("app.amd", mock_file, context)

    def test_parse_wqlquery_file_json_success(self):
        """Test successful JSON parsing of WQL query file."""
        wql_content = json.dumps({
            "id": "getWorkersHiredAfter",
            "parameters": ["locationId", "hireDate", "offsetParam", "limitParam"],
            "query": "SELECT worker FROM workersForHCMReporting(dataSourceFilter=allActiveWorkers) WHERE location in (\"<% locationId %>\")",
            "offset": "<% const offset = offsetParam; offset %>",
            "limit": "<% limitParam %>"
        })

        mock_file = Mock()
        mock_file.content = wql_content

        context = ProjectContext()
        self.parser._parse_single_file("getWorkersHiredAfter.wqlquery", mock_file, context)

        assert hasattr(context, "wqlqueries")
        assert "getWorkersHiredAfter" in context.wqlqueries
        wql_model = context.wqlqueries["getWorkersHiredAfter"]
        assert wql_model.id == "getWorkersHiredAfter"
        assert wql_model.parameters == ["locationId", "hireDate", "offsetParam", "limitParam"]
        assert "<% locationId %>" in wql_model.query
        assert "<% limitParam %>" in wql_model.limit

    def test_parse_orchestration_file_sync(self):
        """Test successful parsing of .orchestration file (Synchronous flow)."""
        orch_content = '{"flowVersion":"3.3.0","_type":"Flow","_value":{"id":{"_type":"String","_value":"sync-id-1"},"name":{"_type":"Identifier","_value":"mySyncFlow"},"type":{"_type":"FlowType","_value":".maya.FlowSync"},"start":{},"end":{},"nodes":{"_type":["List","Node"],"_value":[]},"securityDomains":{"_type":["Opt",["List","String"]],"_value":null}}}'
        mock_file = Mock()
        mock_file.content = orch_content
        context = ProjectContext()
        self.parser._parse_single_file("mySync.orchestration", mock_file, context)
        assert hasattr(context, "orchestrations")
        assert len(context.orchestrations) == 1
        orch = list(context.orchestrations.values())[0]
        assert orch.flow_type == ".maya.FlowSync"
        assert orch.name == "mySyncFlow"
        assert orch.id == "sync-id-1"
        assert orch.security_domains is None
        assert "nodes" in orch.raw_value

    def test_parse_orchestration_file_integration(self):
        """Test successful parsing of .orchestration file (Integration flow)."""
        orch_content = '{"flowVersion":"3.3.0","_type":"Flow","_value":{"id":{"_type":"String","_value":"o4i-id-1"},"name":{"_type":"Identifier","_value":"myIntegration"},"type":{"_type":"FlowType","_value":".maya.IntegrationFrameworkTrigger"},"start":{},"end":{},"nodes":{"_type":["List","Node"],"_value":[]},"securityDomains":{"_type":["Opt",["List","String"]],"_value":null}}}'
        mock_file = Mock()
        mock_file.content = orch_content
        context = ProjectContext()
        self.parser._parse_single_file("o4i.orchestration", mock_file, context)
        assert "o4i.orchestration" in context.orchestrations
        orch = context.orchestrations["o4i.orchestration"]
        assert orch.flow_type == ".maya.IntegrationFrameworkTrigger"
        assert orch.name == "myIntegration"

    def test_parse_suborchestration_file(self):
        """Test successful parsing of .suborchestration file (FlowSubflow)."""
        suborch_content = json.dumps({
            "flowVersion": "3.3.0",
            "_type": "Flow",
            "_value": {
                "id": {"_type": "String", "_value": "sub-id-1"},
                "name": {"_type": "Identifier", "_value": "subOrch"},
                "type": {"_type": "FlowType", "_value": ".maya.FlowSubflow"},
                "start": {"_type": "StartSubflow", "_value": {"parameters": {"_type": ["List", "ExprParameter"], "_value": []}}},
                "end": {"_type": "EndSubflow", "_value": {"exports": {"_type": ["List", "Assignment"], "_value": []}}},
                "nodes": {"_type": ["List", "Node"], "_value": []},
                "securityDomains": {"_type": ["Opt", ["List", "String"]], "_value": None},
            },
        })
        mock_file = Mock()
        mock_file.content = suborch_content
        context = ProjectContext()
        self.parser._parse_single_file("subOrch.suborchestration", mock_file, context)
        assert hasattr(context, "orchestrations")
        assert "subOrch.suborchestration" in context.orchestrations
        orch = context.orchestrations["subOrch.suborchestration"]
        assert orch.flow_type == ".maya.FlowSubflow"
        assert orch.name == "subOrch"
        assert "start" in orch.raw_value
        start = orch.raw_value["start"]
        assert isinstance(start, dict) and start.get("_type") == "StartSubflow"

    def test_parse_orchestration_file_with_security_domains(self):
        """Test parsing orchestration with non-empty securityDomains."""
        orch_content = json.dumps({
            "flowVersion": "3.3.0",
            "_type": "Flow",
            "_value": {
                "id": {"_type": "String", "_value": "async-1"},
                "name": {"_type": "Identifier", "_value": "asyncFull"},
                "type": {"_type": "FlowType", "_value": ".maya.FlowAsync"},
                "start": {},
                "end": {},
                "nodes": {"_type": ["List", "Node"], "_value": []},
                "securityDomains": {
                    "_type": ["Opt", ["List", "String"]],
                    "_value": {
                        "_type": ["List", "String"],
                        "_value": [{"_type": "String", "_value": "OrchSecurityDomain"}],
                    },
                },
            },
        })
        mock_file = Mock()
        mock_file.content = orch_content
        context = ProjectContext()
        self.parser._parse_single_file("asyncFull.orchestration", mock_file, context)
        orch = context.orchestrations["asyncFull.orchestration"]
        assert orch.security_domains == ["OrchSecurityDomain"]

    def test_parse_orchestration_file_multiline_normalization(self):
        """Test that pretty-printed (multi-line) orchestration parses identically to single-line."""
        single_line = '{"flowVersion":"3.3.0","_type":"Flow","_value":{"id":{"_type":"String","_value":"norm-id"},"name":{"_type":"Identifier","_value":"normFlow"},"type":{"_type":"FlowType","_value":".maya.FlowSync"},"start":{},"end":{},"nodes":{"_type":["List","Node"],"_value":[]},"securityDomains":{"_type":["Opt",["List","String"]],"_value":null}}}'
        pretty = json.dumps(json.loads(single_line), indent=2)
        assert "\n" in pretty
        mock_single = Mock()
        mock_single.content = single_line
        mock_pretty = Mock()
        mock_pretty.content = pretty
        context_single = ProjectContext()
        context_pretty = ProjectContext()
        self.parser._parse_single_file("a.orchestration", mock_single, context_single)
        self.parser._parse_single_file("b.orchestration", mock_pretty, context_pretty)
        o_single = list(context_single.orchestrations.values())[0]
        o_pretty = list(context_pretty.orchestrations.values())[0]
        assert o_single.flow_type == o_pretty.flow_type == ".maya.FlowSync"
        assert o_single.name == o_pretty.name == "normFlow"
        assert o_single.security_domains == o_pretty.security_domains
        assert "nodes" in o_pretty.raw_value
    
    def test_parse_single_file_pmd(self):
        """Test single file parsing for PMD files."""
        pmd_content = '{"id": "testPage", "presentation": {"body": {"type": "section", "children": [{"type": "text", "id": "hello", "label": "Hello World!", "value": "Welcome!"}]}}}'
        
        mock_file = Mock()
        mock_file.content = pmd_content
        
        context = ProjectContext()
        self.parser._parse_single_file("test.pmd", mock_file, context)

        assert "test.pmd" in context.pmds

    def test_parse_single_file_script(self):
        """Test single file parsing for script files."""
        mock_file = Mock()
        mock_file.content = "const x = 1;"
        
        context = ProjectContext()
        self.parser._parse_single_file("utils.script", mock_file, context)
        
        assert "utils.script" in context.scripts
    
    def test_parse_single_file_amd(self):
        """Test single file parsing for AMD files."""
        amd_content = '{"routes": {}}'
        
        mock_file = Mock()
        mock_file.content = amd_content
        
        context = ProjectContext()
        self.parser._parse_single_file("app.amd", mock_file, context)
        
        assert context.amd is not None
    
    def test_parse_single_file_unsupported_extension(self):
        """Test parsing of unsupported file extensions."""
        mock_file = Mock()
        mock_file.content = "some content"
        
        context = ProjectContext()
        
        # Should raise JSONDecodeError when POD parsing fails (no fallback)
        with pytest.raises(json.JSONDecodeError):
            self.parser._parse_single_file("test.pod", mock_file, context)
    
    def test_parse_files_with_errors(self):
        """Test parsing files with some parsing errors."""
        source_files_map = {
            "valid.pmd": Mock(content='{"id": "valid", "presentation": {"body": {"type": "section", "children": [{"type": "text", "id": "hello", "label": "Hello World!", "value": "Welcome!"}]}}}'),
            "invalid.pmd": Mock(content="invalid json content"),
            "valid.script": Mock(content="var x = 1;")
        }
        
        # Mock the _parse_single_file method to simulate an error
        original_method = self.parser._parse_single_file
        
        def mock_parse_with_error(file_path, source_file, context):
            if file_path == "invalid.pmd":
                raise Exception("JSON parse error")
            return original_method(file_path, source_file, context)
        
        self.parser._parse_single_file = mock_parse_with_error
        
        try:
            result = self.parser.parse_files(source_files_map)
            
            # Should continue processing other files
            assert "valid.pmd" in result.pmds
            assert "valid.script" in result.scripts
            assert len(result.parsing_errors) == 1
            assert "invalid.pmd" in result.parsing_errors[0]
            
        finally:
            # Restore original method
            self.parser._parse_single_file = original_method
    
    def test_parse_files_integration(self):
        """Test full integration of parsing multiple files."""
        source_files_map = {
            "main.pmd": Mock(content='{"id": "mainPage", "presentation": {"body": {"type": "section", "children": [{"type": "text", "id": "hello", "label": "Hello World!", "value": "Welcome!"}]}}, "onLoad": "var x = 1;"}'),
            "utils.script": Mock(content="var y = 2;"),
            "app.amd": Mock(content='{"routes": {"main": {"pageId": "mainPage"}}}')
        }
        
        result = self.parser.parse_files(source_files_map)
        
        # Check all files were parsed
        assert "main.pmd" in result.pmds
        assert "utils.script" in result.scripts
        assert result.amd is not None
        assert result.amd.routes["main"].pageId == "mainPage"
        
        # Check no parsing errors
        assert len(result.parsing_errors) == 0


if __name__ == "__main__":
    pytest.main([__file__])

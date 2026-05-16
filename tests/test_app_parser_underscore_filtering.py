"""Unit tests for underscore key filtering in ModelParser."""

import pytest
from parser.app_parser import ModelParser
from parser.models import ProjectContext


class TestUnderscoreKeyFiltering:
    """Test cases for filtering commented-out JSON keys (starting with underscore)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ModelParser()

    def test_filter_commented_keys_simple_dict(self):
        """Test filtering simple dictionary with underscore keys."""
        data = {
            "type": "text",
            "label": "Active Field",
            "_render": "<% foo.bar.baz %>",
            "_tempField": "ignored"
        }
        
        filtered = self.parser._filter_commented_keys(data)
        
        expected = {
            "type": "text",
            "label": "Active Field"
        }
        assert filtered == expected

    def test_filter_commented_keys_nested_objects(self):
        """Test filtering nested objects with underscore keys."""
        data = {
            "widget": {
                "_commented": "value",
                "active": True,
                "nested": {
                    "_ignored": "should be removed",
                    "valid": "should remain"
                }
            },
            "_rootCommented": "removed"
        }
        
        filtered = self.parser._filter_commented_keys(data)
        
        expected = {
            "widget": {
                "active": True,
                "nested": {
                    "valid": "should remain"
                }
            }
        }
        assert filtered == expected

    def test_filter_commented_keys_arrays(self):
        """Test filtering arrays containing objects with underscore keys."""
        data = [
            {"_temp": 1, "real": 2},
            {"normal": "value"},
            {"_commented": "ignored", "active": True}
        ]
        
        filtered = self.parser._filter_commented_keys(data)
        
        expected = [
            {"real": 2},
            {"normal": "value"},
            {"active": True}
        ]
        assert filtered == expected

    def test_filter_commented_keys_primitive_values(self):
        """Test that primitive values are returned unchanged."""
        assert self.parser._filter_commented_keys("string") == "string"
        assert self.parser._filter_commented_keys(123) == 123
        assert self.parser._filter_commented_keys(True) == True
        assert self.parser._filter_commented_keys(None) == None

    def test_filter_commented_keys_empty_structures(self):
        """Test filtering empty structures."""
        assert self.parser._filter_commented_keys({}) == {}
        assert self.parser._filter_commented_keys([]) == []

    def test_filter_commented_keys_all_underscore_keys(self):
        """Test filtering when all keys start with underscore."""
        data = {
            "_temp": "value1",
            "_ignored": "value2",
            "_commented": "value3"
        }
        
        filtered = self.parser._filter_commented_keys(data)
        assert filtered == {}

    def test_filter_commented_keys_no_underscore_keys(self):
        """Test filtering when no keys start with underscore."""
        data = {
            "normal": "value1",
            "active": "value2",
            "valid": "value3"
        }
        
        filtered = self.parser._filter_commented_keys(data)
        assert filtered == data  # Should be unchanged

    def test_filter_commented_keys_deeply_nested(self):
        """Test filtering deeply nested structures."""
        data = {
            "level1": {
                "_ignored1": "removed",
                "level2": {
                    "_ignored2": "removed",
                    "level3": {
                        "_ignored3": "removed",
                        "valid": "kept"
                    }
                }
            }
        }
        
        filtered = self.parser._filter_commented_keys(data)
        
        expected = {
            "level1": {
                "level2": {
                    "level3": {
                        "valid": "kept"
                    }
                }
            }
        }
        assert filtered == expected


class TestPMDFileFiltering:
    """Test PMD file parsing with underscore keys."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ModelParser()

    def test_pmd_widget_underscore_keys_ignored(self):
        """Test that PMD widgets with underscore keys are filtered out."""
        from file_processing.models import SourceFile
        
        pmd_content = '''{
  "id": "testPage",
  "presentation": {
    "body": {
      "widgets": [{
        "type": "text",
        "label": "Active Field",
        "_render": "<% foo.bar.baz.boo %>",
        "_tempField": "ignored"
      }]
    }
  }
}'''
        
        from pathlib import Path
        source_file = SourceFile(Path("test.pmd"), pmd_content, len(pmd_content.encode('utf-8')))
        context = ProjectContext()
        
        # Parse the file
        self.parser._parse_single_file("test.pmd", source_file, context)
        
        # Verify the PMD was parsed
        assert "test.pmd" in context.pmds
        pmd_model = context.pmds["test.pmd"]

        # Verify the widget was parsed but underscore keys were filtered out
        widgets = pmd_model.presentation.body["widgets"]
        widget = widgets[0]
        assert widget["type"] == "text"
        assert widget["label"] == "Active Field"
        assert "_render" not in widget
        assert "_tempField" not in widget

    def test_pmd_presentation_underscore_keys_ignored(self):
        """Test that PMD presentation-level underscore keys are filtered out."""
        from file_processing.models import SourceFile
        
        pmd_content = '''{
  "id": "testPage",
  "presentation": {
    "_tempConfig": "ignored",
    "title": {
      "label": "Page Title",
      "_hiddenTitle": "ignored"
    },
    "body": {}
  },
  "_globalTemp": "ignored"
}'''
        
        from pathlib import Path
        source_file = SourceFile(Path("test.pmd"), pmd_content, len(pmd_content.encode('utf-8')))
        context = ProjectContext()
        
        # Parse the file
        self.parser._parse_single_file("test.pmd", source_file, context)
        
        # Verify the PMD was parsed
        assert "test.pmd" in context.pmds
        pmd_model = context.pmds["test.pmd"]

        # Verify underscore keys were filtered out
        assert "_tempConfig" not in pmd_model.presentation.model_dump()
        assert "_globalTemp" not in pmd_model.model_dump()
        assert "_hiddenTitle" not in pmd_model.presentation.title


class TestPODFileFiltering:
    """Test POD file parsing with underscore keys."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ModelParser()

    def test_pod_seed_underscore_keys_ignored(self):
        """Test that POD seed data with underscore keys are filtered out."""
        from file_processing.models import SourceFile
        
        pod_content = '''{
  "podId": "testPod",
  "seed": {
    "_tempConfig": "ignored",
    "parameters": ["activeParam", "_tempParam"],
    "template": {
      "type": "widget",
      "_hiddenConfig": "ignored"
    }
  }
}'''
        
        from pathlib import Path
        source_file = SourceFile(Path("test.pod"), pod_content, len(pod_content.encode('utf-8')))
        context = ProjectContext()
        
        # Parse the file
        self.parser._parse_single_file("test.pod", source_file, context)
        
        # Verify the POD was parsed
        assert "test.pod" in context.pods
        pod_model = context.pods["test.pod"]
        
        # Verify underscore keys were filtered out
        seed_data = pod_model.seed.model_dump()
        assert "_tempConfig" not in seed_data
        
        # Check parameters
        parameters = pod_model.seed.parameters
        assert "activeParam" in parameters
        # Note: "_tempParam" is an array element, not a dictionary key, so it's not filtered
        # The filtering only applies to dictionary keys starting with underscore
        
        # Check template
        template = pod_model.seed.template
        assert template["type"] == "widget"
        assert "_hiddenConfig" not in template


class TestAMDFileFiltering:
    """Test AMD file parsing with underscore keys."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ModelParser()

    def test_amd_underscore_keys_ignored(self):
        """Test that AMD file underscore keys are filtered out."""
        from file_processing.models import SourceFile
        
        amd_content = '''{
  "_tempConfig": "ignored",
  "routes": {
    "_tempRoute": {
      "pageId": "tempPage"
    },
    "activeRoute": {
      "pageId": "activePage",
      "_tempConfig": "ignored"
    }
  },
  "baseUrls": {
    "_tempUrl": "ignored",
    "api": "https://api.example.com"
  }
}'''
        
        from pathlib import Path
        source_file = SourceFile(Path("test.amd"), amd_content, len(amd_content.encode('utf-8')))
        context = ProjectContext()
        
        # Parse the file
        self.parser._parse_single_file("test.amd", source_file, context)
        
        # Verify the AMD was parsed
        assert context.amd is not None
        amd_model = context.amd
        
        # Verify underscore keys were filtered out
        routes = amd_model.routes
        assert "_tempRoute" not in routes  # Should be filtered out
        assert "activeRoute" in routes
        assert routes["activeRoute"].pageId == "activePage"
        # The _tempConfig should be filtered out from the activeRoute
        
        base_urls = amd_model.baseUrls
        assert "_tempUrl" not in base_urls
        assert "api" in base_urls


class TestSMDFileFiltering:
    """Test SMD file parsing with underscore keys."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ModelParser()

    def test_smd_underscore_keys_ignored(self):
        """Test that SMD file underscore keys are filtered out."""
        from file_processing.models import SourceFile
        
        smd_content = '''{
  "id": "testSite",
  "applicationId": "testApp",
  "siteId": "testSite",
  "_tempConfig": "ignored",
  "languages": [
    {"code": "en", "name": "English"},
    {"code": "es", "name": "Spanish", "_tempLang": "ignored"}
  ],
  "siteAuth": {
    "_tempAuth": "ignored",
    "type": "oauth"
  },
  "_hiddenConfig": "ignored"
}'''
        
        from pathlib import Path
        source_file = SourceFile(Path("test.smd"), smd_content, len(smd_content.encode('utf-8')))
        context = ProjectContext()
        
        # Parse the file
        self.parser._parse_single_file("test.smd", source_file, context)
        
        # Verify the SMD was parsed
        assert context.smd is not None
        smd_model = context.smd
        
        # Verify underscore keys were filtered out
        assert smd_model.id == "testSite"
        assert smd_model.applicationId == "testApp"
        assert smd_model.siteId == "testSite"
        assert len(smd_model.languages) == 2
        assert smd_model.languages[0]["code"] == "en"
        assert smd_model.languages[1]["code"] == "es"
        assert "_tempLang" not in smd_model.languages[1]  # Should be filtered out
        
        # The model should not have access to underscore keys
        model_dict = smd_model.model_dump()
        assert "_tempConfig" not in model_dict
        assert "_hiddenConfig" not in model_dict


class TestRuleBehaviorWithFiltering:
    """Test that rules no longer flag commented-out content."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ModelParser()


    def test_hardcoded_wid_rule_ignores_commented_content(self):
        """Test that HardcodedWidRule doesn't flag commented WIDs."""
        from file_processing.models import SourceFile
        from parser.rules.structure.validation.hardcoded_wid import HardcodedWidRule
        
        pmd_content = '''{
  "id": "testPage",
  "presentation": {
    "body": {
      "widgets": [{
        "type": "text",
        "label": "Active Field",
        "_widgetId": "1a2b3c4d5e6f7890abcdef1234567890"
      }]
    }
  }
}'''
        
        from pathlib import Path
        source_file = SourceFile(Path("test.pmd"), pmd_content, len(pmd_content.encode('utf-8')))
        context = ProjectContext()
        
        # Parse the file
        self.parser._parse_single_file("test.pmd", source_file, context)
        
        # Run the hardcoded WID rule
        rule = HardcodedWidRule()
        findings = list(rule.analyze(context))
        
        # Should not find any violations since the WID is in a commented field
        assert len(findings) == 0


class TestEdgeCases:
    """Test edge cases for underscore key filtering."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ModelParser()

    def test_unicode_underscore_characters(self):
        """Test that only ASCII underscore is considered, not Unicode variants."""
        data = {
            "_normal": "removed",
            "＿unicode": "kept",  # Full-width underscore
            "normal": "kept"
        }
        
        filtered = self.parser._filter_commented_keys(data)
        
        expected = {
            "＿unicode": "kept",  # Should be kept
            "normal": "kept"
        }
        assert filtered == expected

    def test_mixed_case_underscore_keys(self):
        """Test that only lowercase underscore prefix is filtered."""
        data = {
            "_lowercase": "removed",
            "_UPPERCASE": "removed", 
            "_MixedCase": "removed",
            "normal": "kept"
        }
        
        filtered = self.parser._filter_commented_keys(data)
        
        expected = {
            "normal": "kept"
        }
        assert filtered == expected

    def test_empty_objects_after_filtering(self):
        """Test handling of objects that become empty after filtering."""
        data = {
            "valid": {
                "_temp": "removed"
            },
            "_commented": "removed"
        }
        
        filtered = self.parser._filter_commented_keys(data)
        
        expected = {
            "valid": {}
        }
        assert filtered == expected

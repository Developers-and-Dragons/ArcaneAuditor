"""Unit tests for FileNameLowerCamelCaseRule."""

from parser.rules.structure.validation.file_name_lower_camel_case import FileNameLowerCamelCaseRule
from parser.models import PMDModel, PodModel, ScriptModel, AMDModel, SMDModel, ProjectContext, WQLQueryModel


class TestFileNameLowerCamelCaseRule:
    """Test cases for FileNameLowerCamelCaseRule."""

    def test_rule_initialization(self):
        """Test that the rule initializes correctly."""
        rule = FileNameLowerCamelCaseRule()
        assert rule.ID == "FileNameLowerCamelCaseRule"
        assert rule.DESCRIPTION == "Ensures all file names follow lowerCamelCase naming convention"
        assert rule.SEVERITY == "ADVICE"

    def test_get_description(self):
        """Test that get_description returns the correct description."""
        rule = FileNameLowerCamelCaseRule()
        assert rule.get_description() == rule.DESCRIPTION

    def test_valid_pmd_filename(self):
        """Test that valid lowerCamelCase PMD filenames pass."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "myPage.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_invalid_pmd_filename_pascal_case(self):
        """Test that PascalCase PMD filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "MyPage.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "MyPage.pmd" in findings[0].message
        assert "lowerCamelCase" in findings[0].message
        assert findings[0].file_path == "MyPage.pmd"

    def test_invalid_pmd_filename_snake_case(self):
        """Test that snake_case PMD filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "my_page.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "my_page.pmd" in findings[0].message
        assert "lowerCamelCase" in findings[0].message

    def test_invalid_pmd_filename_uppercase(self):
        """Test that UPPERCASE PMD filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "MYPAGE.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "MYPAGE.pmd" in findings[0].message

    def test_valid_pod_filename(self):
        """Test that valid lowerCamelCase POD filenames pass."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pod_data = {
            "podId": "footerPod",
            "seed": {},
            "file_path": "footer.pod"
        }
        pod_model = PodModel(**pod_data)
        context.pods = {"footerPod": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_invalid_pod_filename(self):
        """Test that invalid POD filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pod_data = {
            "podId": "footerPod",
            "seed": {},
            "file_path": "Footer_Pod.pod"
        }
        pod_model = PodModel(**pod_data)
        context.pods = {"footerPod": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Footer_Pod.pod" in findings[0].message

    def test_valid_script_filename(self):
        """Test that valid lowerCamelCase Script filenames pass."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        script_data = {
            "source": "function test() { }",
            "file_path": "helperFunctions.script"
        }
        script_model = ScriptModel(**script_data)
        context.scripts = {"helperFunctions": script_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_invalid_script_filename(self):
        """Test that invalid Script filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        script_data = {
            "source": "function test() { }",
            "file_path": "helper_functions.script"
        }
        script_model = ScriptModel(**script_data)
        context.scripts = {"helper_functions": script_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "helper_functions.script" in findings[0].message

    def test_multiple_invalid_filenames(self):
        """Test that multiple invalid filenames are all flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        # Add multiple files with invalid names
        pmd_data = {
            "pageId": "testPage",
            "file_path": "My_Page.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        pod_data = {
            "podId": "footerPod",
            "seed": {},
            "file_path": "Footer_Pod.pod"
        }
        pod_model = PodModel(**pod_data)
        context.pods = {"footerPod": pod_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 2
        assert any("My_Page.pmd" in f.message for f in findings)
        assert any("Footer_Pod.pod" in f.message for f in findings)

    def test_valid_wqlquery_filename(self):
        """Test that valid lowerCamelCase WQL query filenames pass."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()

        wql_model = WQLQueryModel(
            id="getWorkersHiredAfter",
            parameters=[],
            query="SELECT worker FROM workersForHCMReporting(dataSourceFilter=allActiveWorkers)",
            file_path="getWorkersHiredAfter.wqlquery"
        )
        context.wqlqueries = {"getWorkersHiredAfter": wql_model}

        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_invalid_wqlquery_filename(self):
        """Test that invalid WQL query filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()

        wql_model = WQLQueryModel(
            id="getWorkersHiredAfter",
            parameters=[],
            query="SELECT worker FROM workersForHCMReporting(dataSourceFilter=allActiveWorkers)",
            file_path="Get_Workers_Hired_After.wqlquery"
        )
        context.wqlqueries = {"getWorkersHiredAfter": wql_model}

        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "Get_Workers_Hired_After.wqlquery" in findings[0].message

    def test_filename_with_numbers_valid(self):
        """Test that filenames with numbers following lowerCamelCase are valid."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "myPage2.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_filename_starting_with_number_invalid(self):
        """Test that filenames starting with numbers are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "2myPage.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "2myPage.pmd" in findings[0].message

    def test_single_lowercase_letter_filename_valid(self):
        """Test that a single lowercase letter filename is valid."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "a.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_filename_with_path_components(self):
        """Test that filenames with path components are handled correctly."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        pmd_data = {
            "pageId": "testPage",
            "file_path": "presentation/MyPage.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "MyPage.pmd" in findings[0].message

    def test_filename_with_underscore_prefix_not_stripped(self):
        """Test that single-letter or short prefixes with underscores are not stripped as UUIDs."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        # e_TestArrayNesting.pmd should NOT have 'e_' stripped (it's not a UUID)
        # It should be flagged because it contains an underscore and doesn't follow lowerCamelCase
        pmd_data = {
            "pageId": "testPage",
            "file_path": "e_TestArrayNesting.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1, "Should flag e_TestArrayNesting.pmd as invalid (contains underscore)"
        assert "e_TestArrayNesting.pmd" in findings[0].message, "Error message should contain the original filename"
        assert "lowerCamelCase" in findings[0].message

    def test_uuid_prefix_stripped_correctly(self):
        """Test that actual UUID prefixes are correctly stripped before validation."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        # Valid UUID prefix should be stripped, leaving valid lowerCamelCase filename
        pmd_data = {
            "pageId": "testPage",
            "file_path": "50356922-5e0c-454f-a39a-2b8ca88c379c_myPage.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0, "UUID prefix should be stripped, leaving valid lowerCamelCase filename"

    def test_valid_amd_filename(self):
        """Test that valid lowerCamelCase AMD filenames pass."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        amd_data = {
            "routes": {},
            "file_path": "myApp.amd"
        }
        amd_model = AMDModel(**amd_data)
        context.amd = amd_model
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_invalid_amd_filename(self):
        """Test that invalid AMD filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        amd_data = {
            "routes": {},
            "file_path": "My_App.amd"
        }
        amd_model = AMDModel(**amd_data)
        context.amd = amd_model
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "My_App.amd" in findings[0].message
        assert "lowerCamelCase" in findings[0].message

    def test_valid_smd_filename(self):
        """Test that valid lowerCamelCase SMD filenames pass."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        smd_data = {
            "id": "testSite",
            "applicationId": "testApp",
            "siteId": "testSite",
            "file_path": "mySite.smd"
        }
        smd_model = SMDModel(**smd_data)
        context.smd = smd_model
        
        findings = list(rule.analyze(context))
        assert len(findings) == 0

    def test_invalid_smd_filename(self):
        """Test that invalid SMD filenames are flagged."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        smd_data = {
            "id": "testSite",
            "applicationId": "testApp",
            "siteId": "testSite",
            "file_path": "My_Site.smd"
        }
        smd_model = SMDModel(**smd_data)
        context.smd = smd_model
        
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert "My_Site.smd" in findings[0].message
        assert "lowerCamelCase" in findings[0].message

    def test_amd_and_smd_missing_no_error(self):
        """Test that missing AMD and SMD files don't cause errors."""
        rule = FileNameLowerCamelCaseRule()
        context = ProjectContext()
        
        # Add a PMD file
        pmd_data = {
            "pageId": "testPage",
            "file_path": "myPage.pmd"
        }
        pmd_model = PMDModel(**pmd_data)
        context.pmds = {"testPage": pmd_model}
        
        # Don't set context.amd or context.smd (they remain None)
        findings = list(rule.analyze(context))
        # Should only check PMD, no errors for missing AMD/SMD
        assert len(findings) == 0


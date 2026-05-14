"""JSONPath helper + end-to-end `path` field on Finding.

The repo already produces internal dotted paths (script field_paths from
`_extract_script_fields` and widget_paths in widget rules).
"""
from parser.models import PMDModel, PodModel, ProjectContext, SMDModel
from parser.rules.common import Violation
from parser.rules.script.core.var_usage import ScriptVarUsageRule
from parser.rules.structure.widgets.widget_id_required import WidgetIdRequiredRule
from utils.jsonpath import dotted_to_jsonpath


class TestDottedToJsonPath:
    def test_none_returns_none(self):
        assert dotted_to_jsonpath(None) is None

    def test_empty_returns_none(self):
        assert dotted_to_jsonpath("") is None

    def test_single_segment(self):
        assert dotted_to_jsonpath("script") == "$.script"

    def test_two_segments(self):
        assert dotted_to_jsonpath("body.primaryLayout") == "$.body.primaryLayout"

    def test_numeric_segment_becomes_bracket(self):
        assert dotted_to_jsonpath("body.children.0.onLoad") == "$.body.children[0].onLoad"

    def test_trailing_numeric(self):
        assert dotted_to_jsonpath("body.children.2") == "$.body.children[2]"

    def test_multiple_numerics(self):
        assert (
            dotted_to_jsonpath("body.children.1.columns.0.cellTemplate")
            == "$.body.children[1].columns[0].cellTemplate"
        )

    def test_already_jsonpath_passthrough(self):
        # If someone hands us a JSONPath-shaped string (starts with $), don't double-prefix.
        assert dotted_to_jsonpath("$.foo.bar") == "$.foo.bar"


class TestViolationCarriesPath:
    def test_violation_default_path_is_none(self):
        assert Violation(message="m", line=1).path is None

    def test_violation_accepts_path(self):
        v = Violation(message="m", line=1, path="body.children.0.onLoad")
        assert v.path == "body.children.0.onLoad"


class TestScriptRuleEmitsJsonPath:
    def test_pmd_script_field_path_becomes_jsonpath(self):
        rule = ScriptVarUsageRule()
        context = ProjectContext()
        # PMD with var in onLoad — _extract_script_fields produces "onLoad" path.
        context.pmds["p"] = PMDModel(
            pageId="p",
            onLoad="<% var x = 1; %>",
            file_path="p.pmd",
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].path == "$.onLoad"

    def test_nested_script_field_path_includes_brackets(self):
        rule = ScriptVarUsageRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            presentation={
                "body": {
                    "children": [
                        {"type": "text", "onLoad": "<% var x = 1; %>"},
                    ]
                }
            },
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        # The dotted path includes the nested numeric index.
        assert findings[0].path is not None
        assert "[0]" in findings[0].path
        assert findings[0].path.startswith("$.")
        assert findings[0].path.endswith(".onLoad")

    def test_standalone_script_file_path_is_none(self):
        # .script files have no natural path.
        from parser.models import ScriptModel

        rule = ScriptVarUsageRule()
        context = ProjectContext()
        context.scripts["s"] = ScriptModel(
            file_path="s.script", source="var x = 1;"
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].path is None


class TestWidgetRuleEmitsJsonPath:
    def test_widget_id_required_emits_jsonpath(self):
        rule = WidgetIdRequiredRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            presentation={
                "body": {
                    "children": [
                        {"type": "text"},  # missing id
                    ]
                }
            },
        )
        findings = list(rule.analyze(context))
        assert any(f.path and "[0]" in f.path for f in findings)

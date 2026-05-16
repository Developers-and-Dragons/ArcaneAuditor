"""Actionable rules populate `suggested_replacement` on Finding.

Wired rules opt in incrementally. Rules without a wired replacement
(including all `human_review` rules) leave the field `None`.
"""
import pytest

from parser.models import ProjectContext, PMDModel, SMDModel
from parser.rules.common import Violation
from parser.rules.script.core.var_usage import ScriptVarUsageRule
from parser.rules.structure.validation.hardcoded_application_id import HardcodedApplicationIdRule
from parser.rules.structure.validation.string_boolean import StringBooleanRule


class TestViolationCarriesReplacement:
    def test_violation_default_is_none(self):
        v = Violation(message="m", line=1)
        assert v.suggested_replacement is None

    def test_violation_accepts_explicit_value(self):
        v = Violation(message="m", line=1, suggested_replacement="let")
        assert v.suggested_replacement == "let"


class TestScriptVarUsageRule:
    def test_var_finding_suggests_let(self):
        rule = ScriptVarUsageRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            script="<% var x = 1; %>",
            file_path="p.pmd",
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == "let"


class TestHardcodedApplicationIdRule:
    def test_finding_suggests_site_applicationid(self):
        rule = HardcodedApplicationIdRule()
        context = ProjectContext()
        context.smd = SMDModel(
            id="app", applicationId="template_nkhlsq", siteId="s", file_path="x.smd"
        )
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            source_content='{\n  "applicationId": "template_nkhlsq"\n}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) >= 1
        assert all(f.suggested_replacement == "site.applicationId" for f in findings)


class TestStringBooleanRule:
    def test_string_true_finding_suggests_unquoted_true(self):
        rule = StringBooleanRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            source_content='{\n  "visible": "true"\n}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == "true"

    def test_string_false_finding_suggests_unquoted_false(self):
        rule = StringBooleanRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            source_content='{\n  "enabled": "false"\n}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == "false"


class TestScriptConsoleLogRule:
    def test_console_log_finding_suggests_commented_line(self):
        from parser.rules.script.core.console_log import ScriptConsoleLogRule

        rule = ScriptConsoleLogRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            script="<%\n  console.info('hello');\n%>",
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == "// console.info('hello');"

    def test_console_log_preserves_inner_indentation(self):
        from parser.rules.script.core.console_log import ScriptConsoleLogRule

        rule = ScriptConsoleLogRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            script="<%\nif (x) {\n    console.debug(x);\n}\n%>",
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == "    // console.debug(x);"


class TestScriptStringConcatRule:
    def test_concat_finding_suggests_pmd_template_literal(self):
        from parser.rules.script.logic.string_concat import ScriptStringConcatRule

        rule = ScriptStringConcatRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            script="<% var greeting = 'hello ' + name; %>",
        )
        findings = list(rule.analyze(context))
        assert len(findings) >= 1
        assert findings[0].suggested_replacement == "`hello {{name}}`"

    def test_concat_finding_suggests_multi_operand_template(self):
        from parser.rules.script.logic.string_concat import ScriptStringConcatRule

        rule = ScriptStringConcatRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            script="<% var s = 'a=' + a + ', b=' + b; %>",
        )
        findings = list(rule.analyze(context))
        assert len(findings) >= 1
        assert findings[0].suggested_replacement == "`a={{a}}, b={{b}}`"


class TestScriptVerboseBooleanCheckRule:
    def test_verbose_ternary_suggests_variable(self):
        from parser.rules.script.logic.verbose_boolean import ScriptVerboseBooleanCheckRule

        rule = ScriptVerboseBooleanCheckRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            script="<% var y = x ? true : false; %>",
        )
        findings = list(rule.analyze(context))
        assert len(findings) >= 1
        assert findings[0].suggested_replacement == "x"

    def test_verbose_ternary_inverted_suggests_negation(self):
        from parser.rules.script.logic.verbose_boolean import ScriptVerboseBooleanCheckRule

        rule = ScriptVerboseBooleanCheckRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            script="<% var y = x ? false : true; %>",
        )
        findings = list(rule.analyze(context))
        assert len(findings) >= 1
        assert findings[0].suggested_replacement == "!x"


class TestScriptUnusedIncludesRule:
    def test_unused_include_suggests_deletion(self):
        """Unused include emits empty-string replacement signaling 'remove this entry'."""
        from parser.rules.script.unused_code.unused_script_includes import ScriptUnusedIncludesRule
        from parser.models import PMDIncludes

        rule = ScriptUnusedIncludesRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            includes=PMDIncludes(scripts=["unused.script"]),
            script="<% let x = 1; %>",
            file_path="t.pmd",
            source_content='{"include": ["unused.script"], "script": "<% let x = 1; %>"}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == ""


class TestEndpointFailOnStatusCodesRule:
    def _make_pmd(self, endpoint_json: str) -> PMDModel:
        source = (
            '{\n'
            '  "inboundEndpoints": [\n'
            f'    {endpoint_json}\n'
            '  ]\n'
            '}'
        )
        import json
        endpoint = json.loads(endpoint_json)
        return PMDModel(
            pageId="t",
            file_path="t.pmd",
            inboundEndpoints=[endpoint],
            source_content=source,
        )

    def test_missing_field_suggests_full_field_insert(self):
        """No failOnStatusCodes at all → replacement is the whole key:value pair."""
        from parser.rules.structure.endpoints.endpoint_fail_on_status_codes import (
            EndpointFailOnStatusCodesRule,
        )

        rule = EndpointFailOnStatusCodesRule()
        context = ProjectContext()
        context.pmds["t"] = self._make_pmd('{"name": "getUser", "url": "/u"}')
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == '"failOnStatusCodes": [{"code": 400}, {"code": 403}]'

    def test_partial_missing_suggests_only_missing_entries(self):
        """One required code missing → replacement is just that entry."""
        from parser.rules.structure.endpoints.endpoint_fail_on_status_codes import (
            EndpointFailOnStatusCodesRule,
        )

        rule = EndpointFailOnStatusCodesRule()
        context = ProjectContext()
        context.pmds["t"] = self._make_pmd(
            '{"name": "getUser", "url": "/u", "failOnStatusCodes": [{"code": 400}]}'
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == '{"code": 403}'

    def test_both_missing_in_empty_array_suggests_both_entries(self):
        """Empty array → both required entries, comma-separated, sorted."""
        from parser.rules.structure.endpoints.endpoint_fail_on_status_codes import (
            EndpointFailOnStatusCodesRule,
        )

        rule = EndpointFailOnStatusCodesRule()
        context = ProjectContext()
        context.pmds["t"] = self._make_pmd(
            '{"name": "getUser", "url": "/u", "failOnStatusCodes": []}'
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == '{"code": 400}, {"code": 403}'

    def test_existing_non_required_code_is_not_in_replacement(self):
        """Existing entries (e.g. 500) are NOT in the replacement — replacement
        contains only the missing required codes. Agent must splice into the
        existing array, not replace its contents."""
        from parser.rules.structure.endpoints.endpoint_fail_on_status_codes import (
            EndpointFailOnStatusCodesRule,
        )

        rule = EndpointFailOnStatusCodesRule()
        context = ProjectContext()
        context.pmds["t"] = self._make_pmd(
            '{"name": "getUser", "url": "/u", "failOnStatusCodes": [{"code": 500}]}'
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        # Agent splices these INTO the existing array; the 500 entry is preserved.
        assert findings[0].suggested_replacement == '{"code": 400}, {"code": 403}'
        assert "500" not in findings[0].suggested_replacement


class TestUnsupportedRuleLeavesNone:
    """Rules without a wired replacement emit None — guards against
    accidentally setting a default everywhere. Uses a `human_review` rule
    so the test stays valid as more `actionable` rules get wired."""

    def test_unwired_rule_finding_has_none(self):
        from parser.rules.structure.validation.footer_pod_required import (
            FooterPodRequiredRule,
        )
        from parser.models import PMDPresentation

        rule = FooterPodRequiredRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            source_content='{"presentation":{"footer":{"type":"footer","children":[{"type":"richText"}]}}}',
            presentation=PMDPresentation(
                footer={"type": "footer", "children": [{"type": "richText"}]}
            ),
        )
        findings = list(rule.analyze(context))
        assert len(findings) >= 1
        assert all(f.suggested_replacement is None for f in findings)

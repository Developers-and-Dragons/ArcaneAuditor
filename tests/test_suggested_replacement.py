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
        # suggested_replacement is the new substring that replaces target_text;
        # applying it to the source via str.replace yields the desired edit.
        assert findings[0].target_text == '"visible": "true"'
        assert findings[0].suggested_replacement == '"visible": true'
        assert findings[0].replacement_context == "substring"

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
        assert findings[0].target_text == '"enabled": "false"'
        assert findings[0].suggested_replacement == '"enabled": false'
        assert findings[0].replacement_context == "substring"


class TestScriptConsoleLogRule:
    def test_console_log_finding_is_substring_swap(self):
        """Single-quoted args are JSON-safe — agent gets a clean substring swap
        targeting the whole call (so it works regardless of surrounding indent)."""
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
        f = findings[0]
        assert f.target_text == "console.info('hello');"
        assert f.suggested_replacement == "// console.info('hello');"
        assert f.replacement_context == "substring"

    def test_console_log_indented_call_uses_call_slice(self):
        """Indent is preserved automatically by the substring swap; we target
        only the call, not the surrounding whitespace."""
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
        f = findings[0]
        assert f.target_text == "console.debug(x);"
        assert f.suggested_replacement == "// console.debug(x);"
        assert f.replacement_context == "substring"

    def test_console_log_with_double_quoted_arg_skips_enrichment(self):
        """Double quotes get JSON-escaped in the source file, so a literal
        substring search would miss — rule falls back to legacy line-replace."""
        from parser.rules.script.core.console_log import ScriptConsoleLogRule

        rule = ScriptConsoleLogRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            script='<%\n  console.info("hello");\n%>',
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        f = findings[0]
        assert f.target_text is None
        assert f.replacement_context is None
        assert f.suggested_replacement is not None  # legacy line-comment fallback


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
    def test_unused_include_emits_array_remove(self):
        """Unused include enriches with array_remove context so the agent can
        splice out the literal entry without touching other includes."""
        from parser.rules.script.unused_code.unused_script_includes import ScriptUnusedIncludesRule
        from parser.models import PMDIncludes

        rule = ScriptUnusedIncludesRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            includes=PMDIncludes(scripts=["util.script", "unused.script"]),
            script="<% util.go(); %>",
            file_path="t.pmd",
            source_content='{"include": ["util.script", "unused.script"], "script": "<% util.go(); %>"}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        f = findings[0]
        assert f.suggested_replacement == ""
        assert f.target_text == '"unused.script"'
        assert f.replacement_context == "array_remove"
        assert f.path == "$.include"


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


class TestOnlyMaximumEffortRule:
    def test_boolean_true_suggests_false(self):
        from parser.rules.structure.endpoints.only_maximum_effort import (
            OnlyMaximumEffortRule,
        )

        rule = OnlyMaximumEffortRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            inboundEndpoints=[{"name": "getUser", "url": "/u", "bestEffort": True}],
            source_content='{"inboundEndpoints":[{"name":"getUser","url":"/u","bestEffort": true}]}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        # New contract: target_text + suggested_replacement are the exact swap pair.
        assert findings[0].target_text == '"bestEffort": true'
        assert findings[0].suggested_replacement == '"bestEffort": false'
        assert findings[0].replacement_context == "substring"

    def test_string_true_suggests_false(self):
        from parser.rules.structure.endpoints.only_maximum_effort import (
            OnlyMaximumEffortRule,
        )

        rule = OnlyMaximumEffortRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            inboundEndpoints=[{"name": "getUser", "url": "/u", "bestEffort": "true"}],
            source_content='{"inboundEndpoints":[{"name":"getUser","url":"/u","bestEffort": "true"}]}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        # String-quoted variant: replacement preserves quotes (StringBooleanRule
        # will catch the redundant quoting on a subsequent pass).
        assert findings[0].target_text == '"bestEffort": "true"'
        assert findings[0].suggested_replacement == '"bestEffort": "false"'
        assert findings[0].replacement_context == "substring"


class TestMultipleStringInterpolatorsRule:
    def test_two_interpolators_combined_into_template_literal(self):
        from parser.rules.structure.validation.multiple_string_interpolators import (
            MultipleStringInterpolatorsRule,
        )

        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            source_content='{\n  "value": "My name is <% name %> and I like <% food %>"\n}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == "<% `My name is {{name}} and I like {{food}}` %>"

    def test_three_interpolators(self):
        from parser.rules.structure.validation.multiple_string_interpolators import (
            MultipleStringInterpolatorsRule,
        )

        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            source_content='{\n  "value": "<% a %>-<% b %>-<% c %>"\n}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == "<% `{{a}}-{{b}}-{{c}}` %>"

    def test_inner_expression_whitespace_stripped(self):
        from parser.rules.structure.validation.multiple_string_interpolators import (
            MultipleStringInterpolatorsRule,
        )

        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            source_content='{\n  "value": "x=<%   x   %> y=<%y%>"\n}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == "<% `x={{x}} y={{y}}` %>"


class TestHardcodedWorkdayAPIRule:
    def test_pmd_endpoint_url_suggests_template_literal(self):
        from parser.rules.structure.validation.hardcoded_workday_api import (
            HardcodedWorkdayAPIRule,
        )

        rule = HardcodedWorkdayAPIRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            inboundEndpoints=[{
                "name": "getWorker",
                "url": "https://api.workday.com/common/v1/workers/me",
            }],
            source_content='{"inboundEndpoints":[{"name":"getWorker","url":"https://api.workday.com/common/v1/workers/me"}]}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == "<% apiGatewayEndpoint + '/common/v1/workers/me' %>"

    def test_amd_dataprovider_suggests_template_literal(self):
        from parser.models import AMDModel
        from parser.rules.structure.validation.hardcoded_workday_api import (
            HardcodedWorkdayAPIRule,
        )

        rule = HardcodedWorkdayAPIRule()
        context = ProjectContext()
        context.amd = AMDModel(
            routes={},
            dataProviders=[{"key": "workday-common", "value": "https://api.workday.com/common/v1/"}],
            file_path="test.amd",
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == "<% apiGatewayEndpoint + '/common/v1/' %>"

    def test_subdomain_workday_url_handled(self):
        """Subdomains other than 'api' (e.g. 'wd5-impl-services1') should also work."""
        from parser.rules.structure.validation.hardcoded_workday_api import (
            HardcodedWorkdayAPIRule,
        )

        rule = HardcodedWorkdayAPIRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            inboundEndpoints=[{
                "name": "getThing",
                "url": "https://wd5-impl-services1.workday.com/ccx/api/v1/foo",
            }],
            source_content='{"inboundEndpoints":[{"name":"getThing","url":"https://wd5-impl-services1.workday.com/ccx/api/v1/foo"}]}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].suggested_replacement == "<% apiGatewayEndpoint + '/ccx/api/v1/foo' %>"


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

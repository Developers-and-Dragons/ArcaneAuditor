"""Step 5 contract: mechanical rules populate `suggested_replacement` on Finding.

Three rules opt in initially — the unambiguous cases. Other mechanical rules
will be wired up incrementally; their Findings stay `None` for now.
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


class TestUnsupportedRuleLeavesNone:
    """Non-mechanical / not-yet-wired rules emit None — guards against
    accidentally setting a default everywhere."""

    def test_non_mechanical_rule_finding_has_none(self):
        # MultipleStringInterpolatorsRule is LOCALIZED, not MECHANICAL.
        from parser.rules.structure.validation.multiple_string_interpolators import (
            MultipleStringInterpolatorsRule,
        )

        rule = MultipleStringInterpolatorsRule()
        context = ProjectContext()
        context.pmds["t"] = PMDModel(
            pageId="t",
            file_path="t.pmd",
            source_content='{\n  "x": "<% a %> and <% b %>"\n}',
        )
        findings = list(rule.analyze(context))
        assert len(findings) >= 1
        assert all(f.suggested_replacement is None for f in findings)

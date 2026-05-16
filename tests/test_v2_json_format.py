"""v2 JSON formatter (breaking schema change).

Top-level: schema_version, summary, findings, [context]. Findings have nested `location` and carry
category, fix_strategy, snippet, suggested_replacement, finding_id.
"""
import json

from output.formatter import OutputFormatter, OutputFormat
from parser.models import PMDModel, ProjectContext, SMDModel
from parser.rules.script.core.var_usage import ScriptVarUsageRule
from parser.rules.structure.validation.hardcoded_application_id import (
    HardcodedApplicationIdRule,
)


def _format(findings, total_files=1, total_rules=1, context=None):
    formatter = OutputFormatter(OutputFormat.JSON)
    return json.loads(
        formatter.format_results(findings, total_files, total_rules, context)
    )


class TestTopLevelShape:
    def test_schema_version_present(self):
        result = _format([])
        assert result["schema_version"] == "2.0"

    def test_summary_structure(self):
        result = _format([], total_files=3, total_rules=42)
        assert result["summary"] == {
            "total_files": 3,
            "total_rules": 42,
            "total_findings": 0,
            "findings_by_severity": {"ACTION": 0, "ADVICE": 0},
        }

    def test_findings_is_list(self):
        result = _format([])
        assert result["findings"] == []

    def test_no_context_when_none(self):
        assert "context" not in _format([])


class TestFindingShape:
    def _one_finding(self):
        rule = ScriptVarUsageRule()
        ctx = ProjectContext()
        ctx.pmds["p"] = PMDModel(
            pageId="p", onLoad="<% var x = 1; %>", file_path="p.pmd",
            source_content="line1\nline2\n<% var x = 1; %>\nline4\nline5",
        )
        return list(rule.analyze(ctx)), ctx

    def test_finding_top_level_keys(self):
        findings, ctx = self._one_finding()
        result = _format(findings, context=ctx)
        f = result["findings"][0]
        assert set(f.keys()) == {
            "rule_id",
            "severity",
            "category",
            "fix_strategy",
            "fix_strategy_overridden",
            "message",
            "location",
            "snippet",
            "suggested_replacement",
            "target_text",
            "replacement_context",
            "finding_id",
        }

    def test_location_nested(self):
        findings, ctx = self._one_finding()
        result = _format(findings, context=ctx)
        loc = result["findings"][0]["location"]
        assert loc["file_path"] == "p.pmd"
        assert isinstance(loc["line"], int) and loc["line"] >= 1
        assert loc["column"] is None
        assert loc["end_line"] is None
        assert loc["end_column"] is None
        assert loc["path"] == "$.onLoad"

    def test_category_and_fix_strategy_are_strings(self):
        findings, ctx = self._one_finding()
        result = _format(findings, context=ctx)
        f = result["findings"][0]
        # str-Enum members serialize as their string values.
        assert f["category"] == "script"
        assert f["fix_strategy"] == "actionable"

    def test_finding_id_prefix(self):
        findings, ctx = self._one_finding()
        result = _format(findings, context=ctx)
        assert result["findings"][0]["finding_id"].startswith("sha1:")

    def test_suggested_replacement_passed_through(self):
        findings, ctx = self._one_finding()
        result = _format(findings, context=ctx)
        assert result["findings"][0]["suggested_replacement"] == "let x"

    def test_snippet_populated_when_context_has_source(self):
        findings, ctx = self._one_finding()
        result = _format(findings, context=ctx)
        snippet = result["findings"][0]["snippet"]
        assert snippet is not None
        # The violating line should appear in the snippet.
        assert "var x = 1" in snippet

    def test_snippet_none_when_no_context(self):
        findings, _ = self._one_finding()
        result = _format(findings, context=None)
        assert result["findings"][0]["snippet"] is None


class TestSnippetLookupAcrossModelTypes:
    """Snippet population must work for every model type the parser produces,
    not just PMD/POD. ScriptModel stores source on ``.source`` (not
    ``.source_content``) — easy to overlook."""

    def test_snippet_for_script_file(self):
        from parser.models import ScriptModel
        from parser.rules.script.core.var_usage import ScriptVarUsageRule

        ctx = ProjectContext()
        ctx.scripts["s"] = ScriptModel(
            file_path="s.script",
            source="line1\nvar x = 1;\nline3",
        )
        findings = list(ScriptVarUsageRule().analyze(ctx))
        assert len(findings) == 1
        result = _format(findings, context=ctx)
        snippet = result["findings"][0]["snippet"]
        assert snippet is not None
        assert "var x = 1" in snippet

    def test_snippet_for_amd_file(self):
        from parser.models import AMDModel
        from parser.rules.structure.validation.hardcoded_application_id import (
            HardcodedApplicationIdRule,
        )

        ctx = ProjectContext()
        ctx.smd = SMDModel(
            id="app", applicationId="app_xyz", siteId="s", file_path="x.smd"
        )
        ctx.amd = AMDModel(
            routes={},
            dataProviders=[{"key": "k", "value": "https://api/app_xyz/foo"}],
            file_path="x.amd",
            source_content='{\n  "dataProviders": [{"value": "https://api/app_xyz/foo"}]\n}',
        )
        findings = list(HardcodedApplicationIdRule().analyze(ctx))
        amd_findings = [f for f in findings if f.file_path == "x.amd"]
        assert amd_findings, "expected at least one AMD finding for setup sanity"
        result = _format(amd_findings, context=ctx)
        # AMD source_content is in the lookup, so snippet should be populated.
        assert result["findings"][0]["snippet"] is not None


class TestSummaryCountsByActualSeverity:
    def test_action_advice_counts(self):
        ctx = ProjectContext()
        ctx.smd = SMDModel(
            id="app", applicationId="app_xyz", siteId="s", file_path="x.smd"
        )
        ctx.pmds["t"] = PMDModel(
            pageId="t", file_path="t.pmd",
            source_content='{\n  "applicationId": "app_xyz"\n}',
        )
        findings = list(HardcodedApplicationIdRule().analyze(ctx))
        result = _format(findings, context=ctx)
        # HardcodedApplicationIdRule is ADVICE severity.
        assert result["summary"]["findings_by_severity"]["ADVICE"] == len(findings)
        assert result["summary"]["findings_by_severity"]["ACTION"] == 0
        assert result["summary"]["total_findings"] == len(findings)

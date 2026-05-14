"""Finding carries enrichment fields populated from its Rule.

Covers:
- New optional fields: snippet, suggested_replacement, path.
- Derived fields category, fix_strategy populated from self.rule.
- finding_id is deterministic and excludes line so re-runs after a fix still
  produce a joinable id.
"""
import hashlib
import pytest

from parser.rules.base import Finding, Rule, FixStrategy, Category


class _FakeRule(Rule):
    """Minimal concrete Rule for constructing Findings under test."""
    DESCRIPTION = "fake rule for finding tests"
    SEVERITY = "ACTION"
    CATEGORY = Category.SCRIPT
    FIX_STRATEGY = FixStrategy.MECHANICAL

    def analyze(self, context):
        yield from []


def _expected_id(rule_id: str, file_path: str, path: str, message: str) -> str:
    raw = f"{rule_id}|{file_path}|{path or ''}|{message}"
    return "sha1:" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


class TestEnrichmentFields:
    def test_defaults_for_new_fields(self):
        f = Finding(rule=_FakeRule(), message="m", line=10, file_path="a.pmd")
        assert f.snippet is None
        assert f.suggested_replacement is None
        assert f.path is None

    def test_category_and_fix_strategy_populated_from_rule(self):
        f = Finding(rule=_FakeRule(), message="m", line=10, file_path="a.pmd")
        assert f.category == Category.SCRIPT
        assert f.fix_strategy == FixStrategy.MECHANICAL

    def test_explicit_enrichment_values_round_trip(self):
        f = Finding(
            rule=_FakeRule(),
            message="m",
            line=10,
            file_path="a.pmd",
            snippet="line9\nline10\nline11",
            suggested_replacement="let",
            path="$.body.children[0].onLoad",
        )
        assert f.snippet == "line9\nline10\nline11"
        assert f.suggested_replacement == "let"
        assert f.path == "$.body.children[0].onLoad"


class TestFindingId:
    def test_finding_id_matches_expected_hash(self):
        f = Finding(
            rule=_FakeRule(),
            message="hello",
            line=10,
            file_path="a.pmd",
            path="$.x",
        )
        assert f.finding_id == _expected_id("_FakeRule", "a.pmd", "$.x", "hello")

    def test_finding_id_excludes_line(self):
        a = Finding(rule=_FakeRule(), message="m", line=10, file_path="a.pmd", path="$.x")
        b = Finding(rule=_FakeRule(), message="m", line=999, file_path="a.pmd", path="$.x")
        assert a.finding_id == b.finding_id

    def test_finding_id_changes_with_file_path(self):
        a = Finding(rule=_FakeRule(), message="m", line=1, file_path="a.pmd", path="$.x")
        b = Finding(rule=_FakeRule(), message="m", line=1, file_path="b.pmd", path="$.x")
        assert a.finding_id != b.finding_id

    def test_finding_id_changes_with_path(self):
        a = Finding(rule=_FakeRule(), message="m", line=1, file_path="a.pmd", path="$.x")
        b = Finding(rule=_FakeRule(), message="m", line=1, file_path="a.pmd", path="$.y")
        assert a.finding_id != b.finding_id

    def test_finding_id_changes_with_message(self):
        a = Finding(rule=_FakeRule(), message="one", line=1, file_path="a.pmd")
        b = Finding(rule=_FakeRule(), message="two", line=1, file_path="a.pmd")
        assert a.finding_id != b.finding_id

    def test_finding_id_treats_missing_path_as_empty_string(self):
        f = Finding(rule=_FakeRule(), message="m", line=1, file_path="a.pmd")
        assert f.finding_id == _expected_id("_FakeRule", "a.pmd", "", "m")

    def test_finding_id_is_prefixed(self):
        f = Finding(rule=_FakeRule(), message="m", line=1, file_path="a.pmd")
        assert f.finding_id.startswith("sha1:")

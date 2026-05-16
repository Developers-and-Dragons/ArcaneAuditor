"""Filter flags on `review-app`: --rules, --exclude-rules, --severity, --fix-strategy, --files.

Rule filters narrow the rules list before running (faster). Finding filters
(--severity / --fix-strategy) apply after running. --files filters
source_files_map before parsing.
"""
import json
import os
import tempfile

from typer.testing import CliRunner

from main import app

runner = CliRunner()


def _tmp_pmd_with_var(suffix: str = ".pmd") -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    # Valid minimal PMD that triggers ScriptVarUsageRule (script/mechanical, ADVICE).
    f.write(
        '{"id": "p", "script": "<% var x = 1; %>", "presentation": {"body": {}}}'
    )
    f.close()
    return f.name


def _agent_output(args):
    return runner.invoke(app, ["review-app", *args, "--agent"])


class TestRulesFilter:
    def test_rules_flag_in_help(self):
        result = runner.invoke(app, ["review-app", "--help"])
        for flag in ("--rules", "--exclude-rules", "--severity", "--fix-strategy", "--files"):
            assert flag in result.output, f"missing {flag}"

    def test_rules_narrows_to_named_rule(self):
        path = _tmp_pmd_with_var()
        try:
            result = _agent_output([path, "--rules", "ScriptVarUsageRule"])
            assert result.exit_code in (0, 1), result.output
            data = json.loads(result.output)
            rule_ids = {f["rule_id"] for f in data["findings"]}
            assert rule_ids <= {"ScriptVarUsageRule"}
            assert "ScriptVarUsageRule" in rule_ids
        finally:
            os.unlink(path)

    def test_unknown_rule_in_rules_exits_2(self):
        path = _tmp_pmd_with_var()
        try:
            result = _agent_output([path, "--rules", "NoSuchRule"])
            assert result.exit_code == 2, result.output
        finally:
            os.unlink(path)

    def test_exclude_rules_drops_named_rule(self):
        path = _tmp_pmd_with_var()
        try:
            result = _agent_output([path, "--exclude-rules", "ScriptVarUsageRule"])
            assert result.exit_code in (0, 1), result.output
            data = json.loads(result.output)
            rule_ids = {f["rule_id"] for f in data["findings"]}
            assert "ScriptVarUsageRule" not in rule_ids
        finally:
            os.unlink(path)

    def test_unknown_rule_in_exclude_rules_exits_2(self):
        path = _tmp_pmd_with_var()
        try:
            result = _agent_output([path, "--exclude-rules", "NoSuchRule"])
            assert result.exit_code == 2
        finally:
            os.unlink(path)


class TestSeverityFilter:
    def test_severity_advice_keeps_only_advice(self):
        path = _tmp_pmd_with_var()
        try:
            result = _agent_output([path, "--severity", "ADVICE"])
            data = json.loads(result.output)
            assert all(f["severity"] == "ADVICE" for f in data["findings"])
        finally:
            os.unlink(path)

    def test_severity_action_drops_all_advice(self):
        path = _tmp_pmd_with_var()
        try:
            result = _agent_output([path, "--severity", "ACTION"])
            data = json.loads(result.output)
            assert all(f["severity"] == "ACTION" for f in data["findings"])
        finally:
            os.unlink(path)

    def test_invalid_severity_exits_2(self):
        path = _tmp_pmd_with_var()
        try:
            result = _agent_output([path, "--severity", "BOGUS"])
            assert result.exit_code == 2
        finally:
            os.unlink(path)


class TestFixStrategyFilter:
    def test_actionable_keeps_only_actionable(self):
        path = _tmp_pmd_with_var()
        try:
            result = _agent_output([path, "--fix-strategy", "actionable"])
            data = json.loads(result.output)
            assert data["findings"], "expected at least one actionable finding"
            assert all(f["fix_strategy"] == "actionable" for f in data["findings"])
        finally:
            os.unlink(path)

    def test_multiple_strategies_csv(self):
        path = _tmp_pmd_with_var()
        try:
            result = _agent_output([path, "--fix-strategy", "actionable,human_review"])
            data = json.loads(result.output)
            assert all(
                f["fix_strategy"] in {"actionable", "human_review"} for f in data["findings"]
            )
        finally:
            os.unlink(path)

    def test_invalid_fix_strategy_exits_2(self):
        path = _tmp_pmd_with_var()
        try:
            result = _agent_output([path, "--fix-strategy", "magic"])
            assert result.exit_code == 2
        finally:
            os.unlink(path)


class TestFilesFilter:
    def test_files_glob_drops_non_matching(self):
        keep_path = _tmp_pmd_with_var(suffix="_keep.pmd")
        drop_path = _tmp_pmd_with_var(suffix="_drop.pmd")
        try:
            # Run with --files matching it: finding should be on keep_path only.
            result = _agent_output([keep_path, "--files", "*_keep.pmd"])
            assert result.exit_code in (0, 1), result.output
            data = json.loads(result.output)
            for finding in data["findings"]:
                assert "_keep.pmd" in finding["location"]["file_path"]

            # Run with --files that excludes the only file → no files to analyze → exit 2.
            result = _agent_output([keep_path, "--files", "*_nomatch*.pmd"])
            assert result.exit_code == 2, result.output
        finally:
            os.unlink(keep_path)
            os.unlink(drop_path)

    def test_files_csv_keeps_union(self):
        """Comma-separated patterns: a file is kept if ANY pattern matches."""
        d = tempfile.mkdtemp()
        try:
            for name, pid in (("alpha.pmd", "a"), ("beta.pmd", "b"), ("gamma.pmd", "g")):
                with open(os.path.join(d, name), "w") as fh:
                    fh.write(
                        '{"id": "' + pid + '", "script": "<% var x = 1; %>", "presentation": {"body": {}}}'
                    )
            result = runner.invoke(
                app,
                ["review-app", d, "--files", "alpha.pmd,beta.pmd", "--agent"],
            )
            assert result.exit_code in (0, 1), result.output
            data = json.loads(result.output)
            file_paths = {f["location"]["file_path"] for f in data["findings"]}
            assert any("alpha.pmd" in p for p in file_paths), f"got {file_paths}"
            assert any("beta.pmd" in p for p in file_paths), f"got {file_paths}"
            assert not any("gamma.pmd" in p for p in file_paths), f"got {file_paths}"
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)

    def test_distinct_files_with_duplicate_pmd_id_all_analyzed(self):
        """Regression: PMDs sharing pageId across different files must not collide."""
        d = tempfile.mkdtemp()
        try:
            for name in ("alpha.pmd", "beta.pmd", "gamma.pmd"):
                with open(os.path.join(d, name), "w") as fh:
                    fh.write(
                        '{"id": "samePage", "script": "<% var x = 1; %>", "presentation": {"body": {}}}'
                    )
            result = _agent_output([d])
            assert result.exit_code in (0, 1), result.output
            data = json.loads(result.output)
            file_paths = {f["location"]["file_path"] for f in data["findings"]}
            assert any("alpha.pmd" in p for p in file_paths), f"got {file_paths}"
            assert any("beta.pmd" in p for p in file_paths), f"got {file_paths}"
            assert any("gamma.pmd" in p for p in file_paths), f"got {file_paths}"
        finally:
            import shutil
            shutil.rmtree(d, ignore_errors=True)

    def test_files_csv_whitespace_tolerated(self):
        """Whitespace around CSV entries is stripped, mirroring --rules."""
        keep_path = _tmp_pmd_with_var(suffix="_keep.pmd")
        try:
            result = _agent_output([keep_path, "--files", " *_keep.pmd , *_nope.pmd "])
            assert result.exit_code in (0, 1), result.output
            data = json.loads(result.output)
            for finding in data["findings"]:
                assert "_keep.pmd" in finding["location"]["file_path"]
        finally:
            os.unlink(keep_path)

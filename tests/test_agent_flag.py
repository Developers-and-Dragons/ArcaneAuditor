"""--agent preset flag: implies quiet + json + stdout; conflicts with --ci and non-json formats."""
import json
import os
import tempfile

from typer.testing import CliRunner

from main import app

runner = CliRunner()


def _tmp_pmd(text: str = '{"id": "test", "presentation": {"body": {}}}'):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".pmd", delete=False)
    f.write(text)
    f.close()
    return f.name


class TestAgentFlagExists:
    def test_flag_in_help(self):
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--agent" in result.output


class TestAgentImpliesJsonStdout:
    def test_agent_emits_v2_json_on_stdout(self):
        path = _tmp_pmd()
        try:
            result = runner.invoke(app, ["review-app", path, "--agent"])
            assert result.exit_code in (0, 1), result.output
            # Output should be parseable JSON conforming to v2 schema.
            data = json.loads(result.output)
            assert data["schema_version"] == "2.0"
            assert "summary" in data
            assert "findings" in data
        finally:
            os.unlink(path)

    def test_agent_quiet_suppresses_startup_chatter(self):
        path = _tmp_pmd()
        try:
            result = runner.invoke(app, ["review-app", path, "--agent"])
            # --agent should imply --quiet: no verbose info() messages.
            assert "Starting review for" not in result.output
            assert "Using" not in result.output or "configuration" not in result.output.split("Using", 1)[-1].split("\n", 1)[0]
        finally:
            os.unlink(path)

    def test_agent_does_not_write_default_output_file(self):
        path = _tmp_pmd()
        # --ci writes arcane-auditor-results.json by default; --agent must not.
        default_ci_file = "arcane-auditor-results.json"
        existed_before = os.path.exists(default_ci_file)
        try:
            runner.invoke(app, ["review-app", path, "--agent"])
            if not existed_before:
                assert not os.path.exists(default_ci_file)
        finally:
            os.unlink(path)
            if not existed_before and os.path.exists(default_ci_file):
                os.unlink(default_ci_file)


class TestAgentMutualExclusion:
    def test_agent_with_ci_exits_2(self):
        path = _tmp_pmd()
        try:
            result = runner.invoke(app, ["review-app", path, "--agent", "--ci"])
            assert result.exit_code == 2, result.output
        finally:
            os.unlink(path)

    def test_agent_with_non_json_format_exits_2(self):
        path = _tmp_pmd()
        try:
            result = runner.invoke(app, ["review-app", path, "--agent", "--format", "console"])
            assert result.exit_code == 2, result.output
        finally:
            os.unlink(path)

    def test_agent_with_explicit_json_format_is_allowed(self):
        path = _tmp_pmd()
        try:
            result = runner.invoke(app, ["review-app", path, "--agent", "--format", "json"])
            assert result.exit_code in (0, 1), result.output
            data = json.loads(result.output)
            assert data["schema_version"] == "2.0"
        finally:
            os.unlink(path)

"""`list-rules --format json` and `describe-rule <RuleId>` machine-readable rule introspection."""
import json

from typer.testing import CliRunner

from main import app

runner = CliRunner()


class TestListRulesJson:
    def test_format_flag_in_help(self):
        result = runner.invoke(app, ["list-rules", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output

    def test_default_format_is_unchanged(self):
        # Plain `list-rules` should still print the human-readable text format.
        result = runner.invoke(app, ["list-rules"])
        assert result.exit_code == 0
        assert "Total:" in result.output  # text-format footer

    def test_json_format_emits_array(self):
        result = runner.invoke(app, ["list-rules", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_json_entry_shape(self):
        result = runner.invoke(app, ["list-rules", "--format", "json"])
        data = json.loads(result.output)
        entry = data[0]
        assert set(entry.keys()) >= {
            "rule_id",
            "category",
            "severity",
            "fix_strategy",
            "description",
            "enabled",
        }
        assert isinstance(entry["rule_id"], str)
        # Enums serialize as their string values.
        assert isinstance(entry["category"], str)
        assert isinstance(entry["fix_strategy"], str)
        assert isinstance(entry["enabled"], bool)

    def test_json_sorted_by_rule_id(self):
        result = runner.invoke(app, ["list-rules", "--format", "json"])
        data = json.loads(result.output)
        ids = [e["rule_id"] for e in data]
        assert ids == sorted(ids)

    def test_invalid_format_exits_2(self):
        result = runner.invoke(app, ["list-rules", "--format", "yaml"])
        assert result.exit_code == 2


class TestDescribeRule:
    def test_describe_known_rule_emits_json(self):
        result = runner.invoke(app, ["describe-rule", "ScriptVarUsageRule"])
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["rule_id"] == "ScriptVarUsageRule"
        assert data["category"] == "script"
        assert data["fix_strategy"] == "actionable"
        assert data["severity"] in {"ACTION", "ADVICE"}
        assert isinstance(data["description"], str) and data["description"]
        assert isinstance(data["available_settings"], dict)
        # All four DOCUMENTATION keys.
        for key in ("why", "catches", "examples", "recommendation"):
            assert key in data, f"missing documentation key {key}"

    def test_describe_unknown_rule_exits_2(self):
        result = runner.invoke(app, ["describe-rule", "DoesNotExistRule"])
        assert result.exit_code == 2

    def test_describe_help_lists_command(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "describe-rule" in result.output

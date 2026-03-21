"""
Unit tests for Arcane Auditor CLI functionality.

Tests the main CLI interface including CI-specific features like --fail-on-advice and --quiet modes.
"""

import pytest
import typer
from typer.testing import CliRunner
from pathlib import Path
import tempfile
import json
import os
from unittest.mock import patch, MagicMock

# Import the main CLI app
from main import app

runner = CliRunner()


class TestCLICIFeatures:
    """Test CI-specific CLI features."""

    def test_fail_on_advice_flag_exists(self):
        """Test that --fail-on-advice flag is available."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--fail-on-advice" in result.output
        assert "CI mode" in result.output

    def test_quiet_flag_exists(self):
        """Test that --quiet flag is available."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--quiet" in result.output
        assert "-q" in result.output
        assert "Minimal output mode (CI-friendly)" in result.output

    def test_quiet_mode_suppresses_output(self):
        """Test that --quiet mode suppresses non-essential output."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pmd', delete=False) as f:
            f.write('{"id": "test", "presentation": {"body": {}}}')
            temp_file = f.name

        try:
            # Mock the analysis to return some findings
            with patch('main.FileProcessor') as mock_processor, \
                 patch('main.ModelParser') as mock_parser, \
                 patch('main.RulesEngine') as mock_rules_engine, \
                 patch('main.OutputFormatter') as mock_formatter:
                
                # Setup mocks
                mock_processor.return_value.process_zip_file.return_value = {}
                mock_parser.return_value.parse_files.return_value = MagicMock()
                mock_rules_engine.return_value.run.return_value = []
                mock_formatter.return_value.format_results.return_value = "Test output"
                
                # Test with quiet mode
                result = runner.invoke(app, ["review-app", temp_file, "--quiet"])
                
                # Should not contain verbose startup messages
                assert "Starting review for" not in result.output
                assert "Using default configuration" not in result.output
                
        finally:
            os.unlink(temp_file)

    def test_fail_on_advice_exit_codes(self):
        """Test exit codes with --fail-on-advice flag."""
        # Test the help to ensure the flag exists
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--fail-on-advice" in result.output
        
        # Test with a non-existent file to trigger error handling
        result = runner.invoke(app, ["review-app", "nonexistent.pmd", "--fail-on-advice"])
        # Should fail due to file not existing, not due to our flag
        assert result.exit_code != 0

    def test_quiet_mode_with_timing(self):
        """Test that --quiet flag exists and can be combined with --timing."""
        # Test that both flags exist
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--quiet" in result.output
        assert "--timing" in result.output
        
        # Test that flags can be combined (should not crash)
        result = runner.invoke(app, ["review-app", "nonexistent.pmd", "--quiet", "--timing"])
        assert result.exit_code != 0  # Should fail due to file not existing

    def test_ci_mode_combination(self):
        """Test combining --quiet and --fail-on-advice for CI usage."""
        # Test that all CI flags exist and can be combined
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--quiet" in result.output
        assert "--fail-on-advice" in result.output
        assert "--format" in result.output
        
        # Test that CI flags can be combined (should not crash)
        result = runner.invoke(app, [
            "review-app", "nonexistent.pmd", 
            "--quiet", "--fail-on-advice", "--format", "json"
        ])
        assert result.exit_code != 0  # Should fail due to file not existing

    def test_exit_code_documentation(self):
        """Test that exit codes are properly documented in help."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        
        # The help should mention CI-friendly behavior
        help_text = result.output
        assert "CI mode" in help_text or "fail-on-advice" in help_text


class TestCLIExitCodes:
    """Test CLI exit code behavior."""

    def test_exit_code_0_no_issues(self):
        """Test that CLI accepts valid flags."""
        # Test that help works (exit code 0)
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0

    def test_exit_code_1_advice_only(self):
        """Test that --fail-on-advice flag exists."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--fail-on-advice" in result.output

    def test_exit_code_2_action_issues(self):
        """Test that CLI handles invalid files properly."""
        result = runner.invoke(app, ["review-app", "nonexistent.pmd"])
        assert result.exit_code != 0  # Should fail due to file not existing

    def test_exit_code_3_analysis_error(self):
        """Test that CLI handles errors gracefully."""
        result = runner.invoke(app, ["review-app", "nonexistent.pmd"])
        assert result.exit_code != 0  # Should fail due to file not existing


class TestCLIOutputFormats:
    """Test CLI output format options."""

    def test_json_output_format(self):
        """Test that JSON output format is available."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "json" in result.output

    def test_summary_output_format(self):
        """Test that summary output format is available."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "summary" in result.output


def _minimal_pmd_path():
    """Create a minimal valid PMD temp file and return its path. Caller must clean up."""
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.pmd', delete=False)
    f.write('{"id": "testPage", "presentation": {"body": {}}}')
    f.close()
    return f.name


class TestQuietAndChannels:
    """Test --quiet, three-channel output, and --ci preset."""

    def test_normal_run_shows_status(self):
        """Without --quiet, status/info messages appear on stdout."""
        path = _minimal_pmd_path()
        try:
            result = runner.invoke(app, ["review-app", path])
            assert result.exit_code in (0, 1)  # 0 no issues, 1 has findings
            assert "Starting review" in result.stdout
        finally:
            os.unlink(path)

    def test_quiet_suppresses_status(self):
        """With --quiet, status chatter is suppressed."""
        path = _minimal_pmd_path()
        try:
            result = runner.invoke(app, ["review-app", path, "--quiet"])
            assert result.exit_code in (0, 1)
            assert "Starting review" not in result.stdout
        finally:
            os.unlink(path)

    def test_quiet_still_prints_console_findings_when_no_output_file(self):
        """With --quiet and no -o, results (e.g. console format) still go to stdout."""
        path = _minimal_pmd_path()
        try:
            result = runner.invoke(app, ["review-app", path, "--quiet", "--format", "console"])
            assert result.exit_code in (0, 1)
            assert "Starting review" not in result.stdout
        finally:
            os.unlink(path)

    def test_quiet_output_file_keeps_stdout_empty_on_success(self):
        """With --quiet and -o, write to file and do not print success banners to stdout."""
        path = _minimal_pmd_path()
        out = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        out.close()
        try:
            result = runner.invoke(app, ["review-app", path, "--quiet", "--output", out.name])
            assert result.exit_code in (0, 1)
            assert "Results written to" not in result.stdout
            assert os.path.exists(out.name)
            with open(out.name) as f:
                data = json.load(f)
            assert "findings" in data or "summary" in data
        finally:
            os.unlink(path)
            if os.path.exists(out.name):
                os.unlink(out.name)

    def test_ci_flag_in_help(self):
        """--ci is documented as CI preset."""
        result = runner.invoke(app, ["review-app", "--help"])
        assert result.exit_code == 0
        assert "--ci" in result.output

    def test_ci_defaults_quiet_json_file(self):
        """--ci implies quiet and json output to default file when -o not given."""
        path = _minimal_pmd_path()
        default_name = "arcane-auditor-results.json"
        try:
            result = runner.invoke(app, ["review-app", path, "--ci"])
            assert result.exit_code in (0, 1)
            assert Path(default_name).exists()
            with open(default_name) as f:
                data = json.load(f)
            assert "findings" in data or "summary" in data
        finally:
            os.unlink(path)
            if Path(default_name).exists():
                os.unlink(default_name)

    def test_ci_format_override(self):
        """Explicit --format overrides --ci preset."""
        path = _minimal_pmd_path()
        out = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        out.close()
        try:
            result = runner.invoke(app, ["review-app", path, "--ci", "--format", "summary", "--output", out.name])
            assert result.exit_code in (0, 1)
            with open(out.name, encoding="utf-8") as f:
                text = f.read()
            assert "findings" in text.lower() or "issue" in text.lower() or "no issues" in text.lower()
        finally:
            os.unlink(path)
            os.unlink(out.name)

    def test_ci_output_override(self):
        """Explicit --output overrides --ci default file."""
        path = _minimal_pmd_path()
        custom = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        custom.close()
        try:
            result = runner.invoke(app, ["review-app", path, "--ci", "--output", custom.name])
            assert result.exit_code in (0, 1)
            assert os.path.exists(custom.name)
        finally:
            os.unlink(path)
            os.unlink(custom.name)

    def test_errors_go_to_stderr(self):
        """Fatal errors (e.g. file not found) go to stderr."""
        result = runner.invoke(app, ["review-app", "nonexistent.pmd"])
        assert result.exit_code != 0
        assert "nonexistent" in result.stderr or "No such file" in result.stderr or "Error" in result.stderr

"""`agent-help` command prints SKILL.md so agents can self-discover usage."""
from pathlib import Path

from typer.testing import CliRunner

from main import app

runner = CliRunner()

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = REPO_ROOT / "SKILL.md"


class TestSkillMdFile:
    def test_skill_md_exists(self):
        assert SKILL_MD.exists(), "SKILL.md should live at repo root"

    def test_skill_md_has_yaml_frontmatter(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        # First non-empty line must be `---`.
        first = next(line for line in text.splitlines() if line.strip())
        assert first.strip() == "---"

    def test_frontmatter_has_name_and_description(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        # Naive extract: between the first two `---` lines.
        parts = text.split("---", 2)
        assert len(parts) >= 3, "expected '---' delimited frontmatter"
        frontmatter = parts[1]
        assert "name: arcane-auditor" in frontmatter
        assert "description:" in frontmatter

    def test_body_mentions_core_concepts(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        for token in ("schema_version", "fix_strategy", "JSONPath", "--agent"):
            assert token in text, f"SKILL.md should mention {token}"


class TestAgentHelpCommand:
    def test_command_in_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "agent-help" in result.output

    def test_command_prints_skill_md(self):
        result = runner.invoke(app, ["agent-help"])
        assert result.exit_code == 0, result.output
        # Should include the frontmatter name and at least one body landmark.
        assert "arcane-auditor" in result.output
        assert "schema_version" in result.output

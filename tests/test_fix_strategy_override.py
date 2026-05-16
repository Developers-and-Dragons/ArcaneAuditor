"""Per-rule `fix_strategy_override` mirrors the existing `severity_override` pattern.

A user (or team config) can re-classify a rule's fix_strategy — e.g. changing a
rule that ships as `actionable` to `human_review` for their codebase. This gives
the same agency users already have over severity.
"""
import json

from parser.config import ArcaneAuditorConfig, RuleConfig
from parser.models import PMDModel, ProjectContext
from parser.rules.base import FixStrategy
from parser.rules.script.core.var_usage import ScriptVarUsageRule
from parser.rules_engine import RulesEngine


class TestRuleConfigField:
    def test_default_is_none(self):
        assert RuleConfig().fix_strategy_override is None

    def test_accepts_enum_value(self):
        c = RuleConfig(fix_strategy_override="human_review")
        assert c.fix_strategy_override == FixStrategy.HUMAN_REVIEW


class TestConfigResolver:
    def test_returns_default_when_no_override(self):
        cfg = ArcaneAuditorConfig()
        result = cfg.get_rule_fix_strategy("ScriptVarUsageRule", FixStrategy.ACTIONABLE)
        assert result == FixStrategy.ACTIONABLE

    def test_returns_override_when_set(self):
        cfg = ArcaneAuditorConfig()
        cfg.rules.ScriptVarUsageRule.fix_strategy_override = FixStrategy.HUMAN_REVIEW
        result = cfg.get_rule_fix_strategy("ScriptVarUsageRule", FixStrategy.ACTIONABLE)
        assert result == FixStrategy.HUMAN_REVIEW


class TestRulesEngineAppliesOverride:
    def test_finding_picks_up_override(self):
        cfg = ArcaneAuditorConfig()
        cfg.rules.ScriptVarUsageRule.fix_strategy_override = FixStrategy.HUMAN_REVIEW

        engine = RulesEngine(cfg)
        # Replace discovered rules with just the one we care about.
        engine.rules = [r for r in engine.rules if r.__class__.__name__ == "ScriptVarUsageRule"]
        assert len(engine.rules) == 1
        assert engine.rules[0].FIX_STRATEGY == FixStrategy.HUMAN_REVIEW

        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p", onLoad="<% var x = 1; %>", file_path="p.pmd"
        )
        findings = engine.run(context)
        assert len(findings) == 1
        # str-Enum comparison.
        assert findings[0].fix_strategy == FixStrategy.HUMAN_REVIEW


class TestJsonRoundtrip:
    def test_load_from_json_with_override(self, tmp_path):
        cfg_path = tmp_path / "cfg.json"
        cfg_path.write_text(
            json.dumps({
                "rules": {
                    "ScriptVarUsageRule": {
                        "enabled": True,
                        "severity_override": None,
                        "fix_strategy_override": "human_review",
                        "custom_settings": {},
                    }
                }
            }),
            encoding="utf-8",
        )
        cfg = ArcaneAuditorConfig.from_file(str(cfg_path))
        assert cfg.rules.ScriptVarUsageRule.fix_strategy_override == FixStrategy.HUMAN_REVIEW

    def test_unknown_strategy_value_raises(self, tmp_path):
        cfg_path = tmp_path / "cfg.json"
        cfg_path.write_text(
            json.dumps({
                "rules": {
                    "ScriptVarUsageRule": {
                        "enabled": True,
                        "severity_override": None,
                        "fix_strategy_override": "not_a_real_strategy",
                        "custom_settings": {},
                    }
                }
            }),
            encoding="utf-8",
        )
        import pytest
        with pytest.raises(Exception):
            ArcaneAuditorConfig.from_file(str(cfg_path))

"""Backend support for the fix_strategy_override config UI.

The config-editor UI (web/frontend/js/config/) reads rule rows from the
normalized config document and renders a dropdown for fix_strategy alongside
the existing severity dropdown. These tests cover the backend pieces the UI
depends on: normalization, default resolution, and round-tripping.
"""
import json

from utils.config_normalizer import normalize_config_rules
from web.routes.configs import (
    get_rule_default_fix_strategies,
    get_rule_default_severities,
)


class TestNormalizerPreservesFixStrategy:
    def test_existing_rule_with_override_kept(self):
        runtime = ["ScriptVarUsageRule"]
        production = {
            "ScriptVarUsageRule": {
                "enabled": True,
                "severity_override": "ADVICE",
                "fix_strategy_override": "mechanical",
                "custom_settings": {},
            }
        }
        user_config = {
            "ScriptVarUsageRule": {
                "enabled": True,
                "severity_override": "ACTION",
                "fix_strategy_override": "design_decision",
                "custom_settings": {},
            }
        }
        out = normalize_config_rules(user_config, True, runtime, production)
        assert out["ScriptVarUsageRule"]["fix_strategy_override"] == "design_decision"
        assert out["ScriptVarUsageRule"]["severity_override"] == "ACTION"

    def test_existing_rule_without_override_falls_back_to_production(self):
        runtime = ["ScriptVarUsageRule"]
        production = {
            "ScriptVarUsageRule": {
                "enabled": True,
                "severity_override": "ADVICE",
                "fix_strategy_override": "mechanical",
                "custom_settings": {},
            }
        }
        user_config = {
            # User omitted fix_strategy_override entirely.
            "ScriptVarUsageRule": {
                "enabled": True,
                "severity_override": "ADVICE",
                "custom_settings": {},
            }
        }
        out = normalize_config_rules(user_config, True, runtime, production)
        assert out["ScriptVarUsageRule"]["fix_strategy_override"] == "mechanical"

    def test_missing_rule_picks_up_production_default(self):
        runtime = ["ScriptVarUsageRule"]
        production = {
            "ScriptVarUsageRule": {
                "enabled": True,
                "severity_override": "ADVICE",
                "fix_strategy_override": "mechanical",
                "custom_settings": {},
            }
        }
        out = normalize_config_rules({}, True, runtime, production)
        assert out["ScriptVarUsageRule"]["fix_strategy_override"] == "mechanical"


class TestRouteHelpers:
    def test_default_fix_strategies_includes_all_runtime_rules(self):
        strategies = get_rule_default_fix_strategies()
        severities = get_rule_default_severities()
        # Same rule set as severity helper.
        assert set(strategies.keys()) == set(severities.keys())

    def test_default_fix_strategies_values_are_valid(self):
        from parser.rules.base import FixStrategy
        valid = {fs.value for fs in FixStrategy}
        strategies = get_rule_default_fix_strategies()
        for rule_name, value in strategies.items():
            assert value in valid, f"{rule_name} has invalid fix_strategy {value!r}"

    def test_known_rule_classifications(self):
        strategies = get_rule_default_fix_strategies()
        # Spot-check a few well-known classifications.
        assert strategies["ScriptVarUsageRule"] == "mechanical"
        assert strategies["HardcodedApplicationIdRule"] == "mechanical"
        assert strategies["StringBooleanRule"] == "mechanical"
        assert strategies["OrchestrationGlobalErrorHandlerRule"] == "design_decision"

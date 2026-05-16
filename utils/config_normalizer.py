"""
Configuration normalization helpers.

Ensures that user-provided configuration rule sets stay aligned with the
production-ready baseline and that new rules are injected with the
appropriate default enabled state.
"""

from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from utils.arcane_paths import resource_path


@lru_cache(maxsize=1)
def _load_production_rules() -> Dict[str, Dict[str, Any]]:
    """Load the production-ready rule definitions once."""
    production_path = Path(
        resource_path("config/rules/presets/production-ready.json")
    )
    with production_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    rules = data.get("rules", {})
    if not isinstance(rules, dict):
        return {}
    return rules


def get_production_rules() -> Dict[str, Dict[str, Any]]:
    """
    Return a deep copy of the production-ready rules.

    Returns:
        Dict[str, Dict[str, Any]]: canonical rule definitions.
    """
    return deepcopy(_load_production_rules())


def get_runtime_rule_names() -> list[str]:
    """
    Discover all available rule class names at runtime.
    
    Returns:
        list[str]: List of rule class names discovered from the rules engine.
    """
    try:
        from parser.rules_engine import RulesEngine
        from parser.config import ArcaneAuditorConfig
        
        # Create a config that enables all rules for discovery
        config = ArcaneAuditorConfig()
        engine = RulesEngine(config)
        
        # Extract rule class names
        rule_names = [rule.__class__.__name__ for rule in engine.rules]
        return rule_names
    except Exception:
        # Fallback: return empty list if discovery fails
        return []


def _merge_custom_settings(
    base: Optional[Dict[str, Any]], overlay: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    base = deepcopy(base or {})
    overlay = overlay or {}
    if not overlay:
        return base
    merged = base
    for key, value in overlay.items():
        merged[key] = value
    return merged


def normalize_config_rules(
    config_rules: Optional[Dict[str, Dict[str, Any]]],
    default_enabled: bool,
    runtime_rule_names: list[str],
    production_rules: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Normalize a rule configuration using runtime rule discovery as the source of truth.

    Args:
        config_rules: Existing rule configuration mapping from user's JSON.
        default_enabled: If True, newly introduced rules default to enabled.
            If False, missing rules are added disabled.
        runtime_rule_names: List of rule names discovered at runtime (source of truth).
        production_rules: Optional override of production rules (for default severity lookups).

    Returns:
        Normalized mapping of rules. Ghost rules (in config but not in runtime) are marked with _is_ghost=True.
    """
    production = (
        deepcopy(production_rules) if production_rules is not None else get_production_rules()
    )
    existing = deepcopy(config_rules or {})
    normalized: Dict[str, Dict[str, Any]] = {}
    matched_rules: set[str] = set()

    # Iterate over runtime rules (source of truth)
    for rule_name in runtime_rule_names:
        matched_rules.add(rule_name)
        production_rule = production.get(rule_name, {}) or {}
        current_rule = existing.get(rule_name, {})

        normalized_rule: Dict[str, Any] = {}

        # If rule exists in user's config, use their settings
        if rule_name in existing:
            if "enabled" in current_rule:
                normalized_rule["enabled"] = bool(current_rule["enabled"])
            else:
                # New rule not in config - use default
                normalized_rule["enabled"] = default_enabled

            if "severity_override" in current_rule:
                normalized_rule["severity_override"] = current_rule["severity_override"]
            else:
                # Fall back to production rule for default severity
                normalized_rule["severity_override"] = production_rule.get("severity_override")

            if "fix_strategy_override" in current_rule:
                normalized_rule["fix_strategy_override"] = current_rule["fix_strategy_override"]
            else:
                normalized_rule["fix_strategy_override"] = production_rule.get("fix_strategy_override")

            normalized_rule["custom_settings"] = _merge_custom_settings(
                production_rule.get("custom_settings"),
                current_rule.get("custom_settings"),
            )
        else:
            # Rule missing from user's config - treat as new default rule
            normalized_rule["enabled"] = default_enabled
            normalized_rule["severity_override"] = production_rule.get("severity_override")
            normalized_rule["fix_strategy_override"] = production_rule.get("fix_strategy_override")
            normalized_rule["custom_settings"] = deepcopy(production_rule.get("custom_settings", {}))

        normalized[rule_name] = normalized_rule

    # Identify 'Ghost Rules' - rules in config but not in runtime
    for rule_name, rule_config in existing.items():
        if rule_name not in matched_rules:
            # This is a ghost rule (likely deleted from codebase)
            ghost_rule = deepcopy(rule_config)
            ghost_rule["_is_ghost"] = True
            normalized[rule_name] = ghost_rule

    return normalized


"""
Parametrized tests asserting every concrete Rule subclass declares the expected
FIX_STRATEGY and CATEGORY metadata.

Classifications are intentionally explicit (not derived) so they're a contract
that's reviewed during code review, not silently inherited.
"""
import pytest
from parser.rules_engine import RulesEngine
from parser.rules.base import FixStrategy, Category
from utils.console import set_quiet


# (rule_class_name, expected_fix_strategy, expected_category)
EXPECTED_CLASSIFICATIONS = [
    # --- Script rules (mechanical) ---
    ("ScriptConsoleLogRule", FixStrategy.MECHANICAL, Category.SCRIPT),
    ("ScriptStringConcatRule", FixStrategy.MECHANICAL, Category.SCRIPT),
    ("ScriptVarUsageRule", FixStrategy.MECHANICAL, Category.SCRIPT),
    ("ScriptVerboseBooleanCheckRule", FixStrategy.MECHANICAL, Category.SCRIPT),
    # --- Script rules (localized) ---
    ("ScriptArrayMethodUsageRule", FixStrategy.LOCALIZED, Category.SCRIPT),
    ("ScriptDeadCodeRule", FixStrategy.LOCALIZED, Category.SCRIPT),
    ("ScriptEmptyFunctionRule", FixStrategy.LOCALIZED, Category.SCRIPT),
    ("ScriptOnSendSelfDataRule", FixStrategy.LOCALIZED, Category.SCRIPT),
    ("ScriptUnusedFunctionRule", FixStrategy.LOCALIZED, Category.SCRIPT),
    ("ScriptUnusedIncludesRule", FixStrategy.LOCALIZED, Category.SCRIPT),
    ("ScriptUnusedVariableRule", FixStrategy.LOCALIZED, Category.SCRIPT),
    # --- Script rules (naming required) ---
    ("ScriptDescriptiveParameterRule", FixStrategy.NAMING_REQUIRED, Category.SCRIPT),
    ("ScriptMagicNumberRule", FixStrategy.NAMING_REQUIRED, Category.SCRIPT),
    # --- Script rules (cascading rename) ---
    ("ScriptFunctionParameterNamingRule", FixStrategy.CASCADING_RENAME, Category.SCRIPT),
    ("ScriptVariableNamingRule", FixStrategy.CASCADING_RENAME, Category.SCRIPT),
    ("ScriptUnusedFunctionParametersRule", FixStrategy.CASCADING_RENAME, Category.SCRIPT),
    # --- Script rules (design decision — incl. multi-step rewrites; inherit defaults) ---
    ("ScriptFunctionReturnConsistencyRule", FixStrategy.DESIGN_DECISION, Category.SCRIPT),
    ("ScriptNestedArraySearchRule", FixStrategy.DESIGN_DECISION, Category.SCRIPT),
    ("ScriptComplexityRule", FixStrategy.DESIGN_DECISION, Category.SCRIPT),
    ("ScriptFunctionParameterCountRule", FixStrategy.DESIGN_DECISION, Category.SCRIPT),
    ("ScriptLongBlockRule", FixStrategy.DESIGN_DECISION, Category.SCRIPT),
    ("ScriptLongFunctionRule", FixStrategy.DESIGN_DECISION, Category.SCRIPT),
    ("ScriptNestingLevelRule", FixStrategy.DESIGN_DECISION, Category.SCRIPT),

    # --- Endpoint rules ---
    ("EndpointBaseUrlTypeRule", FixStrategy.LOCALIZED, Category.ENDPOINT),
    ("EndpointFailOnStatusCodesRule", FixStrategy.LOCALIZED, Category.ENDPOINT),
    ("EndpointNameLowerCamelCaseRule", FixStrategy.CASCADING_RENAME, Category.ENDPOINT),
    ("NoIsCollectionOnEndpointsRule", FixStrategy.MECHANICAL, Category.ENDPOINT),
    ("NoPMDSessionVariablesRule", FixStrategy.LOCALIZED, Category.ENDPOINT),
    ("OnlyMaximumEffortRule", FixStrategy.LOCALIZED, Category.ENDPOINT),

    # --- Widget rules ---
    ("GridPagingWithSortableFilterableRule", FixStrategy.DESIGN_DECISION, Category.WIDGET),
    ("WidgetIdLowerCamelCaseRule", FixStrategy.CASCADING_RENAME, Category.WIDGET),
    ("WidgetIdRequiredRule", FixStrategy.NAMING_REQUIRED, Category.WIDGET),

    # --- Orchestration rules ---
    ("OrchestratePreferExplicitDefaultAccessor", FixStrategy.MECHANICAL, Category.ORCHESTRATION),
    ("OrchestrationApiStepErrorHandlerRule", FixStrategy.DESIGN_DECISION, Category.ORCHESTRATION),
    ("OrchestrationBranchOnConditionsNestingRule", FixStrategy.DESIGN_DECISION, Category.ORCHESTRATION),
    ("OrchestrationGlobalErrorHandlerRule", FixStrategy.DESIGN_DECISION, Category.ORCHESTRATION),
    ("OrchestrationSecurityDomainRule", FixStrategy.DESIGN_DECISION, Category.ORCHESTRATION),
    ("OrchestrationVerboseBooleanCheckRule", FixStrategy.DESIGN_DECISION, Category.ORCHESTRATION),

    # --- Structure rules (mechanical) ---
    ("HardcodedApplicationIdRule", FixStrategy.MECHANICAL, Category.STRUCTURE),
    ("HardcodedWidRule", FixStrategy.MECHANICAL, Category.STRUCTURE),
    ("HardcodedWorkdayAPIRule", FixStrategy.MECHANICAL, Category.STRUCTURE),
    ("PMDSectionOrderingRule", FixStrategy.MECHANICAL, Category.STRUCTURE),
    ("StringBooleanRule", FixStrategy.MECHANICAL, Category.STRUCTURE),
    # --- Structure rules (localized) ---
    ("FooterPodRequiredRule", FixStrategy.LOCALIZED, Category.STRUCTURE),
    ("MultipleStringInterpolatorsRule", FixStrategy.LOCALIZED, Category.STRUCTURE),
    # --- Structure rules (cascading rename) ---
    ("FileNameLowerCamelCaseRule", FixStrategy.CASCADING_RENAME, Category.STRUCTURE),
    # --- Structure rules (design decision) ---
    ("EmbeddedImagesRule", FixStrategy.DESIGN_DECISION, Category.STRUCTURE),
    ("PMDSecurityDomainRule", FixStrategy.DESIGN_DECISION, Category.STRUCTURE),
]


@pytest.fixture(scope="module")
def discovered_rules():
    """Discover all rules once per module."""
    set_quiet(True)
    engine = RulesEngine()
    return {r.__class__.__name__: r for r in engine.rules}


def test_classification_table_covers_every_rule(discovered_rules):
    """The classification table must cover every concrete Rule subclass — no silent gaps."""
    classified = {name for name, _, _ in EXPECTED_CLASSIFICATIONS}
    discovered = set(discovered_rules.keys())
    missing = discovered - classified
    extra = classified - discovered
    assert not missing, f"Rules discovered but not classified: {sorted(missing)}"
    assert not extra, f"Rules classified but not discovered: {sorted(extra)}"


@pytest.mark.parametrize("rule_name,expected_strategy,expected_category", EXPECTED_CLASSIFICATIONS)
def test_rule_has_expected_classification(discovered_rules, rule_name, expected_strategy, expected_category):
    """Each rule must declare (or inherit) the expected FIX_STRATEGY and CATEGORY."""
    rule = discovered_rules.get(rule_name)
    assert rule is not None, f"Rule {rule_name} not discovered"
    assert rule.FIX_STRATEGY == expected_strategy, (
        f"{rule_name}: FIX_STRATEGY={rule.FIX_STRATEGY!r}, expected {expected_strategy!r}"
    )
    assert rule.CATEGORY == expected_category, (
        f"{rule_name}: CATEGORY={rule.CATEGORY!r}, expected {expected_category!r}"
    )

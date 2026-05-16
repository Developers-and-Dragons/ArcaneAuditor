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
    # --- Script rules ---
    ("ScriptConsoleLogRule", FixStrategy.ACTIONABLE, Category.SCRIPT),
    ("ScriptStringConcatRule", FixStrategy.ACTIONABLE, Category.SCRIPT),
    ("ScriptVarUsageRule", FixStrategy.ACTIONABLE, Category.SCRIPT),
    ("ScriptVerboseBooleanCheckRule", FixStrategy.ACTIONABLE, Category.SCRIPT),
    ("ScriptUnusedIncludesRule", FixStrategy.ACTIONABLE, Category.SCRIPT),

    ("ScriptArrayMethodUsageRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptDeadCodeRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptEmptyFunctionRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptOnSendSelfDataRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptUnusedFunctionRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptUnusedVariableRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptDescriptiveParameterRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptMagicNumberRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptFunctionParameterNamingRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptVariableNamingRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptUnusedFunctionParametersRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptFunctionReturnConsistencyRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptNestedArraySearchRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptComplexityRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptFunctionParameterCountRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptLongBlockRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptLongFunctionRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),
    ("ScriptNestingLevelRule", FixStrategy.HUMAN_REVIEW, Category.SCRIPT),

    # --- Endpoint rules ---
    ("EndpointFailOnStatusCodesRule", FixStrategy.ACTIONABLE, Category.ENDPOINT),
    ("OnlyMaximumEffortRule", FixStrategy.ACTIONABLE, Category.ENDPOINT),

    ("EndpointBaseUrlTypeRule", FixStrategy.HUMAN_REVIEW, Category.ENDPOINT),
    ("EndpointNameLowerCamelCaseRule", FixStrategy.HUMAN_REVIEW, Category.ENDPOINT),
    ("NoIsCollectionOnEndpointsRule", FixStrategy.HUMAN_REVIEW, Category.ENDPOINT),
    ("NoPMDSessionVariablesRule", FixStrategy.HUMAN_REVIEW, Category.ENDPOINT),

    # --- Widget rules ---
    ("GridPagingWithSortableFilterableRule", FixStrategy.HUMAN_REVIEW, Category.WIDGET),
    ("WidgetIdLowerCamelCaseRule", FixStrategy.HUMAN_REVIEW, Category.WIDGET),
    ("WidgetIdRequiredRule", FixStrategy.HUMAN_REVIEW, Category.WIDGET),

    # --- Orchestration rules ---
    ("OrchestratePreferExplicitDefaultAccessor", FixStrategy.HUMAN_REVIEW, Category.ORCHESTRATION),
    ("OrchestrationApiStepErrorHandlerRule", FixStrategy.HUMAN_REVIEW, Category.ORCHESTRATION),
    ("OrchestrationBranchOnConditionsNestingRule", FixStrategy.HUMAN_REVIEW, Category.ORCHESTRATION),
    ("OrchestrationGlobalErrorHandlerRule", FixStrategy.HUMAN_REVIEW, Category.ORCHESTRATION),
    ("OrchestrationSecurityDomainRule", FixStrategy.HUMAN_REVIEW, Category.ORCHESTRATION),
    ("OrchestrationVerboseBooleanCheckRule", FixStrategy.HUMAN_REVIEW, Category.ORCHESTRATION),

    # --- Structure rules ---
    ("HardcodedApplicationIdRule", FixStrategy.ACTIONABLE, Category.STRUCTURE),
    ("HardcodedWorkdayAPIRule", FixStrategy.ACTIONABLE, Category.STRUCTURE),
    ("PMDSectionOrderingRule", FixStrategy.HUMAN_REVIEW, Category.STRUCTURE),
    ("StringBooleanRule", FixStrategy.ACTIONABLE, Category.STRUCTURE),
    ("MultipleStringInterpolatorsRule", FixStrategy.ACTIONABLE, Category.STRUCTURE),

    ("HardcodedWidRule", FixStrategy.HUMAN_REVIEW, Category.STRUCTURE),
    ("FooterPodRequiredRule", FixStrategy.HUMAN_REVIEW, Category.STRUCTURE),
    ("FileNameLowerCamelCaseRule", FixStrategy.HUMAN_REVIEW, Category.STRUCTURE),
    ("EmbeddedImagesRule", FixStrategy.HUMAN_REVIEW, Category.STRUCTURE),
    ("PMDSecurityDomainRule", FixStrategy.HUMAN_REVIEW, Category.STRUCTURE),
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

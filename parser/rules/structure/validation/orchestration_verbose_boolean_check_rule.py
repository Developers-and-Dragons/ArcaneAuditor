"""Rule to flag redundant boolean wrapper expressions in orchestrations (if (X) true else false / if (X) false else true)."""

from typing import Any, Generator, Optional, Tuple, Union
from ...base import Finding, FixStrategy, Category
from ....models import ProjectContext, PMDModel, PodModel, OrchestrationModel
from ..shared import StructureRuleBase
from ..shared.orchestration_path_utils import (
    get_expression_source,
    resolve_ui_location,
    unwrap as _unwrap,
)


def _is_expression_object(d: Any) -> bool:
    """True if d is a dict with _type indicating Expr, _value is a dict, and _value contains 'source'."""
    if not isinstance(d, dict):
        return False
    type_val = d.get("_type")
    value_val = d.get("_value")
    if not isinstance(value_val, dict) or "source" not in value_val:
        return False
    if isinstance(type_val, list) and len(type_val) >= 1 and type_val[0] == "Expr":
        return True
    if isinstance(type_val, str) and type_val.startswith("Expr"):
        return True
    return False


def _is_boolean_expression(d: Any) -> bool:
    """True if d is an expression object and type is Boolean."""
    if not _is_expression_object(d):
        return False
    type_val = d.get("_type")
    if isinstance(type_val, list) and len(type_val) >= 2 and type_val[1] == "Boolean":
        return True
    value_val = d.get("_value")
    if isinstance(value_val, dict):
        type_node = value_val.get("type")
        unwrapped = _unwrap(type_node)
        if isinstance(unwrapped, str) and unwrapped == "Boolean":
            return True
    return False


def _is_redundant_boolean_wrapper(source: str) -> bool:
    """Detect only the full top-level pattern: if (X) true else false or if (X) false else true."""
    if not source or not isinstance(source, str):
        return False
    s = source.strip()
    if not s:
        return False
    # Optional outer parentheses
    if s.startswith("(") and s.endswith(")"):
        inner = s[1:-1].strip()
        if inner.startswith("if ("):
            s = inner
    if not s.startswith("if ("):
        return False
    # Find the closing parenthesis for the condition with balanced-paren counter
    start = 4  # after "if ("
    depth = 1
    i = start
    while i < len(s) and depth > 0:
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
        i += 1
    if depth != 0:
        return False
    # i points past the closing ); remainder is " true else false" or " false else true" (flexible whitespace)
    remainder = s[i:].strip()
    # Allow optional trailing )
    if remainder.endswith(")"):
        remainder = remainder[:-1].strip()
    normalized = " ".join(remainder.split())
    return normalized in ("true else false", "false else true")


def _walk_json(obj: Any, path: Tuple[Union[str, int], ...] = ()) -> Generator[Tuple[dict, Tuple[Union[str, int], ...]], None, None]:
    """Generic recursive walk; yield (expr_dict, path) for each Boolean expression. Path is from root to the expression."""
    if isinstance(obj, dict):
        if _is_boolean_expression(obj):
            yield (obj, path)
        for k, v in obj.items():
            yield from _walk_json(v, path + (k,))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            yield from _walk_json(item, path + (idx,))


class OrchestrationVerboseBooleanCheckRule(StructureRuleBase):
    """Flags boolean expressions that use the redundant pattern if (X) true else false or if (X) false else true."""

    ID = "OrchestrationVerboseBooleanCheckRule"
    DESCRIPTION = (
        "Detects redundant conditions with simple true/false values (if (X) true else false / if (X) false else true); "
        "This appears in a condition on a given step where the return values for true and false are true and false respectively."
    )
    SEVERITY = "ADVICE"
    CATEGORY = Category.ORCHESTRATION
    FIX_STRATEGY = FixStrategy.MECHANICAL
    AVAILABLE_SETTINGS = {}

    DOCUMENTATION = {
        "why": "This value is created using a Conditional wrapper that returns `true` or `false`. The condition itself already evaluates to a Boolean value, so the Conditional step is unnecessary.",
        "catches": [
            "Conditional value builders that return `true` when conditions are met and `false` otherwise.",
            "Conditional value builders that return `false` when conditions are met and `true` otherwise."
        ],
        "examples": "Example: A value configured as a Conditional where the result is `true` if the conditions are met and `false` otherwise. The conditions themselves already evaluate to a Boolean value. This is redundant and can be removed.",
        "recommendation": "Remove the Conditional wrapper and use the Boolean condition directly in the step. The condition already evaluates to `true` or `false`, so the extra Conditional step is not needed."
    }

    def get_description(self) -> str:
        return self.DESCRIPTION

    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        yield from ()

    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        yield from ()

    def visit_orchestration(
        self, orch_model: OrchestrationModel, context: ProjectContext
    ) -> Generator[Finding, None, None]:
        raw = orch_model.raw_value
        file_path = orch_model.file_path
        for expr_obj, path in _walk_json(raw):
            source = get_expression_source(expr_obj)
            if source and _is_redundant_boolean_wrapper(source):
                location = resolve_ui_location(raw, path)
                location_suffix = f" Location: {location}." if location else ""
                yield Finding(
                    rule=self,
                    file_path=file_path,
                    line=1,
                    message=(
                        f"{location_suffix} "
                        'Conditional step returns true/false based on a condition that already evaluates to true/false.'
                        f'This creates a redundant wrapper (internally generated as "if (foo == true) {{return true}} else {{return false}}"). '
                        'Remove the Conditional step and test the boolean directly.'
                    ),
                )

"""Rule to flag redundant boolean wrapper expressions in orchestrations (if (X) true else false / if (X) false else true)."""

from typing import Any, Generator, Optional, Tuple, Union
from ...base import Finding
from ....models import ProjectContext, PMDModel, PodModel, OrchestrationModel
from ..shared import StructureRuleBase
from ..shared.orchestration_path_utils import (
    get_container_display_name,
    get_owning_key_from_path,
    get_step_name_chain_from_path,
    navigate,
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


def _get_expression_source(expr_obj: Any) -> Optional[str]:
    """Unwrap _value.source to raw string; normalize to plain string. Return None if missing or not a string."""
    if not isinstance(expr_obj, dict):
        return None
    value_val = expr_obj.get("_value")
    if not isinstance(value_val, dict):
        return None
    source_node = value_val.get("source")
    raw = _unwrap(source_node)
    if isinstance(raw, str):
        return raw.strip()
    return None


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


def _get_ui_location(raw_value: Any, path: Tuple[Union[str, int], ...]) -> str:
    """
    Resolve path to a UI-oriented location: "StepName -> sublocation".
    Uses shared path helpers: step name from first node in path, sublocation from parent's display name or key.
    """
    if not path or not isinstance(raw_value, dict):
        return ""
    step_chain = get_step_name_chain_from_path(raw_value, path)
    if not step_chain:
        return _format_location_fallback(path)
    step_prefix = " -> ".join(step_chain)
    parent = navigate(raw_value, path[:-1]) if len(path) > 1 else None
    sub = get_container_display_name(parent) if isinstance(parent, dict) else None
    if not sub:
        # Prefer a meaningful owning key when path ends with envelope details like '_value'
        sub = get_owning_key_from_path(path)  # e.g. "filter", "condition", "expr"
    return f"{step_prefix} -> {sub}" if sub else step_prefix


def _format_location_fallback(path: Tuple[Union[str, int], ...]) -> str:
    """Fallback when UI location cannot be resolved: structural path (e.g. 'nodes -> node 2 -> condition')."""
    if not path:
        return ""
    parts: list[str] = []
    path_list = list(path)
    i = 0
    while i < len(path_list):
        seg = path_list[i]
        if seg == "_value":
            i += 1
            continue
        if isinstance(seg, int):
            prev = path_list[i - 1] if i > 0 else None
            prev2 = path_list[i - 2] if i > 1 else None
            if prev == "_value" and prev2 == "nodes":
                parts.append(f"node {seg + 1}")
            elif prev == "_value" and prev2 == "ifBranches":
                parts.append(f"branch {seg + 1}")
            elif prev == "_value" and prev2 == "values":
                parts.append(f"assignment {seg + 1}")
            else:
                parts.append(f"item {seg + 1}")
        else:
            if seg in ("condition", "expr", "nodes", "ifBranches", "values"):
                parts.append(seg)
        i += 1
    return " -> ".join(parts) if parts else ""


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
    AVAILABLE_SETTINGS = {}

    DOCUMENTATION = {
        "why": "Expressions like if (X) true else false are redundant; X already evaluates to a Boolean and can be used directly (or inverted for false else true).",
        "catches": [
            "Step conditions where the true/false return values are true and false (or inverted) respectively.",
        ],
        "examples": "Redundant boolean condition step: expression uses \"if (...) true else false\" (or \"false else true\"). The condition step is unnecessary as it already evaluates to a Boolean and can be used directly or inverted.",
        "recommendation": "Remove the condition step and test the value directly in the step itself.",
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
            source = _get_expression_source(expr_obj)
            if source and _is_redundant_boolean_wrapper(source):
                location = _get_ui_location(raw, path)
                location_suffix = f" Location: {location}." if location else ""
                yield Finding(
                    rule=self,
                    file_path=file_path,
                    line=1,
                    message=(
                        'Condition expression uses "if (...) true else false" '
                        '(or "false else true"). The condition step is unnecessary as it already evaluates to a Boolean and can be used directly.'
                        f"{location_suffix}"
                    ),
                )

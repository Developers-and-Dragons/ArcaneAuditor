"""Rule to prefer default-capable Orchestrate accessors over exception-throwing ones."""

import re
from typing import Any, Generator, List, Optional, Tuple, Union

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

# Unsafe function name -> tuple of preferred alternative(s). Only these exact names are flagged.
UNSAFE_TO_ALTERNATIVES: List[Tuple[str, Tuple[str, ...]]] = [
    ("booleanAtJsonPath", ("booleanAtJsonPathWithDefault",)),
    ("numberAtJsonPath", ("numberAtJsonPathWithDefault",)),
    ("objectAtJsonPath", ("objectAtJsonPathWithDefault",)),
    ("stringAtJsonPath", ("stringAtJsonPathWithDefault", "stringAtJsonPathOrEmptyString")),
    ("bigDecimalAtXPath", ("bigDecimalAtXPathWithDefault",)),
    ("booleanAtXPath", ("booleanAtXPathWithDefault",)),
    ("dateAtXPath", ("dateAtXPathWithDefault",)),
    ("dateTimeAtXPath", ("dateTimeAtXPathWithDefault",)),
    ("numberAtXPath", ("numberAtXPathWithDefault",)),
    ("stringAtXPath", ("stringAtXPathWithDefault", "stringAtXPathOrEmptyString")),
    ("xmlString", ("xmlStringWithDefault",)),
    ("zonedDateTimeAtXPath", ("zonedDateTimeAtXPathWithDefault",)),
]


def _is_expression_with_source(d: Any) -> bool:
    """True if d is a dict with _type indicating Expr and _value contains 'source'."""
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


def _get_expression_source(expr_obj: Any) -> Optional[str]:
    """Unwrap _value.source to raw string. Return None if missing or not a string."""
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


def _format_message(function_name: str, alternatives: Tuple[str, ...]) -> str:
    """Build finding message for one or two alternatives."""
    if len(alternatives) == 1:
        return (
            f'This expression uses "{function_name}", which throws an exception when the target value is not found. '
            f'Prefer "{alternatives[0]}" so missing values are handled explicitly, or validate first if the value is required.'
        )
    return (
        f'This expression uses "{function_name}", which throws an exception when the target value is not found. '
        f'Prefer "{alternatives[0]}" or "{alternatives[1]}" so missing values are handled explicitly, or validate first if the value is required.'
    )


def _get_ui_location(raw_value: Any, path: Tuple[Union[str, int], ...]) -> str:
    """Resolve path to a UI-oriented location: StepName -> sublocation."""
    if not path or not isinstance(raw_value, dict):
        return ""
    step_chain = get_step_name_chain_from_path(raw_value, path)
    if not step_chain:
        return _format_location_fallback(path)
    step_prefix = " -> ".join(step_chain)
    parent = navigate(raw_value, path[:-1]) if len(path) > 1 else None
    sub = get_container_display_name(parent) if isinstance(parent, dict) else None
    if not sub:
        sub = get_owning_key_from_path(path)
    return f"{step_prefix} -> {sub}" if sub else step_prefix


def _format_location_fallback(path: Tuple[Union[str, int], ...]) -> str:
    """Fallback when UI location cannot be resolved."""
    if not path:
        return ""
    parts: List[str] = []
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


def _walk_expressions(
    obj: Any, path: Tuple[Union[str, int], ...] = ()
) -> Generator[Tuple[dict, Tuple[Union[str, int], ...]], None, None]:
    """Recursive walk; yield (expr_dict, path) for every expression that has source."""
    if isinstance(obj, dict):
        if _is_expression_with_source(obj):
            yield (obj, path)
        for k, v in obj.items():
            yield from _walk_expressions(v, path + (k,))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            yield from _walk_expressions(item, path + (idx,))


class OrchestratePreferExplicitDefaultAccessor(StructureRuleBase):
    """Flags use of specific Orchestrate accessor functions that throw when value is not found; recommends default-capable alternatives."""

    ID = "OrchestratePreferExplicitDefaultAccessor"
    DESCRIPTION = "Prefer default-capable accessors over exception-throwing accessors"
    SEVERITY = "ADVICE"
    AVAILABLE_SETTINGS = {}

    DOCUMENTATION = {
        "why": "Some Orchestrate accessor functions throw an exception when a value is not found. Prefer the paired default-capable accessor so missing values are handled explicitly, or validate first when the value is required.",
        "catches": [
            "Calls to exception-throwing accessors (e.g. stringAtJsonPath, numberAtXPath) that have default-capable alternatives.",
        ],
        "examples": "Use stringAtJsonPathWithDefault or stringAtJsonPathOrEmptyString instead of stringAtJsonPath; use numberAtXPathWithDefault instead of numberAtXPath.",
        "recommendation": "Replace the reported function with the suggested alternative and supply an explicit default, or validate that the value exists before calling.",
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
        for expr_obj, path in _walk_expressions(raw):
            source = _get_expression_source(expr_obj)
            if not source:
                continue
            for unsafe_name, alternatives in UNSAFE_TO_ALTERNATIVES:
                pattern = re.compile(r"\b" + re.escape(unsafe_name) + r"\s*\(")
                for _ in pattern.finditer(source):
                    location = _get_ui_location(raw, path)
                    location_suffix = f" Location: {location}. " if location else ""
                    message = location_suffix + _format_message(unsafe_name, alternatives)
                    yield Finding(
                        rule=self,
                        file_path=file_path,
                        line=1,
                        message=message,
                    )

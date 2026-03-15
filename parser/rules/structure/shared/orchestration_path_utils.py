"""Shared helpers for resolving locations in orchestration flow JSON (paths, step names, etc.)."""

from typing import Any, Generator, List, Optional, Tuple, Union


def unwrap(obj: Any) -> Any:
    """Unwrap typed envelope: return obj['_value'] if obj is a dict with _value."""
    if obj is None:
        return None
    if isinstance(obj, dict) and "_value" in obj:
        return obj["_value"]
    return obj


def navigate(obj: Any, path: Tuple[Union[str, int], ...]) -> Any:
    """Follow path (keys/indices) into obj; return the value at that path or None if any step fails."""
    for seg in path:
        if obj is None:
            return None
        if isinstance(obj, dict) and seg in obj:
            obj = obj[seg]
        elif isinstance(obj, list) and isinstance(seg, int) and 0 <= seg < len(obj):
            obj = obj[seg]
        else:
            return None
    return obj


def get_step_name_from_path(raw_value: Any, path: Tuple[Union[str, int], ...]) -> str:
    """
    Return the step reference name for the first node appearing in path.

    Walks the path to find the segment pattern (nodes, _value, node_index), then
    resolves that node's _value and returns its name (Identifier). Use this when
    you have a path into the flow and need a human-readable step name for messages.

    Returns the step name string, or "node {index+1}" if the node has no name,
    or "" if the path does not go through flow nodes.
    """
    chain = get_step_name_chain_from_path(raw_value, path)
    return chain[0] if chain else ""


def get_step_name_chain_from_path(raw_value: Any, path: Tuple[Union[str, int], ...]) -> list[str]:
    """
    Return a list of step reference names for every node encountered in the path.

    Generic across step types and nesting: any time the path includes
    ('nodes', '_value', index) we resolve that index against the *owning object*
    at that point in the path (not just the flow root). This supports nested
    groups/branches/loops that contain their own 'nodes' lists.
    """
    if not path:
        return []
    path_list = list(path)
    out: list[str] = []
    for i in range(len(path_list) - 2):
        if path_list[i] != "nodes" or path_list[i + 1] != "_value":
            continue
        ni = path_list[i + 2]
        if not isinstance(ni, int):
            continue

        owner = raw_value if i == 0 else navigate(raw_value, tuple(path_list[:i]))
        if not isinstance(owner, dict):
            continue
        nodes_val = unwrap(owner.get("nodes"))
        if not isinstance(nodes_val, list) or ni < 0 or ni >= len(nodes_val):
            continue

        node = nodes_val[ni]
        node_value = unwrap(node) if isinstance(node, dict) else None
        if not isinstance(node_value, dict):
            continue
        name_val = unwrap(node_value.get("name"))
        if isinstance(name_val, str) and name_val:
            out.append(name_val)
        else:
            out.append(f"node {ni + 1}")
    return out


def get_container_display_name(container: Any) -> Optional[str]:
    """
    Get a human-readable name from a container dict (e.g. branch, assignment).

    Tries 'name' (Identifier) then 'param.name' (Parameter). Works for any
    step structure that uses these common patterns.
    """
    if not isinstance(container, dict):
        return None
    name_val = unwrap(container.get("name"))
    if isinstance(name_val, str):
        return name_val
    param = container.get("param")
    pv = unwrap(param) if isinstance(param, dict) else None
    if isinstance(pv, dict):
        param_name = unwrap(pv.get("name"))
        if isinstance(param_name, str):
            return param_name
    return None


def get_owning_key_from_path(path: Tuple[Union[str, int], ...]) -> str:
    """
    Return a stable, user-meaningful key name from a JSON path.

    Useful when the last segment is an envelope detail like '_value' (e.g. Opt wrappers),
    in which case we want the owning key like 'filter' instead of '_value'.
    """
    if not path:
        return ""
    for seg in reversed(path):
        if isinstance(seg, str) and seg != "_value":
            return seg
    return ""


# --- CreateJson Mapping path label (row label for mapping expr) ---


def _normalize_mapping_path_label(path_value: str) -> str:
    """Use mapping path as row label; only strip leading '$.' when present. No other parsing."""
    if not path_value or not isinstance(path_value, str):
        return path_value or ""
    s = path_value.strip()
    if s.startswith("$."):
        return s[2:]
    return s


def _get_mapping_path_label(mapping_node: Any) -> Optional[str]:
    """If mapping_node is a Mapping with a path (JsonPath), return normalized label; else None."""
    if not isinstance(mapping_node, dict):
        return None
    path_node = mapping_node.get("path")
    raw = unwrap(path_node)
    if not isinstance(raw, str):
        return None
    return _normalize_mapping_path_label(raw)


def _path_inside_createjson_mapping(
    raw_value: Any, path: Tuple[Union[str, int], ...]
) -> Optional[Tuple[Tuple[Union[str, int], ...], Any]]:
    """
    If path goes through values -> _value -> i -> _value (Mapping), return (path_to_mapping, mapping_node).
    Else return None.
    """
    path_list = list(path)
    for i in range(len(path_list) - 3):
        if (
            path_list[i] == "values"
            and path_list[i + 1] == "_value"
            and isinstance(path_list[i + 2], int)
            and path_list[i + 3] == "_value"
        ):
            prefix = tuple(path_list[: i + 4])
            mapping = navigate(raw_value, prefix)
            if isinstance(mapping, dict) and "path" in mapping:
                return (prefix, mapping)
    return None


# --- User-facing location resolution ---


def format_location_fallback(path: Tuple[Union[str, int], ...]) -> str:
    """
    Human-meaningful fallback when step chain cannot be resolved.
    Does not emit raw internal tokens (expr, nodes, values, ifBranches); uses user-facing labels.
    """
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
            if seg == "expr":
                parts.append("value")
            elif seg == "condition":
                parts.append("condition")
            elif seg == "nodes":
                pass
            elif seg == "ifBranches":
                pass
            elif seg == "values":
                pass
            else:
                parts.append(seg)
        i += 1
    return " -> ".join(parts) if parts else ""


def resolve_ui_location(raw_value: Any, path: Tuple[Union[str, int], ...]) -> str:
    """
    Resolve path to user-facing Orchestrate location text: "StepName -> sublocation".

    - CreateJson mapping: if path is inside a Mapping (values -> _value -> i -> _value -> expr...),
      uses step name + mapping path as row label (path with only leading '$.' stripped).
    - Otherwise: step name chain + container display name or mapping path if parent is Mapping,
      or normalized fallback (no raw 'expr' / 'nodes' / 'values' / 'ifBranches').
    """
    if not path or not isinstance(raw_value, dict):
        return ""

    mapping_info = _path_inside_createjson_mapping(raw_value, path)
    if mapping_info is not None:
        path_to_mapping, mapping_node = mapping_info
        step_chain = get_step_name_chain_from_path(raw_value, path_to_mapping)
        label = _get_mapping_path_label(mapping_node)
        if step_chain and label is not None:
            step_prefix = " -> ".join(step_chain)
            if label != step_chain[-1]:
                return f"{step_prefix} -> {label}"
            return step_prefix
        if label is not None:
            return label

    step_chain = get_step_name_chain_from_path(raw_value, path)
    if not step_chain:
        return format_location_fallback(path)

    step_prefix = " -> ".join(step_chain)
    parent = navigate(raw_value, path[:-1]) if len(path) > 1 else None

    if isinstance(parent, dict):
        parent_mapping_label = _get_mapping_path_label(parent)
        if parent_mapping_label is not None:
            if parent_mapping_label != step_chain[-1]:
                return f"{step_prefix} -> {parent_mapping_label}"
            return step_prefix
        sub = get_container_display_name(parent)
    else:
        sub = None

    if not sub:
        key = get_owning_key_from_path(path)
        sub = "value" if key == "expr" else (key if key else None)
    if sub and sub != step_chain[-1]:
        return f"{step_prefix} -> {sub}"
    return step_prefix


def get_expression_source(expr_obj: Any) -> Optional[str]:
    """Unwrap _value.source from an Expr dict to raw string. Return None if missing or not a string."""
    return _get_expression_source(expr_obj)


# --- Walking orchestration source strings (Expr source + TextTemplate body) ---


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
    raw = unwrap(source_node)
    if isinstance(raw, str):
        return raw.strip()
    return None


def _is_text_template_node(d: Any) -> bool:
    """True if d is a dict with _type TextTemplate and _value is a string (e.g. CreateTextTemplate message)."""
    if not isinstance(d, dict):
        return False
    type_val = d.get("_type")
    value_val = d.get("_value")
    if not isinstance(value_val, str):
        return False
    if type_val == "TextTemplate":
        return True
    if isinstance(type_val, list) and len(type_val) >= 1 and type_val[0] == "TextTemplate":
        return True
    return False


def walk_orchestration_source_strings(
    obj: Any, path: Tuple[Union[str, int], ...] = ()
) -> Generator[Tuple[str, Tuple[Union[str, int], ...]], None, None]:
    """
    Yield (source_string, path) for every script-bearing place in orchestration JSON.

    Covers:
    - Expr nodes: _value.source (conditions, value expressions, mappings, etc.)
    - TextTemplate nodes: _value string (e.g. CreateTextTemplate message with {{ ... }}).

    Path is the tuple of keys/indices from the flow root to the node, for location resolution.
    """
    if isinstance(obj, dict):
        if _is_expression_with_source(obj):
            source = _get_expression_source(obj)
            if source:
                yield (source, path)
        if _is_text_template_node(obj):
            value_val = obj.get("_value")
            if isinstance(value_val, str):
                yield (value_val, path)
        for k, v in obj.items():
            yield from walk_orchestration_source_strings(v, path + (k,))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            yield from walk_orchestration_source_strings(item, path + (idx,))

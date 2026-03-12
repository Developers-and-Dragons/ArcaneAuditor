"""Shared helpers for resolving locations in orchestration flow JSON (paths, step names, etc.)."""

from typing import Any, Optional, Tuple, Union


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

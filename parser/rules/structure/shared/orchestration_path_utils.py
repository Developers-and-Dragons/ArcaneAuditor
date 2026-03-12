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
    if not path or not isinstance(raw_value, dict):
        return ""
    path_list = list(path)
    for i in range(len(path_list) - 1):
        if path_list[i] == "nodes" and path_list[i + 1] == "_value" and i + 2 < len(path_list):
            ni = path_list[i + 2]
            if not isinstance(ni, int):
                continue
            nodes_val = unwrap(raw_value.get("nodes"))
            if not isinstance(nodes_val, list) or ni < 0 or ni >= len(nodes_val):
                continue
            node = nodes_val[ni]
            node_value = unwrap(node) if isinstance(node, dict) else None
            if not isinstance(node_value, dict):
                continue
            name_val = unwrap(node_value.get("name"))
            if isinstance(name_val, str):
                return name_val
            return f"node {ni + 1}"
    return ""


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

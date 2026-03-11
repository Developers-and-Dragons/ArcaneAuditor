"""Shared helpers for orchestration error-handler rules (global and API step)."""

from typing import Any, List

LOG_NODE_TYPE = "Log"
SEND_INTEGRATION_MESSAGE_NODE_TYPE = "SendIntegrationMessage"
FLOW_INTEGRATION = ".maya.IntegrationFrameworkTrigger"


def unwrap(obj: Any) -> Any:
    """Unwrap typed envelope: return obj['_value'] if obj is a dict with _value."""
    if obj is None:
        return None
    if isinstance(obj, dict) and "_value" in obj:
        return obj["_value"]
    return obj


def unwrap_nodes_list(nodes_obj: Any) -> List[dict]:
    """Return list of node dicts from a nodes envelope (e.g. flow nodes or group nodes)."""
    if nodes_obj is None:
        return []
    val = unwrap(nodes_obj)
    if isinstance(val, list):
        return val
    return []


def get_error_handler_nodes(error_handler_obj: Any) -> List[dict]:
    """Get the list of node dicts from an error handler (unwrap errorHandler envelope then inner _value, then nodes)."""
    if error_handler_obj is None:
        return []
    outer = unwrap(error_handler_obj)
    if not isinstance(outer, dict):
        return []
    inner = unwrap(outer)
    if not isinstance(inner, dict):
        return []
    return unwrap_nodes_list(inner.get("nodes"))


def handler_has_log_step(handler_nodes: List[dict]) -> bool:
    """Return True if any node in the handler has _type == Log."""
    return any(
        isinstance(n, dict) and n.get("_type") == LOG_NODE_TYPE
        for n in handler_nodes
    )


def handler_has_log_or_integration_step(handler_nodes: List[dict]) -> bool:
    """Return True if any node has _type Log or SendIntegrationMessage."""
    return any(
        isinstance(n, dict) and n.get("_type") in (LOG_NODE_TYPE, SEND_INTEGRATION_MESSAGE_NODE_TYPE)
        for n in handler_nodes
    )

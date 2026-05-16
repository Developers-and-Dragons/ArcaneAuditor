"""Convert internal dotted paths to JSONPath form for v2 agent-mode findings.
"""
from typing import Iterable, Optional, Union


def tuple_path_to_jsonpath(path: Optional[Iterable[Union[str, int]]]) -> Optional[str]:
    """Convert a tuple/list path (mixed keys + ints) to JSONPath form.

    Used by orchestration rules where `orchestration_path_utils` produces
    paths like ``('endpoints', 'foo', 'nodes', '_value', 2)``.
    """
    if path is None:
        return None
    segs = list(path)
    if not segs:
        return None
    out = "$"
    for seg in segs:
        if isinstance(seg, int):
            out += f"[{seg}]"
        else:
            out += f".{seg}"
    return out


# Roots for the three endpoint collections an agent might land on.
_ENDPOINT_ROOTS = {
    "inbound": "$.inboundEndpoints",
    "outbound": "$.outboundEndpoints",
    "pod": "$.seed.endPoints",
}


def dotted_to_jsonpath(dotted: Optional[str]) -> Optional[str]:
    """Convert ``body.children.0.onLoad`` -> ``$.body.children[0].onLoad``.

    Numeric segments become bracket-indexed; non-numeric segments stay
    dot-prefixed. Inputs already starting with ``$`` are returned unchanged
    so callers can pass through pre-formed JSONPaths safely.
    """
    if not dotted:
        return None
    if dotted.startswith("$"):
        return dotted
    out = "$"
    for part in dotted.split("."):
        if not part:
            continue
        if part.isdigit():
            out += f"[{part}]"
        else:
            out += f".{part}"
    return out if out != "$" else None


def data_provider_jsonpath(key: Optional[str]) -> Optional[str]:
    """JSONPath to an AMD ``dataProviders`` entry by ``key``."""
    if not key:
        return None
    return f"$.dataProviders[?(@.key=='{key}')].value"


def endpoint_jsonpath(
    endpoint_type: str,
    name: Optional[str],
    index: Optional[int] = None,
    subkey: Optional[str] = None,
) -> Optional[str]:
    """Build a JSONPath that points at an endpoint (or one of its fields).

    ``endpoint_type`` is ``'inbound'``, ``'outbound'``, or ``'pod'``. Use
    the endpoint's ``name`` for a stable selector when present; fall back
    to ``[index]`` for unnamed endpoints. ``subkey`` appends a final field
    segment (e.g. ``'bestEffort'``).
    """
    root = _ENDPOINT_ROOTS.get(endpoint_type)
    if root is None:
        return None
    if name:
        selector = f"[?(@.name=='{name}')]"
    elif index is not None:
        selector = f"[{index}]"
    else:
        return root
    base = f"{root}{selector}"
    return f"{base}.{subkey}" if subkey else base

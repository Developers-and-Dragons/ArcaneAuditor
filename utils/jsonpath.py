"""Convert internal dotted paths to JSONPath form for v2 agent-mode findings.
"""
from typing import Optional


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

"""Source-snippet helper for Finding enrichment.

Returns a small slice of raw source text around a 1-based line number, or
None when the source is missing or the line is out of range. Kept dependency-
free so it can be invoked lazily from the JSON formatter without pulling in
parser internals.
"""
from typing import Optional


def make_snippet(source_content: Optional[str], line: int, context: int = 2) -> Optional[str]:
    if not source_content or line <= 0:
        return None
    lines = source_content.splitlines()
    if not lines:
        return None
    idx = line - 1
    if idx >= len(lines):
        return None
    start = max(0, idx - context)
    end = min(len(lines), idx + context + 1)
    return "\n".join(lines[start:end])

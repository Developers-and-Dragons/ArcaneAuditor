"""Shared violation handling for all rule types."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Violation:
    """Represents a code violation with consistent structure."""
    message: str
    line: int
    metadata: Optional[Dict[str, Any]] = None
    suggested_replacement: Optional[str] = None
    path: Optional[str] = None
    # Agent-only enrichment: lets agents apply fragment fixes deterministically.
    # target_text: the exact original substring suggested_replacement should swap in for.
    # replacement_context: how to apply — "substring" | "full_field" | "array_splice" | "field_insert".
    target_text: Optional[str] = None
    replacement_context: Optional[str] = None

    def __post_init__(self):
        """Ensure metadata is always a dict."""
        if self.metadata is None:
            self.metadata = {}

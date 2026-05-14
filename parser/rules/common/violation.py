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
    
    def __post_init__(self):
        """Ensure metadata is always a dict."""
        if self.metadata is None:
            self.metadata = {}

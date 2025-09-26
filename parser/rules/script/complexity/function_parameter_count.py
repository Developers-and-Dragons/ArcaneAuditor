"""Script function parameter count rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .function_parameter_count_detector import FunctionParameterCountDetector


class ScriptFunctionParameterCountRule(ScriptRuleBase):
    """Rule to check for functions with too many parameters."""

    DESCRIPTION = "Functions should not have too many parameters (max 4 by default)"
    SEVERITY = "WARNING"
    DETECTOR = FunctionParameterCountDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

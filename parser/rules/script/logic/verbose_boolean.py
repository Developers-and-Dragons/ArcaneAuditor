"""Script verbose boolean check rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .verbose_boolean_detector import VerboseBooleanDetector


class ScriptVerboseBooleanCheckRule(ScriptRuleBase):
    """Rule to check for overly verbose boolean checks."""

    DESCRIPTION = "Ensures scripts don't use overly verbose boolean checks (if(var == true) return true else return false)"
    SEVERITY = "ADVICE"
    DETECTOR = VerboseBooleanDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def _check_verbose_boolean_patterns(self, script_content, field_name, file_path, line_offset=1, context=None):
        """Check for overly verbose boolean patterns in script content using AST parsing."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content, context)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Create detector and set original content for operator detection
        detector = self.DETECTOR(file_path, line_offset)
        detector.set_original_content(script_content)
        
        # Use detector to find violations
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        for violation in violations:
            yield self._create_finding_from_violation(violation, file_path)

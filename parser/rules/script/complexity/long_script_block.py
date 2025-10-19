#!/usr/bin/env python3
"""Long script block rule for PMD/POD files."""

from ...script.shared import ScriptRuleBase
from ...base import Finding
from .long_script_block_detector import LongScriptBlockDetector


class ScriptLongBlockRule(ScriptRuleBase):
    """Rule to check for script blocks that exceed maximum line count."""

    ID = "ScriptLongBlockRule"
    DESCRIPTION = "Ensures non-function script blocks in PMD/POD files don't exceed maximum line count (max 30 lines). Excludes function definitions which are handled by ScriptLongFunctionRule."
    SEVERITY = "ADVICE"
    DETECTOR = LongScriptBlockDetector

    def __init__(self):
        super().__init__()
        self.max_lines = 30
        self.skip_comments = False  # Default to ESLint behavior
        self.skip_blank_lines = False  # Default to ESLint behavior

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def apply_settings(self, custom_settings: dict):
        """Apply custom settings from configuration."""
        if 'max_lines' in custom_settings:
            self.max_lines = custom_settings['max_lines']
        if 'skip_comments' in custom_settings:
            self.skip_comments = custom_settings['skip_comments']
        if 'skip_blank_lines' in custom_settings:
            self.skip_blank_lines = custom_settings['skip_blank_lines']
    
    def _analyze_script(self, script_model, context=None):
        """Override to skip standalone script files entirely.
        
        ScriptLongBlockRule only applies to embedded script blocks in PMD/POD files,
        not to standalone .script files which are handled by ScriptLongFunctionRule.
        """
        # Skip standalone script files entirely - they should only be analyzed
        # by ScriptLongFunctionRule, not ScriptLongBlockRule
        return
    
    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None):
        """Override to pass custom settings to detector."""
        # Strip <% %> tags from script content if present
        clean_script_content = self._strip_script_tags(script_content)
        
        # Parse the script content with context for caching
        ast = self._parse_script_content(clean_script_content, context)
        if not ast:
            return
        
        # Use detector to find violations, passing custom settings AND stripped content
        detector = self.DETECTOR(file_path, line_offset, self.max_lines, self.skip_comments, self.skip_blank_lines, clean_script_content)
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        if violations is not None and hasattr(violations, '__iter__') and not isinstance(violations, str):
            for violation in violations:
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=violation.line,
                    file_path=file_path
                )

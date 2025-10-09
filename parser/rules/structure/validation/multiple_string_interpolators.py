"""
Rule to detect multiple string interpolators in a single string value.

Multiple interpolators (<% %>) in a single string are harder to read and maintain.
Using a single template literal with embedded expressions is cleaner and more performant.

Example:
  Bad:  "My name is <% name %> and I like <% food %>"
  Good: "<% `My name is ${name} and I like ${food}` %>"
"""
import re
from typing import Generator

from ...base import Finding
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class MultipleStringInterpolatorsRule(StructureRuleBase):
    """
    Detects multiple string interpolators that should be replaced with template literals.
    
    This rule checks:
    - PMD files
    - POD files
    
    Flags strings with 2+ interpolators (<% ... %>).
    """
    
    ID = "MultipleStringInterpolatorsRule"
    DESCRIPTION = "Detects multiple string interpolators in a single string which should use template literals instead"
    SEVERITY = "ADVICE"
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for multiple string interpolators."""
        if not pmd_model.source_content:
            return
        
        yield from self._check_source_content_for_multiple_interpolators(
            pmd_model.source_content, 
            pmd_model.file_path
        )
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for multiple string interpolators."""
        if not pod_model.source_content:
            return
        
        yield from self._check_source_content_for_multiple_interpolators(
            pod_model.source_content,
            pod_model.file_path
        )
    
    def _check_source_content_for_multiple_interpolators(self, source_content: str, file_path: str) -> Generator[Finding, None, None]:
        """Check source content for strings with multiple interpolators."""
        if not source_content:
            return
        
        # Find all string values that might contain interpolators
        # Pattern: "value": "..." or 'value': '...'
        # We need to find strings that contain multiple <% %> patterns
        
        # First, find all JSON string values (quoted strings)
        # This regex finds strings in JSON format: "key": "value" or 'key': 'value'
        string_pattern = r'["\']([^"\']*(?:<%[^>]*%>)[^"\']*(?:<%[^>]*%>)[^"\']*)["\']'
        
        matches = re.finditer(string_pattern, source_content)
        
        for match in matches:
            string_value = match.group(1)  # The content inside quotes
            
            # Count interpolators in this string
            interpolator_pattern = r'<%[^>]*%>'
            interpolators = re.findall(interpolator_pattern, string_value)
            
            if len(interpolators) >= 2:
                # Check if it's already a template literal (has backticks)
                if '`' in string_value and '${' in string_value:
                    continue  # Already using template literal
                
                # Calculate line number
                line_num = self.get_line_from_text_position(source_content, match.start())
                
                # Create suggestion
                suggestion = self._create_template_literal_suggestion(string_value, interpolators)
                
                yield self._create_finding(
                    message=f"String has {len(interpolators)} interpolators. Use a SINGLE interpolator with a template literal inside: {suggestion}",
                    file_path=file_path,
                    line=line_num
                )
    
    def _create_template_literal_suggestion(self, original_string: str, interpolators: list) -> str:
        """Create a suggestion showing template literal usage."""
        # Simple example - show the concept
        return "<% `Use template literal with ${{variable}}` %>"


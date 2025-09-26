from typing import Generator, List, Dict, Any
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel
import json


class PMDSectionOrderingRule(Rule):
    """Validates that PMD file sections follow the configured ordering."""
    
    DESCRIPTION = "Ensures PMD file root-level sections follow consistent ordering for better readability"
    SEVERITY = "INFO"

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with configurable section order."""
        # Default section order based on updated PMD standards
        default_order = [
            "id",
            "securityDomains",
            "include", 
            "script",
            "endPoints",
            "onSubmit",
            "outboundData",
            "onLoad",
            "presentation"
        ]
        
        self.section_order = config.get("section_order", default_order) if config else default_order

    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD files for section ordering."""
        for pmd_model in context.pmds.values():
            yield from self._analyze_pmd_section_order(pmd_model)

    def _analyze_pmd_section_order(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Analyze a single PMD file for section ordering."""
        try:
            # Parse the PMD source to get the actual key order
            actual_order = self._extract_root_key_order(pmd_model)
            
            if not actual_order:
                return
            
            # Check ordering
            yield from self._check_section_ordering(actual_order, pmd_model)
            
        except Exception as e:
            print(f"Warning: Failed to analyze section ordering in {pmd_model.file_path}: {e}")

    def _extract_root_key_order(self, pmd_model: PMDModel) -> List[str]:
        """Extract the order of root-level keys from the PMD source."""
        try:
            # The Workday Extend compiler ensures valid JSON structure
            pmd_data = json.loads(pmd_model.source_content)
            return list(pmd_data.keys())
        except json.JSONDecodeError as e:
            # Handle false positive control character errors
            # Some JSON parsers incorrectly flag valid characters in strings
            if "Invalid control character" in str(e):
                # Try parsing with a more lenient approach using regex
                return self._extract_keys_with_regex(pmd_model.source_content)
            else:
                raise e

    def _extract_keys_with_regex(self, content: str) -> List[str]:
        """Extract root-level keys using regex as a fallback method."""
        import re
        
        # Find root-level keys (minimal indentation - 2 spaces or less)
        # This ensures we don't pick up nested properties
        pattern = r'^(\s{0,2})"([^"]+)"\s*:'
        
        keys = []
        for line in content.split('\n'):
            match = re.match(pattern, line)
            if match:
                indent_level = len(match.group(1))
                key = match.group(2)
                
                # Only include keys with minimal indentation (0-2 spaces)
                # This filters out nested properties which have more indentation
                if indent_level <= 2 and key not in keys:
                    keys.append(key)
        
        return keys


    def _check_section_ordering(self, actual_order: List[str], pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Check if the actual order matches the configured order."""
        
        # Get expected order for the keys that are actually present
        expected_order = self._get_expected_order_for_keys(actual_order)
        
        # Check if ordering is correct
        if actual_order == expected_order:
            return  # No violations found
        
        # Generate a single finding showing the full order comparison
        current_order_str = " → ".join(actual_order)
        expected_order_str = " → ".join(expected_order)
        
        # Find the first violation for line number reference
        first_violation_line = self._get_first_violation_line(pmd_model, actual_order, expected_order)
        
        yield Finding(
            rule=self,
            message=f"PMD sections are not in the correct order. Current: [{current_order_str}] | Expected: [{expected_order_str}]",
            line=first_violation_line,
            column=1,
            file_path=pmd_model.file_path
        )

    def _get_expected_order_for_keys(self, actual_keys: List[str]) -> List[str]:
        """Get the expected order for only the keys that are actually present."""
        expected_order = []
        
        # Add keys in the configured order if they exist in the actual PMD
        for key in self.section_order:
            if key in actual_keys:
                expected_order.append(key)
        
        # Add any keys that aren't in the configured order at the end
        for key in actual_keys:
            if key not in expected_order:
                expected_order.append(key)
        
        return expected_order

    def _get_first_violation_line(self, pmd_model: PMDModel, actual_order: List[str], expected_order: List[str]) -> int:
        """Get the line number of the first section that's out of order."""
        for i, key in enumerate(actual_order):
            expected_index = expected_order.index(key) if key in expected_order else i
            
            if i != expected_index:
                return self._get_key_line_number(pmd_model, key)
        
        return 1  # Fallback

    def _get_key_line_number(self, pmd_model: PMDModel, key: str) -> int:
        """Get the line number where a root-level key is defined."""
        try:
            if pmd_model.source_content:
                lines = pmd_model.source_content.split('\n')
                for i, line in enumerate(lines):
                    # Look for the key at the start of a line (root level)
                    stripped_line = line.strip()
                    if stripped_line.startswith(f'"{key}":'):
                        return i + 1  # Convert to 1-based line numbering
            return 1  # Fallback to line 1
        except Exception:
            return 1

"""Script unused script includes rule using unified architecture."""

from typing import Generator, Set, Any
from ...script.shared import ScriptRuleBase
from ...base import Finding
from ....models import PMDModel
from .unused_script_includes_detector import UnusedScriptIncludesDetector


class ScriptUnusedScriptIncludesRule(ScriptRuleBase):
    """Validates that included script files are actually used in PMD files."""

    DESCRIPTION = "Ensures included script files are actually used (via script.function() calls)"
    SEVERITY = "ACTION"
    DETECTOR = UnusedScriptIncludesDetector

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

    def analyze(self, context) -> Generator[Finding, None, None]:
        """Analyze PMD files for unused script includes."""
        for pmd_model in context.pmds.values():
            yield from self._analyze_pmd_script_includes(pmd_model, context)

    def _analyze_pmd_script_includes(self, pmd_model: PMDModel, context=None) -> Generator[Finding, None, None]:
        """Analyze a PMD file for unused script includes."""
        try:
            # Get included script files
            included_scripts = self._get_included_scripts(pmd_model)
            if not included_scripts:
                return
            
            # Get all script calls in the PMD
            script_calls = self._get_script_calls_in_pmd(pmd_model, context)
            
            # Convert included scripts to base names for comparison
            included_base_names = set()
            for script_file in included_scripts:
                base_name = self._get_script_prefix(script_file)
                included_base_names.add(base_name)
            
            # Use detector to find violations
            detector = self.DETECTOR(pmd_model.file_path, 1, included_base_names, script_calls)
            violations = detector.detect(None, "script_includes")
            
            # Convert violations to findings
            for violation in violations:
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=self._get_include_line_number(pmd_model, violation.metadata.get('script_name', '')),
                    file_path=pmd_model.file_path
                )
                
        except Exception as e:
            print(f"Warning: Failed to analyze script includes in {pmd_model.file_path}: {e}")

    def _get_included_scripts(self, pmd_model: PMDModel) -> Set[str]:
        """Get included script files from PMD model."""
        included_scripts = set()
        
        if hasattr(pmd_model, 'includes') and pmd_model.includes and pmd_model.includes.scripts:
            for script_file in pmd_model.includes.scripts:
                if script_file:
                    included_scripts.add(script_file)
        
        return included_scripts

    def _get_script_calls_in_pmd(self, pmd_model: PMDModel, context=None) -> Set[str]:
        """Get all script calls in the PMD."""
        script_calls = set()
        
        # Analyze all script fields
        script_fields = self.find_script_fields(pmd_model, context)
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and field_value.strip():
                try:
                    ast = self._parse_script_content(field_value, context)
                    if ast:
                        # Find script calls (script.function() pattern)
                        ast_calls_found = False
                        for node in ast.find_data('arguments_expression'):
                            script_name = self._extract_script_name_from_call(node)
                            if script_name:
                                script_calls.add(script_name)
                                ast_calls_found = True
                        
                        # If AST parsing succeeded but found no script calls, try fallback
                        if not ast_calls_found:
                            fallback_calls = self._extract_script_calls_fallback(field_value)
                            script_calls.update(fallback_calls)
                    else:
                        # If AST parsing failed (returned None), fall back to string matching
                        fallback_calls = self._extract_script_calls_fallback(field_value)
                        script_calls.update(fallback_calls)
                except Exception:
                    # If AST parsing throws an exception, fall back to string matching
                    fallback_calls = self._extract_script_calls_fallback(field_value)
                    script_calls.update(fallback_calls)
        
        return script_calls

    def _extract_script_calls_fallback(self, script_content: str) -> Set[str]:
        """Fallback method to extract script calls using string matching when AST parsing fails."""
        import re
        
        script_calls = set()
        
        # Strip PMD wrappers
        content = self._strip_pmd_wrappers(script_content)
        if not content:
            return script_calls
        
        # Pattern to match script.function() calls
        # This regex looks for identifier.identifier( pattern
        pattern = r'\b([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        
        matches = re.findall(pattern, content)
        for script_name, function_name in matches:
            # Only consider it a script call if it's not a built-in or common object
            if not script_name.lower() in ['self', 'console']:
                script_calls.add(script_name)
        
        return script_calls

    def _extract_script_name_from_call(self, node: Any) -> str:
        """Extract script name from an arguments_expression node (e.g., util.function())."""
        try:
            if not hasattr(node, 'children') or len(node.children) < 1:
                return ""
            
            # The first child should be the function being called
            function_expr = node.children[0]
            
            # Check if it's a member expression (script.function)
            if hasattr(function_expr, 'data') and function_expr.data == 'member_dot_expression':
                if hasattr(function_expr, 'children') and len(function_expr.children) >= 2:
                    # The first child should be the script name (object)
                    script_node = function_expr.children[0]
                    if hasattr(script_node, 'data') and script_node.data == 'identifier_expression':
                        if hasattr(script_node, 'children') and script_node.children:
                            identifier = script_node.children[0]
                            if hasattr(identifier, 'value'):
                                return identifier.value
            
            return ""
        except Exception:
            return ""

    def _get_script_prefix(self, script_file: str) -> str:
        """Extract script prefix from script file name."""
        if not script_file:
            return ""
        
        # Remove .script extension if present
        if script_file.endswith('.script'):
            script_file = script_file[:-7]
        
        # Return the base name
        return script_file

    def _get_include_line_number(self, pmd_model: PMDModel, script_name: str) -> int:
        """Get line number for script include."""
        try:
            if hasattr(pmd_model, 'source_content') and pmd_model.source_content:
                lines = pmd_model.source_content.split('\n')
                for i, line in enumerate(lines):
                    # Look for the include array and the specific script
                    if f'"{script_name}.script"' in line or f'"{script_name}"' in line:
                        if '"include"' in line or (i > 0 and '"include"' in lines[i-1]):
                            return i + 1  # Convert to 1-based line numbering
        except Exception:
            pass
        
        return 1  # Fallback
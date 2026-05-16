"""Script unused script includes rule using unified architecture."""

from typing import Generator, Set, Any
from ...script.shared import ScriptRuleBase
from ...base import Finding, FixStrategy
from ....models import PMDModel
from .unused_script_includes_detector import ScriptUnusedIncludesRuleDetector


class ScriptUnusedIncludesRule(ScriptRuleBase):
    """Validates that included script files are actually used in PMD files."""

    DESCRIPTION = "Ensures included script files are actually used (via script.function() calls)"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.ACTIONABLE
    DETECTOR = ScriptUnusedIncludesRuleDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Including unused script files forces the engine to parse and load code that's never executed, directly impacting page load time. Each unnecessary include adds to your application's bundle size and slows down the initial page render. Removing unused includes makes pages load faster and removes potential developer confusion as to why the script is being included in the first place.''',
        'catches': [
            'Script files in PMD include arrays that are never called',
            'Dead script dependencies that increase bundle size'
        ],
        'examples': '''**Example violations:**

```javascript
// In sample.pmd
{
  "include": ["util.script", "helper.script"], // ❌ helper.script never called
  "onLoad": "<%
    pageVariables.winningNumbers = util.getFutureWinningLottoNumbers(); // Only util.script is used
  %>"
}
```

**Fix:**

```javascript
// In sample.pmd
{
  "include": ["util.script"], // ✅ Only include scripts that are actually used
  "onLoad": "<%
    pageVariables.winningNumbers = util.getFutureWinningLottoNumbers();
  %>"
}
```''',
        'recommendation': 'Remove unused script includes from PMD files. Only include script files that are actually called via `script.function()` patterns. This improves page load time and reduces bundle size.'
    }

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
                script_name = violation.metadata.get('script_name', '')
                # Source-side element form; we don't know whether the user wrote
                # "<name>.script" or bare "<name>" — _resolve_include_target_text
                # picks the literal form that appears in the file so the agent's
                # array_remove search is unambiguous.
                target_text = self._resolve_include_target_text(pmd_model, script_name)
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=self._get_include_line_number(pmd_model, script_name),
                    file_path=pmd_model.file_path,
                    # array_remove: agent locates `target_text` in the array at
                    # `path` and removes that element (dropping its surrounding
                    # comma). Other entries are preserved.
                    suggested_replacement="",
                    path="$.include",
                    target_text=target_text,
                    replacement_context="array_remove" if target_text else None,
                )
                
        except Exception as e:
            from utils.console import warn
            warn(f"Failed to analyze script includes in {pmd_model.file_path}: {e}")

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
                        # Find script calls (script.function() pattern) using AST
                        # AST parsing automatically ignores comments
                        for node in ast.find_data('arguments_expression'):
                            script_name = self._extract_script_name_from_call(node)
                            if script_name:
                                script_calls.add(script_name)
                        
                        # Don't use fallback when AST parsing succeeds
                        # AST is authoritative - if it finds no calls, there are no calls
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

    def _resolve_include_target_text(self, pmd_model: PMDModel, script_name: str) -> str:
        """Return the include element as it literally appears in source.

        ``script_name`` is the prefix form (e.g. ``util``). The user may have
        written ``"util.script"`` or just ``"util"`` in the include array; we
        check both quoted forms against the source content so the substring
        the agent removes matches the file exactly.
        """
        if not script_name or not getattr(pmd_model, 'source_content', None):
            return ""
        candidates = (f'"{script_name}.script"', f'"{script_name}"')
        for candidate in candidates:
            if candidate in pmd_model.source_content:
                return candidate
        return ""

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
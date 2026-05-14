"""Script unused variables rule using unified architecture."""

from typing import Generator, Set
from ...script.shared import ScriptRuleBase
from ...base import Finding, FixStrategy
from ....models import PMDModel, PodModel
from .unused_variables_detector import UnusedVariableDetector


class ScriptUnusedVariableRule(ScriptRuleBase):
    """Validates that all declared variables are used with proper scoping."""

    DESCRIPTION = "Ensures all declared variables are used (prevents dead code) with proper scoping awareness"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.LOCALIZED
    DETECTOR = UnusedVariableDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Unused variables clutter code and create confusion - developers waste time wondering if the variable is actually used somewhere they can't see. They also suggest incomplete refactoring or abandoned features. Removing unused variables improves code clarity and reduces the mental load of understanding what's actually active in your application.''',
        'catches': [
            'Variables declared but never used',
            'Dead code that increases bundle size'
        ],
        'examples': '''**Example violations:**

```javascript
function processData() {
    const unusedVar = "never used"; // ❌ Unused variable
    const result = calculateResult();
    return result;
}
```

**Fix:**

```javascript
function processData() {
    const result = calculateResult();
    return result;
}
```''',
        'recommendation': 'Remove unused variables to improve code clarity and reduce bundle size. Unused variables suggest incomplete refactoring or abandoned features.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None, path=None) -> Generator[Finding, None, None]:
        """Check script content using the detector with scope awareness."""
        # Parse the script content
        ast = self._parse_script_content(script_content, context)
        if not ast:
            yield from []
            return
        
        # Determine scope information
        # Template expressions and script fields (onSend, onLoad, etc.) should be analyzed as global scope
        is_global_scope = (field_name == 'script' or 
                          (ast and hasattr(ast, 'data') and ast.data == 'template_expression') or
                          'onSend' in field_name or 'onLoad' in field_name or 'onChange' in field_name)
        global_functions = self._get_global_functions_for_file(file_path)
        
        # Use detector to find violations
        detector = self.DETECTOR(file_path, line_offset, is_global_scope, global_functions)
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        from utils.jsonpath import dotted_to_jsonpath
        jsonpath = dotted_to_jsonpath(path)
        for violation in violations:
            yield Finding(
                rule=self,
                message=violation.message,
                line=violation.line,
                file_path=file_path,
                path=jsonpath,
            )

    def _get_global_functions_for_file(self, file_path: str) -> Set[str]:
        """Get global functions available for the given file."""
        # For now, return empty set - the complex global function logic can be added later
        # This maintains the basic functionality while using the unified architecture
        return set()
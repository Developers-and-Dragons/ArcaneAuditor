"""Script dead code rule using unified architecture."""

from typing import Generator, Dict, Any
from ...base import Finding, FixStrategy
from ...script.shared import ScriptRuleBase
from .script_dead_code_detector import ScriptDeadCodeDetector


class ScriptDeadCodeRule(ScriptRuleBase):
    """Detects dead code in standalone script files (.script)."""

    DESCRIPTION = "Detects and removes dead code from standalone script files"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.LOCALIZED
    DETECTOR = ScriptDeadCodeDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Dead code in standalone script files increases your application's bundle size and memory footprint, making pages load slower. Every unused function or constant is still parsed and loaded, wasting resources. Removing dead code keeps your application lean and makes it easier for other developers to understand what's actually being used.

This rule validates the export pattern specific to standalone `.script` files. Standalone script files use an export object literal at the end to expose functions and constants. This rule checks that ALL declared top-level variables (functions, strings, numbers, objects, etc.) are either:

1. Exported in the final object literal, OR
2. Used internally by other code in the file

**Intent:** Ensure standalone script files follow proper export patterns and don't contain unused declarations that increase bundle size.''',
        'catches': [
            'Top-level variables (of any type) declared but not exported AND not used internally',
            'Function-scoped variables that are declared but never used',
            'Dead code that increases bundle size unnecessarily'
        ],
        'examples': '''**Example violations:**

```javascript
// In util.script
const getCurrentTime = function() { return date:now(); };
const unusedHelper = function() { return "unused"; };    // ❌ Dead code - not exported or used
const apiUrl = "https://api.example.com";  // ❌ Dead code - constant not exported or used

{
  "getCurrentTime": getCurrentTime  // ❌ unusedHelper and API_KEY are dead code
}
```

**Fix:**

```javascript
// In util.script
const getCurrentTime = function() { return date:now(); };
const helperFunction = function() { return "helper"; };    // ✅ Will be exported
const apiUrl = "https://api.example.com";  // ✅ Will be exported

{
  "getCurrentTime": getCurrentTime,
  "helperFunction": helperFunction,
  "apiUrl": apiUrl  // ✅ All declarations are exported
}
```

**Example with internal usage:**

```javascript
// In util.script
const cacheTtl = 3600;  // ✅ Used internally (not exported)
const getCurrentTime = function() { 
  return { "time": date:now(), "ttl": cacheTtl };  // Uses cacheTtl
};

{
  "getCurrentTime": getCurrentTime  // ✅ cacheTtl is used internally
}
```''',
        'recommendation': 'Ensure all top-level variables in standalone script files are either exported in the final object literal or used internally by other code. Remove any unused declarations to reduce bundle size and improve code clarity.'
    }

    def __init__(self, config: Dict[str, Any] = None, context=None):
        """Initialize the rule."""
        self.config = config or {}

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def analyze(self, context):
        """Analyze standalone script files for dead code."""
        # This rule only analyzes standalone script files, not PMD/POD embedded scripts
        for script_model in context.scripts.values():
            yield from self._analyze_script_file(script_model, context)

    def _analyze_script_file(self, script_model, context):
        """Analyze a single script file for dead code."""
        try:
            ast = self._parse_script_content(script_model.source, context)
            if not ast:
                return
            
            # Create detector with configuration
            detector = self.DETECTOR(script_model.file_path, 1, self.config)
            
            # Use detector to find violations
            violations = detector.detect(ast, "script")
            
            # Convert violations to findings
            for violation in violations:
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=violation.line,
                    file_path=script_model.file_path
                )
                
        except Exception as e:
            from utils.console import warn
            warn(f"Failed to analyze script file {script_model.file_path}: {e}")
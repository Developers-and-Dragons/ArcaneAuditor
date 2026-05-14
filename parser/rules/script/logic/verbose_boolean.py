"""Script verbose boolean check rule using unified architecture."""

from ...base import FixStrategy
from ...script.shared import ScriptRuleBase
from .verbose_boolean_detector import VerboseBooleanDetector


class ScriptVerboseBooleanCheckRule(ScriptRuleBase):
    """Rule to check for overly verbose boolean checks."""

    DESCRIPTION = "Ensures scripts don't use overly verbose boolean checks (if(var == true) return true else return false)"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.MECHANICAL
    DETECTOR = VerboseBooleanDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Verbose boolean checks like `if (isActive == true)` or `return (condition) ? true : false` add unnecessary noise and make code harder to scan. The value is already boolean, so the comparison is redundant. Concise expressions (`if (isActive)` or `return condition`) are clearer, more idiomatic, and reduce visual clutter.''',
        'catches': [
            'Verbose boolean comparisons that can be simplified',
            'Redundant boolean expressions'
        ],
        'examples': '''**Example violations:**

```javascript
if (user.active == true) { }     // ❌ Verbose
if (user.active != false) { }    // ❌ Verbose
return (condition) ? true : false; // ❌ Redundant
```

**Fix:**

```javascript
if (user.active) { }              // ✅ Concise
if (!user.active) { }             // ✅ Concise
return condition;                 // ✅ Direct return
```''',
        'recommendation': 'Use concise boolean expressions instead of verbose comparisons. Direct boolean values and conditions are clearer and more idiomatic.'
    }

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

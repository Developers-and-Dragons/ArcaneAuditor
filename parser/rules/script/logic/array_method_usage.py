"""Script array method usage rule using unified architecture."""

from ...base import FixStrategy
from ...script.shared import ScriptRuleBase
from .array_method_usage_detector import ArrayMethodUsageDetector


class ScriptArrayMethodUsageRule(ScriptRuleBase):
    """Rule to detect manual loops that could be replaced with array higher-order methods."""

    DESCRIPTION = "Detects manual loops that could be replaced with array higher-order methods like map, filter, forEach"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.LOCALIZED
    DETECTOR = ArrayMethodUsageDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Array methods like map, filter, and forEach are more concise, less error-prone (no off-by-one errors), and communicate intent better than manual for-loops. They're also harder to get wrong since you don't manage the loop index yourself. Modern array methods make code more readable and reduce bugs related to loop boundaries or index manipulation.''',
        'catches': [
            'Traditional for loops that could be replaced with array higher-order methods',
            'Code that\'s more verbose than necessary'
        ],
        'examples': '''**Example violations:**

```javascript
const results = [];
for (let i = 0; i < items.length; i++) {  // ❌ Manual loop
    if (items[i].active) {
        results.add(items[i].name);
    }
}
```

**Fix:**

```javascript
const results = items
    .filter(item => item.active)     // ✅ Array higher-order methods
    .map(item => item.name);
```''',
        'recommendation': 'Replace manual for-loops with array higher-order methods (map, filter, forEach) to improve code readability, reduce errors, and communicate intent more clearly.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def _check_manual_loops(self, script_content, field_name, file_path, line_offset=1, context=None):
        """Check for manual loops that could use array higher-order methods."""
        # Parse the script content using Lark grammar
        ast = self._parse_script_content(script_content, context)
        if not ast:
            # If parsing fails, skip this script (compiler should have caught syntax errors)
            return
        
        # Create detector
        detector = self.DETECTOR(file_path, line_offset)
        
        # Use detector to find violations
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        for violation in violations:
            yield self._create_finding_from_violation(violation, file_path)
"""Script variable usage rule using unified architecture."""

from ...base import FixStrategy
from ...script.shared import ScriptRuleBase
from .var_usage_detector import VarUsageDetector


class ScriptVarUsageRule(ScriptRuleBase):
    """Rule to check for use of 'var' instead of 'let' or 'const'."""

    DESCRIPTION = "Ensures scripts use 'let' or 'const' instead of 'var' (best practice)"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.MECHANICAL
    DETECTOR = VarUsageDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''The `var` keyword has function scope, which can cause unexpected behavior and bugs when the same name is reused in nested blocks. Using `let` (block scope) and `const` (immutable) makes your code more predictable and prevents accidental variable shadowing issues.

Using the `const` keyword is also a good way to communicate `intent` to your readers.''',
        'catches': [
            'Usage of `var` declarations instead of modern `let`/`const`',
            'Variable declarations that don\'t follow Extend best practices'
        ],
        'examples': '''**Example violations:**

```javascript
var myVariable = "value";  // ❌ Should use 'let' or 'const'
```

**Fix:**

```javascript
const myVariable = "value";  // ✅ Use 'const' for immutable values
let myVariable = "value";    // ✅ Use 'let' for mutable values
```''',
        'recommendation': 'Replace `var` declarations with `let` for mutable variables or `const` for immutable values. This ensures block scoping and prevents variable shadowing issues.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

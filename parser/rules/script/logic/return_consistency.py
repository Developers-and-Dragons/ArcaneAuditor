"""Script function return consistency rule using unified architecture."""

from ...base import FixStrategy
from ...script.shared import ScriptRuleBase
from .return_consistency_detector import ReturnConsistencyDetector


class ScriptFunctionReturnConsistencyRule(ScriptRuleBase):
    """Rule to check for consistent return patterns in script functions."""

    DESCRIPTION = "Functions should have consistent return patterns - either all code paths return a value or none do"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.DESIGN_DECISION
    DETECTOR = ReturnConsistencyDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Functions with inconsistent returns (some code paths return a value, others return nothing) cause subtle bugs where callers receive `null` unexpectedly. This leads to null reference errors downstream or incorrect conditional logic. Ensuring all code paths explicitly return (even if explicitly `null`) makes function behavior predictable and prevents runtime errors. This rule also recognizes valid guard clause patterns where early returns handle error conditions while the main logic continues.

**Note:** Nested functions are analyzed independently - each function's return consistency is evaluated separately. Guard clause patterns are recognized as valid - when `else` branches return early for error handling while `if` branches continue with main logic.''',
        'catches': [
            'Functions with missing return statements ("not all code paths return")',
            'Inconsistent return patterns within functions ("inconsistent return pattern")',
            'Unreachable code after return statements ("unreachable code")'
        ],
        'examples': '''**Example violations:**

```pmd
// Missing return statement
const processUser = function(user) {
    if (user.active) {
        return user.name;
    }
    // ❌ Missing return statement
};

// Inconsistent return pattern
const calculateDiscount = function(price) {
    if (price > 1000) {
        return price * 0.15;  // Returns value
    } else {
        console.log("Standard price");  // ❌ No return
    }
    return price * 0.05;  // Final return
};

// Unreachable code
const getValue = function(data) {
    if (empty data) {
        return null;
    }
    return data.value;
    console.log("This never executes");  // ❌ Unreachable
};
```

**Valid patterns:**

```pmd
// Guard clause pattern (✅ Valid)
const processData = function(data) {
    if (empty data) {
        return null;  // Early return for error
    }
  
    // Main logic continues
    const processed = data.map(item => item.value);
    return processed;  // Final return
};

// Consistent returns (✅ Valid)
const processUser = function(user) {
    if (user.active) {
        return user.name;
    }
    return null;  // ✅ Explicit return
};
```''',
        'recommendation': 'Ensure all code paths in functions explicitly return a value (or `null`). Use guard clauses for early error returns, but ensure the main logic path also returns. Remove unreachable code after return statements.'
    }
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
"""Script unused function parameters rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from ...base import Finding, FixStrategy
from .unused_parameters_detector import UnusedParametersDetector


class ScriptUnusedFunctionParametersRule(ScriptRuleBase):
    """Validates that function parameters are actually used in the function body."""

    DESCRIPTION = "Ensures function parameters are actually used in the function body"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.CASCADING_RENAME
    DETECTOR = UnusedParametersDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Unused parameters make function signatures misleading - callers think they need to pass values that are actually ignored. This wastes developer time figuring out what to pass and creates confusion about the function's actual requirements. Removing unused parameters clarifies the API and prevents wasted effort.''',
        'catches': [
            'Function parameters that are declared but never used',
            'Parameters that could be removed to simplify the function signature'
        ],
        'examples': '''**Example violations:**

```javascript
function processUser(user, preferences) { // ❌ preferences unused
    return user.name;
}
```

**Fix:**

```javascript
function processUser(user) { // ✅ Only used parameters
    return user.name;
}
```''',
        'recommendation': 'Remove unused parameters from function signatures. This clarifies the function\'s actual requirements and prevents confusion for callers.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
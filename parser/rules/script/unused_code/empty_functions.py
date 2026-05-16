"""Script empty function rule using unified architecture."""

from ...base import FixStrategy
from ...script.shared import ScriptRuleBase
from .empty_function_detector import EmptyFunctionDetector


class ScriptEmptyFunctionRule(ScriptRuleBase):
    """Rule to check for empty function bodies."""

    DESCRIPTION = "Ensures functions have actual implementation (not empty bodies)"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.HUMAN_REVIEW
    DETECTOR = EmptyFunctionDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Empty functions are usually placeholder code that was never implemented or handlers that were meant to do something but don't. They add confusion (developers wonder if they're intentional), increase code size unnecessarily (which have hard limits!), and can mask missing functionality. Either implement them or remove them to keep your codebase clean and intentional.''',
        'catches': [
            'Functions with empty bodies',
            'Placeholder functions that should be implemented or removed'
        ],
        'examples': '''**Example violations:**

```javascript
function processData(data) {
    // ❌ Empty function body
}

const handler = function() { }; // ❌ Empty function
```

**Fix:**

```javascript
function processData(data) {
    // ✅ Implement the function or remove it
    return data.map(item => item.value);
}

// ✅ Or remove if not needed
```''',
        'recommendation': 'Implement empty functions with actual logic or remove them entirely. Empty functions add confusion and unnecessary code size.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

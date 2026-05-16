"""Script console log rule using unified architecture."""

from ...base import FixStrategy
from ...script.shared import ScriptRuleBase
from .console_log_detector import ConsoleLogDetector


class ScriptConsoleLogRule(ScriptRuleBase):
    """Rule to check for console statements in scripts."""

    DESCRIPTION = "Ensures scripts don't contain console statements (production code)"
    SEVERITY = "ACTION"
    FIX_STRATEGY = FixStrategy.ACTIONABLE
    DETECTOR = ConsoleLogDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Console statements left in production code can expose sensitive data in production logs, which may be accessible to individuals who should not have access to that same data. They're debugging artifacts that should be removed before deployment. Accidentally shipping console logs can leak business logic, data structures, or user information.

**🧙 Wizard's Note:** If your code uses an app attribute flag to enable/disable logging based on environments, you may think you don't need this rule. However, my recommendation would be to keep the rule in place and use it as a reminder to quickly verify any logging in place and ensure that those statements are implemented using your attribute flags. If a log entry slips in that didn't use it, this means your code may unintentionally write to production logs, leading to the kind of PII leakage that the rule is intended to help avoid!''',
        'catches': [
            '`console log` statements that should be removed before production',
            'Debug statements left in production code'
        ],
        'examples': '''**Example violations:**

```javascript
function processData(data) {
    console.debug("Processing data:", data); // ❌ Debug statement
    return data.map(item => item.value);
}
```

**Fix:**

```javascript
function processData(data) {
    // Comment out or remove
    // console.debug("Processing data:", data);
    return data.map(item => item.value);
}
```''',
        'recommendation': 'Remove all console log statements from production code. If logging is needed, use app attribute flags to control logging based on environment, ensuring sensitive data is never exposed in production logs.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

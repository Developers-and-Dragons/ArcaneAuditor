"""Script string concatenation rule using unified architecture."""

from ...base import FixStrategy
from ...script.shared import ScriptRuleBase
from .string_concat_detector import StringConcatDetector


class ScriptStringConcatRule(ScriptRuleBase):
    """Rule to check for string concatenation using + operator."""

    DESCRIPTION = "Detects string concatenation with + operator - use PMD templates with backticks and {{ }} instead"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.MECHANICAL
    DETECTOR = StringConcatDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''String concatenation with `+` is verbose, error-prone (easy to forget spaces), and harder to read than template syntax. Workday Extend's template syntax (`{{variable}}`) is specifically designed for building strings with dynamic values, handles escaping automatically, and makes the intent clearer. Using the right tool prevents formatting bugs and improves readability.''',
        'catches': [
            'String concatenation using + operator',
            'Code that would be more readable with PMD template syntax'
        ],
        'examples': '''**Example violations:**

```javascript
const message = "Hello " + userName + ", welcome to " + appName; // ❌ String concatenation
```

**Fix:**

```javascript
const message = `Hello {{userName}}, welcome to {{appName}}`; // ✅ PMD template syntax
```''',
        'recommendation': 'Use PMD template syntax with backticks and `{{variable}}` instead of string concatenation. This makes code more readable, prevents formatting errors, and handles escaping automatically.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

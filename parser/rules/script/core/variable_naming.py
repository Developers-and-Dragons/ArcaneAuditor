"""Script variable naming rule using unified architecture."""

from ...base import FixStrategy
from ...script.shared import ScriptRuleBase
from .variable_naming_detector import VariableNamingDetector


class ScriptVariableNamingRule(ScriptRuleBase):
    """Rule to check for variable naming conventions."""

    DESCRIPTION = "Ensures variables follow lowerCamelCase naming convention"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.CASCADING_RENAME
    DETECTOR = VariableNamingDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Consistent naming conventions make code easier to read and reduce cognitive load when switching between files or team members' code. lowerCamelCase is the standard for variables. Consistency enables faster comprehension and fewer mistakes.''',
        'catches': [
            'Variables that don\'t follow lowerCamelCase naming (snake_case, PascalCase, etc.)',
            'Inconsistent naming conventions'
        ],
        'examples': '''**Example violations:**

```javascript
const user_name = "John";     // ❌ snake_case
const UserAge = 25;           // ❌ PascalCase
const user-email = "email";   // ❌ kebab-case
```

**Fix:**

```javascript
const userName = "John";      // ✅ lowerCamelCase
const userAge = 25;           // ✅ lowerCamelCase
const userEmail = "email";    // ✅ lowerCamelCase
```''',
        'recommendation': 'Use lowerCamelCase for all variable names to maintain consistency and improve code readability.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

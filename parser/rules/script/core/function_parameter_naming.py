"""Script function parameter naming rule using unified architecture."""

from ...base import FixStrategy
from ...script.shared import ScriptRuleBase
from .function_parameter_naming_detector import FunctionParameterNamingDetector


class ScriptFunctionParameterNamingRule(ScriptRuleBase):
    """Rule to check for function parameter naming conventions."""

    DESCRIPTION = "Ensures function parameters follow lowerCamelCase naming convention"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.CASCADING_RENAME
    DETECTOR = FunctionParameterNamingDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Parameter names are the first thing developers see when calling your functions. Inconsistent naming (like snake_case parameters when everything else uses lowerCamelCase) forces mental translation and slows comprehension. Following the same convention for parameters as variables creates a seamless reading experience and makes function signatures immediately understandable.''',
        'catches': [
            'Function parameters that don\'t follow lowerCamelCase naming convention',
            'Parameters using snake_case, PascalCase, or other naming conventions',
            'Inconsistent parameter naming that affects code readability'
        ],
        'examples': '''**Example violations:**

```javascript
// ❌ Non-lowerCamelCase parameters
const validateUser = function(user_id, user_name, is_active) {
    return user_id && user_name && is_active;
};

const processData = function(data_source) {
    return data_source.map(item => item.process());
};
```

**Fix:**

```javascript
// ✅ lowerCamelCase parameters
const validateUser = function(userId, userName, isActive) {
    return userId && userName && isActive;
};

const processData = function(dataSource) {
    return dataSource.map(item => item.process());
};
```''',
        'recommendation': 'Use lowerCamelCase for all function parameters to match variable naming conventions and improve code readability.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

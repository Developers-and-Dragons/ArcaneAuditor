"""Script descriptive parameter rule using unified architecture."""

from typing import Generator, Dict, List
from ...script.shared import ScriptRuleBase
from ...base import Finding, FixStrategy
from .descriptive_parameters_detector import DescriptiveParameterDetector


class ScriptDescriptiveParameterRule(ScriptRuleBase):
    """Validates that function parameters use descriptive names when functions take function parameters."""

    DESCRIPTION = "Ensures function parameters use descriptive names when functions take function parameters (except 'a', 'b' for sort)"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.HUMAN_REVIEW
    DETECTOR = DescriptiveParameterDetector
    AVAILABLE_SETTINGS = {
        'allowed_single_letters': {'type': 'list', 'default': [], 'description': 'Additional single-letter parameter names to allow beyond built-in exceptions'}
    }
    
    DOCUMENTATION = {
        'why': '''Single-letter parameters in array methods (`x => x.active`) hide information about what is being processed, making code harder to scan and understand at a glance. Descriptive names (`user => user.active`) self-document the code and prevent confusion in nested method chains where multiple single-letter variables could refer to different things.

**Special Cases:**
- **Sort methods:** `a`, `b` are allowed for comparison parameters
- **Reduce methods:** Suggests `acc` for accumulator, contextual names for items
- **Minimally context-aware:** Suggests `user` for `users.map()`, `team` for `teams.filter()`, etc.''',
        'catches': [
            'Single-letter parameters in array methods that make code hard to read',
            'Nested array methods with confusing parameter names',
            'Non-descriptive variable names in map, filter, find, forEach, reduce, sort'
        ],
        'examples': '''**Example violations:**

```javascript
// ❌ Confusing single-letter parameters
const activeUsers = users.filter(x => x.active);
const userNames = users.map(u => u.name);
```

**Fix:**

```javascript
// ✅ Descriptive parameter names
const activeUsers = users.filter(user => user.active);
const userNames = users.map(user => user.name);

// ✅ Clear chained array methods
const result = departments
    .map(dept => dept.teams)
    .filter(team => team.active);

// ✅ Descriptive reduce parameters
const total = numbers.reduce((acc, num) => {acc + num});
```''',
        'recommendation': 'Use descriptive parameter names in array methods instead of single letters. This makes code self-documenting and prevents confusion, especially in nested method chains.'
    }

    # Expose constants for testing
    FUNCTIONAL_METHODS = {'map', 'filter', 'find', 'forEach', 'reduce', 'sort'}
    ALLOWED_SINGLE_LETTERS = set()  # Empty set - only 'a','b' are allowed for sort (handled separately)

    def __init__(self, config=None):
        """Initialize the rule with optional configuration."""
        super().__init__()
        if config:
            # Update allowed single letters if provided
            if 'allowed_single_letters' in config:
                self.ALLOWED_SINGLE_LETTERS = set(config['allowed_single_letters'])

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None, path=None) -> Generator[Finding, None, None]:
        """Check script content using the detector with rule-specific configuration."""
        # Parse the script content with context for caching
        ast = self._parse_script_content(script_content, context)
        if not ast:
            yield from []
            return
        
        # Create detector with rule-specific configuration
        detector = self.DETECTOR(file_path, line_offset, self.FUNCTIONAL_METHODS, self.ALLOWED_SINGLE_LETTERS)
        detector.set_original_content(script_content)
        
        # Use detector to find violations
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        # Handle both List[Violation] and Generator[Violation, None, None]
        if hasattr(violations, '__iter__') and not isinstance(violations, str):
            from utils.jsonpath import dotted_to_jsonpath
            jsonpath = dotted_to_jsonpath(path)
            for violation in violations:
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=violation.line,
                    file_path=file_path,
                    path=jsonpath,
                )
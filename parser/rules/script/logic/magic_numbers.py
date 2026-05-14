"""Script magic number rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .magic_number_detector import MagicNumberDetector
from ...base import Finding, FixStrategy


class ScriptMagicNumberRule(ScriptRuleBase):
    """Rule to check for magic numbers."""

    DESCRIPTION = "Ensures scripts don't contain magic numbers (use named constants)"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.NAMING_REQUIRED
    DETECTOR = MagicNumberDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Magic numbers (like `if (price > 1000)` or `return value * 0.15`) hide meaning and make code harder to maintain. When the number appears in multiple places, updating it requires finding every occurrence, risking missed updates. Named constants (`const premiumThreshold = 1000`) make the purpose clear and provide a single source of truth for values that might need to change.''',
        'catches': [
            'Numeric literals without clear meaning',
            'Hard-coded numbers that should be constants'
        ],
        'examples': '''**Example violations:**

```javascript
function calculateDiscount(price) {
    if (price > 1000) {        // ❌ Magic number
        return price * 0.15;   // ❌ Magic number
    }
    return price * 0.05;       // ❌ Magic number
}
```

**Fix:**

```javascript
const premiumThreshold = 1000;
const premiumDiscount = 0.15;
const standardDiscount = 0.05;

function calculateDiscount(price) {
    if (price > premiumThreshold) {
        return price * premiumDiscount;
    }
    return price * standardDiscount;
}
```''',
        'recommendation': 'Replace magic numbers with named constants that clearly express their purpose. This makes code more maintainable and provides a single source of truth for values that might need to change.'
    }

    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None, path=None):
        """Override to pass source text to detector for code context extraction."""
        # Strip <% %> tags from script content if present
        clean_script_content = self._strip_script_tags(script_content)
        
        # Parse the script content with context for caching
        ast = self._parse_script_content(clean_script_content, context)
        if not ast:
            return
        
        # Use detector to find violations, passing source text for code context
        detector = self.DETECTOR(file_path, line_offset, clean_script_content)
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        if violations is not None and hasattr(violations, '__iter__') and not isinstance(violations, str):
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

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

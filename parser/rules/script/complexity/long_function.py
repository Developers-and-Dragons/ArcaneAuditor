"""Script long function rule using unified architecture."""

from ...script.shared import ScriptRuleBase
from .long_function_detector import LongFunctionDetector
from ...base import Finding


class ScriptLongFunctionRule(ScriptRuleBase):
    """Rule to check for functions that exceed maximum line count."""

    DESCRIPTION = "Ensures functions don't exceed maximum line count (max 50 lines)"
    SEVERITY = "ADVICE"
    DETECTOR = LongFunctionDetector
    AVAILABLE_SETTINGS = {
        'max_lines': {'type': 'int', 'default': 50, 'description': 'Maximum lines allowed'},
        'skip_comments': {'type': 'bool', 'default': False, 'description': 'Skip comment lines when counting'},
        'skip_blank_lines': {'type': 'bool', 'default': False, 'description': 'Skip blank lines when counting'}
    }
    
    DOCUMENTATION = {
        'why': '''Functions longer than 50 lines typically violate the single responsibility principle - they're doing too many things. Long functions are harder to understand, test, and reuse, and they often hide bugs in the complexity. Breaking them into smaller, focused functions with clear names makes code self-documenting and easier to maintain.''',
        'catches': [
            'Functions that exceed 50 lines of code',
            'Monolithic functions that should be broken down',
            'Functions that likely violate single responsibility principle',
            '**Note:** Nested functions are analyzed independently - but inner function lines are also included in outer function counts. This means you could get multiple violations when an inner function exceeds the threshold. This means the outer function does, too!'
        ],
        'examples': '''**Example violations:**

```pmd
const processLargeDataset = function(data) {
    // ... 60 lines of code ...
    // This function is doing too many things
};
```

**Fix:**

```pmd
const processLargeDataset = function(data) {
    const validated = validateData(data);
    const processed = transformData(validated);
    return formatOutput(processed);
};

const validateData = function(data) {
    // ... validation logic ...
};

const transformData = function(data) {
    // ... transformation logic ...
};

const formatOutput = function(data) {
    // ... formatting logic ...
};
```''',
        'recommendation': 'Break long functions into smaller, focused functions with clear names. Each function should have a single responsibility, making the code easier to understand, test, and maintain.'
    }

    def __init__(self):
        super().__init__()
        self.max_lines = 50
        self.skip_comments = False  # Default to ESLint behavior
        self.skip_blank_lines = False  # Default to ESLint behavior

    def apply_settings(self, custom_settings: dict):
        """Apply custom settings from configuration."""
        if 'max_lines' in custom_settings:
            self.max_lines = custom_settings['max_lines']
        if 'skip_comments' in custom_settings:
            self.skip_comments = custom_settings['skip_comments']
        if 'skip_blank_lines' in custom_settings:
            self.skip_blank_lines = custom_settings['skip_blank_lines']

    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None, path=None):
        """Override to pass custom settings to detector."""
        # Only analyze functions in the 'script' section
        if field_name and field_name != 'script':
            return
        
        # Strip <% %> tags from script content if present
        clean_script_content = self._strip_script_tags(script_content)
        
        # Parse the script content with context for caching
        ast = self._parse_script_content(clean_script_content, context)
        if not ast:
            return
        
        # Use detector to find violations, passing custom settings AND stripped content
        detector = self.DETECTOR(file_path, line_offset, self.skip_comments, self.skip_blank_lines, clean_script_content)
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

#!/usr/bin/env python3
"""Long script block rule for PMD/POD files."""

from ...script.shared import ScriptRuleBase
from ...base import Finding
from .long_script_block_detector import LongScriptBlockDetector


class ScriptLongBlockRule(ScriptRuleBase):
    """Rule to check for script blocks that exceed maximum line count."""

    ID = "ScriptLongBlockRule"
    DESCRIPTION = "Ensures non-function script blocks in PMD/POD files don't exceed maximum line count (max 30 lines). Excludes function definitions which are handled by ScriptLongFunctionRule."
    SEVERITY = "ADVICE"
    DETECTOR = LongScriptBlockDetector
    AVAILABLE_SETTINGS = {
        'max_lines': {'type': 'int', 'default': 30, 'description': 'Maximum lines allowed per script block'},
        'skip_comments': {'type': 'bool', 'default': False, 'description': 'Skip comment lines when counting'},
        'skip_blank_lines': {'type': 'bool', 'default': False, 'description': 'Skip blank lines when counting'}
    }
    
    DOCUMENTATION = {
        'why': '''Embedded script blocks (in event handlers like onLoad, onChange, onSend, or widget properties) should be kept small and focused. When these blocks grow beyond 30 lines, they become difficult to read, test, and maintain. Long embedded blocks often contain complex logic that should be extracted into reusable functions in the `script` section (or `.script` files in the case of functionality that could be shared across pages).

This rule enforces the principle that embedded blocks should contain only simple, focused logic while complex operations belong in dedicated functions.''',
        'catches': [
            'Script blocks in PMD/POD embedded fields (onLoad, onChange, onSend, widget properties, etc.) that exceed 30 lines',
            'Embedded blocks containing inline functions, callbacks, and procedural code that should be refactored',
            'Script blocks that violate single responsibility principle by doing too much in one place',
            '**Note:** The `script` field in PMD files and standalone `.script` files are excluded entirely as they\'re handled by ScriptLongFunctionRule'
        ],
        'examples': '''**Example violations:**

```pmd
// In onLoad field
<%
    const workerData = getWorkerData();
    const processedData = processWorkerData(workerData);
    const validationResults = validateWorkerData(processedData);
    const formattedData = formatWorkerData(validationResults);
    const enrichedData = enrichWorkerData(formattedData);
    const finalData = applyBusinessRules(enrichedData);
    const displayData = prepareDisplayData(finalData);
    const summaryData = generateSummary(displayData);
    const reportData = createReport(summaryData);
    const exportData = prepareExport(reportData);
    const notificationData = prepareNotifications(exportData);
    const auditData = createAuditTrail(notificationData);
    const cacheData = prepareCache(auditData);
    const responseData = formatResponse(cacheData);
    // ... 20+ more lines of data processing ...
    pageVariables.workerData = responseData;
%>
```

**Fix:**

```pmd
// Break into focused functions
<%
    const workerData = getWorkerData();
    const processedData = processWorkerData(workerData);
    pageVariables.workerData = processedData;
%>

// Define functions in script section
const processWorkerData = function(rawData) {
    const validated = validateWorkerData(rawData);
    const formatted = formatWorkerData(validated);
    const enriched = enrichWorkerData(formatted);
    return enriched;
};

const validateWorkerData = function(data) {
    // ... focused validation logic
    return data;
};

const formatWorkerData = function(data) {
    // ... focused formatting logic
    return data;
};
```''',
        'recommendation': 'Extract complex logic from embedded script blocks into focused functions in the `script` section or `.script` files. Keep embedded blocks small and focused, containing only simple, direct logic.'
    }

    def __init__(self):
        super().__init__()
        self.max_lines = 30
        self.skip_comments = False  # Default to ESLint behavior
        self.skip_blank_lines = False  # Default to ESLint behavior

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def apply_settings(self, custom_settings: dict):
        """Apply custom settings from configuration."""
        if 'max_lines' in custom_settings:
            self.max_lines = custom_settings['max_lines']
        if 'skip_comments' in custom_settings:
            self.skip_comments = custom_settings['skip_comments']
        if 'skip_blank_lines' in custom_settings:
            self.skip_blank_lines = custom_settings['skip_blank_lines']
    
    def _analyze_script(self, script_model, context=None):
        """Override to skip standalone script files entirely.
        
        ScriptLongBlockRule only applies to embedded script blocks in PMD/POD files,
        not to standalone .script files which are handled by ScriptLongFunctionRule.
        """
        # Skip standalone script files entirely - they should only be analyzed
        # by ScriptLongFunctionRule, not ScriptLongBlockRule
        yield from []
    
    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None, path=None):
        """Override to pass custom settings to detector."""
        # Strip <% %> tags from script content if present
        clean_script_content = self._strip_script_tags(script_content)
        
        # Parse the script content with context for caching
        ast = self._parse_script_content(clean_script_content, context)
        if not ast:
            yield from []
            return
        
        # Use detector to find violations, passing custom settings AND stripped content
        detector = self.DETECTOR(file_path, line_offset, self.max_lines, self.skip_comments, self.skip_blank_lines, clean_script_content)
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        if violations is not None and hasattr(violations, '__iter__') and not isinstance(violations, str):
            from utils.jsonpath import dotted_to_jsonpath
            jsonpath = dotted_to_jsonpath(path)
            for violation in violations:
                if violation is not None:
                    yield Finding(
                        rule=self,
                        message=violation.message,
                        line=violation.line,
                        file_path=file_path,
                        path=jsonpath,
                    )

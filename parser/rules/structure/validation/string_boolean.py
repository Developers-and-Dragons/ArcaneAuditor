from typing import Generator
from ...base import Finding, FixStrategy
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class StringBooleanRule(StructureRuleBase):
    """Ensures boolean values are not represented as strings 'true'/'false' but as actual booleans."""

    DESCRIPTION = "Ensures boolean values are not represented as strings 'true'/'false' but as actual booleans"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.ACTIONABLE
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Booleans should be represented as actual boolean values (true / false), not strings ("true" / "false"). While the backend may gracefully cast string values, this "magic conversion" hides the true intent of the data.

**🧙 Wizard's Note:** Some areas of Extend actually *require* you to use strings, instead of bools (for example: for some values in your AMD flows), so we won't check in those places and just accept this "gotcha" with Extend.''',
        'catches': [
            'Boolean values represented as strings `"true"` or `"false"`'
        ],
        'examples': '''**Example violations:**

```json
{
  "visible": "true",  // ❌ String instead of boolean
  "enabled": "false"  // ❌ String instead of boolean
}
```

**Fix:**

```json
{
  "visible": true,  // ✅ Actual boolean
  "enabled": false  // ✅ Actual boolean
}
```''',
        'recommendation': 'Use actual boolean values (true/false) instead of strings ("true"/"false") to clearly express intent and avoid relying on implicit type conversion.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyzes the PMD model for string boolean values."""
        if not pmd_model.source_content:
            return
        
        # Check the raw source content for string boolean patterns
        yield from self._check_source_content_for_string_booleans(pmd_model)

    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyzes the POD model for string boolean values."""
        if not pod_model.source_content:
            return
        
        # Check the raw source content for string boolean patterns
        yield from self._check_source_content_for_string_booleans(pod_model)

    def _check_source_content_for_string_booleans(self, model):
        """Check the source content for string boolean patterns."""
        import re
        
        lines = model.source_content.split('\n')
        
        # Pattern to match field: "true" or field: "false" or field:"true" or field:"false"
        pattern = r'"([^"]+)"\s*:\s*"(true|false)"'
        
        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line)
            for match in matches:
                field_name = match.group(1)
                string_value = match.group(2)
                
                # Skip fields that start with underscore (commented out)
                if field_name.startswith('_'):
                    continue
                
                yield self._create_finding(
                    message=f"Field '{field_name}' has string value '{string_value}' instead of boolean {string_value}. Use boolean {string_value} instead of string '{string_value}'.",
                    file_path=model.file_path,
                    line=line_num,
                    suggested_replacement=string_value,
                )

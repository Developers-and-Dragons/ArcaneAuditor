"""
Rule to detect hardcoded WID (Workday ID) values in PMD, POD, and WQL query files.

WIDs should be configured in app attributes and not hardcoded in the app source.
There are two exceptions that are allowed in the code:
- Business process WIDs: "d9e41a8c446c11de98360015c5e6daf6" and "d9e4223e446c11de98360015c5e6daf6"

A WID can be identified as a 32 character long string that is alphanumeric.
"""
import re
from typing import Generator, Any
from ...base import Finding, FixStrategy
from ....models import PMDModel, PodModel, ProjectContext, WQLQueryModel
from ..shared import StructureRuleBase


class HardcodedWidRule(StructureRuleBase):
    """
    Detects hardcoded WID (Workday ID) values that should be configured in app attributes.

    This rule checks PMD, POD, and WQL query files for:
    - 32-character alphanumeric strings that look like WIDs
    - Excludes allowed business process WIDs
    - Recommends using app attributes instead of hardcoded values
    """
    
    ID = "HardcodedWidRule"
    DESCRIPTION = "Detects hardcoded WID values that should be configured in app attributes"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.MECHANICAL
    AVAILABLE_SETTINGS = {
        'allow_wid_in_task_report_link_fields': {
            'type': 'bool',
            'default': False,
            'description': 'Allow WIDs in task/report link wid field values (Workday feature). When enabled, no finding is reported for hardcoded WIDs in field names "wid".'
        }
    }

    def __init__(self):
        super().__init__()
        self.allow_wid_in_task_report_link_fields = False

    def apply_settings(self, custom_settings: dict) -> None:
        """Apply custom settings from configuration."""
        if 'allow_wid_in_task_report_link_fields' in custom_settings:
            self.allow_wid_in_task_report_link_fields = bool(custom_settings['allow_wid_in_task_report_link_fields'])
    
    DOCUMENTATION = {
        'why': '''Hardcoded WIDs (Workday IDs) are often environment-specific - a worker or job WID from your WCPDev tenant won't exist in Production. This causes runtime errors when the code tries to look up non-existent data. But even if you're using a common WID that exists across environments, it is meaningless to a developer looking at your code (possibly including yourself!). Storing WIDs in app attributes allows different values per environment, makes your application portable across tenants and instances, and allows for you to name it in a way that makes sense!''',
        'catches': [
            'Hardcoded 32-character WID values',
            'WIDs that should be configured in app attributes'
        ],
        'allows': [
            'Business process WID "d9e41a8c446c11de98360015c5e6daf6" (allowed exception)',
            'Business process WID "d9e4223e446c11de98360015c5e6daf6" (allowed exception)',
            'WIDs in task/report link "wid" field when allow_wid_in_task_report_link_fields is enabled (Workday feature)'
        ],
        'examples': '''**Example violations:**

```javascript
const query = "SELECT worker FROM allIndexedWorkers WHERE country = 'd9e41a8c446c11de98360015c5e6daf6'"; // ❌ Hardcoded WID
```

**Fix:**

```javascript
const usaLocation = appAttr.usaLocation; // ✅ Use app attribute
const query = "SELECT worker FROM allIndexedWorkers WHERE country = usaLocation"
```''',
        'recommendation': 'Store WID values in app attributes instead of hardcoding them. This makes your application portable across environments and allows meaningful naming that helps developers understand the code.',
        'configuration': 'allow_wid_in_task_report_link_fields (boolean, default false): When true, hardcoded WIDs in the "wid" field (task/report link values) are not reported. Use this if your app uses Workday\'s task/report link feature where wid is required in those fields.'
    }
    
    # Allowed business process WIDs that are exceptions
    ALLOWED_WIDS = {
        "d9e41a8c446c11de98360015c5e6daf6",  # Business process WID
        "d9e4223e446c11de98360015c5e6daf6"   # Business process WID
    }
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for hardcoded WIDs."""
        yield from self._check_pmd_hardcoded_wids(pmd_model, context)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for hardcoded WIDs."""
        yield from self._check_pod_hardcoded_wids(pod_model)

    def visit_wqlquery(self, wql_model: WQLQueryModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze WQL query model for hardcoded WIDs."""
        yield from self._check_wqlquery_hardcoded_wids(wql_model, context)

    def _check_wqlquery_hardcoded_wids(self, wql_model: WQLQueryModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Check WQL query file for hardcoded WID values."""
        wql_dict = wql_model.model_dump(exclude={'file_path', 'source_content'})
        yield from self._check_string_values_for_wids(
            wql_dict, wql_model.file_path, pmd_model=None, pod_model=None, wql_model=wql_model, context=context
        )

    def _check_pmd_hardcoded_wids(self, pmd_model: PMDModel, context: ProjectContext = None) -> Generator[Finding, None, None]:
        """Check PMD file for hardcoded WID values."""
        # Convert PMD model to dictionary for recursive checking
        pmd_dict = pmd_model.model_dump(exclude={'file_path', 'source_content'})
        yield from self._check_string_values_for_wids(pmd_dict, pmd_model.file_path, pmd_model=pmd_model, context=context)
    
    def _check_pod_hardcoded_wids(self, pod_model: PodModel) -> Generator[Finding, None, None]:
        """Check POD file for hardcoded WID values."""
        # Convert POD model to dictionary for recursive checking
        pod_dict = pod_model.model_dump(exclude={'file_path', 'source_content'})
        yield from self._check_string_values_for_wids(pod_dict, pod_model.file_path, pod_model=pod_model)
    
    def _check_string_values_for_wids(self, model: Any, file_path: str, pmd_model: PMDModel = None, pod_model: PodModel = None, wql_model: WQLQueryModel = None, path: str = "", context: ProjectContext = None) -> Generator[Finding, None, None]:
        """Recursively check string values for hardcoded WIDs."""
        if isinstance(model, dict):
            # Track widget ID for better context
            widget_id = model.get('id') or model.get('widgetId')
            widget_type = model.get('type')
            
            for key, value in model.items():
                if isinstance(value, str):
                    # Skip task/report link wid field when config allows it
                    if key == 'wid' and getattr(self, 'allow_wid_in_task_report_link_fields', False):
                        continue
                    # Build descriptive path
                    context_path = path
                    if widget_id and widget_type:
                        context_path = f"{widget_type} widget '{widget_id}' > {key}"
                    elif widget_id:
                        context_path = f"widget '{widget_id}' > {key}"
                    elif key and not path:
                        context_path = key
                    else:
                        context_path = f"{path}.{key}" if path else key
                    
                    yield from self._check_string_for_wids(value, file_path, context_path, pmd_model, pod_model, wql_model, context)
                elif isinstance(value, (dict, list)):
                    new_path = f"{path}.{key}" if path else key
                    yield from self._check_string_values_for_wids(value, file_path, pmd_model, pod_model, wql_model, new_path, context)
        elif isinstance(model, list):
            for i, item in enumerate(model):
                if isinstance(item, str):
                    yield from self._check_string_for_wids(item, file_path, f"{path}[{i}]", pmd_model, pod_model, wql_model, context)
                elif isinstance(item, (dict, list)):
                    yield from self._check_string_values_for_wids(item, file_path, pmd_model, pod_model, wql_model, f"{path}[{i}]", context)

    def _check_string_for_wids(self, text: str, file_path: str, field_name: str, pmd_model: PMDModel = None, pod_model: PodModel = None, wql_model: WQLQueryModel = None, context: ProjectContext = None) -> Generator[Finding, None, None]:
        """Check a single string for hardcoded WID values."""
        if not text:
            return
        
        # Check if this is a script field (contains <% %>)
        if '<%' in text and '%>' in text:
            # Use AST-based detection for script fields (respects comments)
            yield from self._check_script_for_wids_ast(text, file_path, field_name, pmd_model, pod_model, wql_model, context)
        else:
            # Use regex for plain JSON values (no comments possible)
            yield from self._check_string_for_wids_regex(text, file_path, field_name, pmd_model, pod_model, wql_model)

    def _check_string_for_wids_regex(self, text: str, file_path: str, field_name: str, pmd_model: PMDModel = None, pod_model: PodModel = None, wql_model: WQLQueryModel = None) -> Generator[Finding, None, None]:
        """Check a plain string (non-script) for hardcoded WID values using regex."""
        # Pattern to match 32-character alphanumeric strings (WIDs)
        # This will match strings that are exactly 32 characters long and contain only a-f and 0-9
        wid_pattern = r'\b[a-f0-9]{32}\b'
        
        matches = re.finditer(wid_pattern, text, re.IGNORECASE)
        for match in matches:
            wid_value = match.group().lower()
            
            # Skip if this is an allowed business process WID
            if wid_value in self.ALLOWED_WIDS:
                continue
            
            # Calculate line number by searching in source content
            line_num = self._find_wid_line_number(wid_value, pmd_model, pod_model, wql_model)

            yield self._create_finding(
                message=f"Hardcoded WID '{wid_value}' in {field_name}. Use app attributes instead.",
                file_path=file_path,
                line=line_num
            )

    def _check_script_for_wids_ast(self, script_content: str, file_path: str, field_name: str, pmd_model: PMDModel = None, pod_model: PodModel = None, wql_model: WQLQueryModel = None, context: ProjectContext = None) -> Generator[Finding, None, None]:
        """Check a script field for hardcoded WID values using AST (ignores comments)."""
        # Parse with AST using cached parsing (leverage context-level cache)
        ast = self._parse_script_content(script_content, context)
        if not ast:
            # If parsing fails, fall back to regex (but this means comments won't be filtered)
            yield from self._check_string_for_wids_regex(script_content, file_path, field_name, pmd_model, pod_model, wql_model)
            return
        
        # Extract all string literals from AST with context
        wid_pattern = r'^[a-f0-9]{32}$'  # Exact match for literals
        
        for variable_decl in ast.find_data('variable_declaration'):
            # Extract variable name and check its value
            var_name = None
            for child in variable_decl.children:
                if hasattr(child, 'type') and child.type == 'IDENTIFIER':
                    var_name = child.value
                    break
            
            # Check string literals in this variable declaration
            for literal_expr in variable_decl.find_data('literal_expression'):
                if hasattr(literal_expr, 'children') and len(literal_expr.children) > 0:
                    token = literal_expr.children[0]
                    if hasattr(token, 'value'):
                        literal_value = token.value.strip('\'"')
                        
                        if re.match(wid_pattern, literal_value):
                            wid_value = literal_value.lower()
                            
                            if wid_value in self.ALLOWED_WIDS:
                                continue

                            line_num = self._find_wid_line_number(wid_value, pmd_model, pod_model, wql_model)
                            context_desc = f"in variable '{var_name}' in {field_name}" if var_name else f"in {field_name}"
                            
                            yield self._create_finding(
                                message=f"Hardcoded WID '{wid_value}' {context_desc}. Use app attributes instead.",
                                file_path=file_path,
                                line=line_num
                            )
    
    def _find_wid_line_number(self, wid_value: str, pmd_model: PMDModel = None, pod_model: PodModel = None, wql_model: WQLQueryModel = None) -> int:
        """Find the line number where a WID value appears in the source content."""
        if pmd_model:
            return self.find_pattern_line_number(pmd_model, wid_value, case_sensitive=False)
        if pod_model:
            return self.find_pattern_line_number(pod_model, wid_value, case_sensitive=False)
        if wql_model:
            return self.find_pattern_line_number(wql_model, wid_value, case_sensitive=False)
        return 1

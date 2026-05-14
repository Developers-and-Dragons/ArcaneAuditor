from typing import Generator, List
from ...base import Finding, FixStrategy, Category
from ...common_validations import validate_lower_camel_case
from ...common import PMDLineUtils
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class WidgetIdLowerCamelCaseRule(StructureRuleBase):
    """Validates that widget IDs follow lowerCamelCase convention (style guide)."""

    ID = "WidgetIdLowerCamelCaseRule"
    DESCRIPTION = "Ensures widget IDs follow lowerCamelCase naming convention (style guide for PMD and POD files)"
    SEVERITY = "ADVICE"
    CATEGORY = Category.WIDGET
    FIX_STRATEGY = FixStrategy.CASCADING_RENAME
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''LowerCamelCase is the Workday standard, and following it means your code will be consisten across pages AND applications. Mixing conventions (snake_case, PascalCase) forces constant reference checking and slows development.''',
        'catches': [
            'Widget IDs that don\'t follow lowerCamelCase convention',
            'Style guide violations'
        ],
        'examples': '''**Example violations:**

```json
{
  "type": "richText",
  "id": "WelcomeMessage"  // ❌ Should be lowerCamelCase
}
```

**Fix:**

```json
{
  "type": "richText",
  "id": "welcomeMessage"  // ✅ Proper lowerCamelCase
}
```''',
        'recommendation': 'Use lowerCamelCase for all widget IDs to follow Workday standards and ensure consistency across pages and applications.'
    }
    
    # Widget types that do not require or support ID values
    WIDGET_TYPES_WITHOUT_ID_REQUIREMENT = {
        'footer', 'item', 'group', 'title'
    }
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for widget ID naming conventions."""
        if not pmd_model.presentation:
            return
        
        # Use generic traversal to handle different layout types
        presentation_dict = pmd_model.presentation.__dict__
        
        # Traverse all presentation sections (body, title, footer, etc.)
        for section_name, section_data in presentation_dict.items():
            if isinstance(section_data, dict):
                # Use generic traversal for each section
                for widget, path, index, parent_type, container_name in self.traverse_presentation_structure(section_data, section_name):
                    if isinstance(widget, dict) and 'id' in widget:
                        # Skip widget types that are excluded from ID requirements
                        widget_type = widget.get('type', 'unknown')
                        if widget_type not in self.WIDGET_TYPES_WITHOUT_ID_REQUIREMENT:
                            yield from self._check_widget_id_naming(widget, pmd_model, section_name, path, index)
            elif isinstance(section_data, list):
                # Handle tabs list (tabs is a list of section widgets)
                for i, tab_item in enumerate(section_data):
                    if isinstance(tab_item, dict):
                        tab_path = f"{section_name}.{i}"
                        for widget, path, index, parent_type, container_name in self.traverse_presentation_structure(tab_item, tab_path):
                            if isinstance(widget, dict) and 'id' in widget:
                                # Skip widget types that are excluded from ID requirements
                                widget_type = widget.get('type', 'unknown')
                                if widget_type not in self.WIDGET_TYPES_WITHOUT_ID_REQUIREMENT:
                                    yield from self._check_widget_id_naming(widget, pmd_model, section_name, path, index)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for widget ID naming conventions."""
        # Use the base rule utility to find all widgets in the POD script
        widgets = self.find_pod_widgets(pod_model)
        
        for widget_path, widget_data in widgets:
            if isinstance(widget_data, dict) and 'id' in widget_data:
                yield from self._check_widget_id_naming(widget_data, None, 'script', widget_path, 0, pod_model)
    
    def _check_widget_id_naming(self, widget, pmd_model=None, section='body', widget_path="", widget_index=0, pod_model=None):
        """Check if a widget ID follows lowerCamelCase convention."""
        if not isinstance(widget, dict) or 'id' not in widget:
            return
        
        widget_id = widget.get('id', '')
        widget_type = widget.get('type', 'unknown')
        
        # Skip widget types that are excluded from ID requirements
        if widget_type in self.WIDGET_TYPES_WITHOUT_ID_REQUIREMENT:
            return
        
        # Check script syntax - if it's script syntax, validate static parts for lowerCamelCase
        if self._is_script_syntax(widget_id):
            # For script syntax, validate that any starting static string prefixes follow lowerCamelCase
            script_validation_errors = self._validate_script_id_naming(widget_id)
            if script_validation_errors:
                # Get line number
                line_number = 1
                if pmd_model:
                    line_number = self._get_widget_line_number(pmd_model, widget_id)
                elif pod_model:
                    line_number = self._get_pod_widget_line_number(pod_model, widget_id)
                
                # Create a full readable path description
                readable_path = self._build_readable_widget_path(widget, widget_path, section, pmd_model, pod_model)
                path_description = f" at {readable_path}" if readable_path else ""
                
                yield self._create_finding(
                    message=f"Widget ID '{widget_id}'{path_description} has invalid name '{widget_id}'. Must follow lowerCamelCase convention (e.g., 'myField', 'userName').",
                    file_path=pmd_model.file_path if pmd_model else pod_model.file_path,
                    line=line_number
                )
            return
        
        # Validate the ID follows lowerCamelCase convention
        validation_errors = validate_lower_camel_case(widget_id, 'id', 'widget', widget_id)
        
        if validation_errors:
            # Get line number
            line_number = 1
            if pmd_model:
                line_number = self._get_widget_line_number(pmd_model, widget_id)
            elif pod_model:
                line_number = self._get_pod_widget_line_number(pod_model, widget_id)
            
            # Create a full readable path description using the same logic as WidgetIdRequiredRule
            readable_path = self._build_readable_widget_path(widget, widget_path, section, pmd_model, pod_model)
            path_description = f" at {readable_path}" if readable_path else ""
            
            yield self._create_finding(
                message=f"Widget ID '{widget_id}'{path_description} has invalid name '{widget_id}'. Must follow lowerCamelCase convention (e.g., 'myField', 'userName').",
                file_path=pmd_model.file_path if pmd_model else pod_model.file_path,
                line=line_number
            )
    
    def _get_widget_line_number(self, pmd_model: PMDModel, widget_id: str) -> int:
        """Get line number for widget ID field."""
        if widget_id:
            return self.get_field_line_number(pmd_model, 'id', widget_id)
        return 1
    
    def _get_pod_widget_line_number(self, pod_model: PodModel, widget_id: str) -> int:
        """Get line number for widget ID field in POD."""
        if widget_id:
            return self.get_field_line_number(pod_model, 'id', widget_id)
        return 1
    
    def _build_readable_widget_path(self, widget, widget_path, section, pmd_model=None, pod_model=None):
        """
        Build a readable path to a widget using the same logic as script rules.
        
        Args:
            widget: The widget dictionary
            widget_path: Technical path like "body.children.0"
            section: Section name (body, title, footer, etc.)
            pmd_model: PMD model for context
            pod_model: POD model for context
            
        Returns:
            Readable path string like "body->primaryLayout->label: Primary content"
        """
        try:
            if not widget_path:
                # Fallback to just the widget identifier
                return self._get_readable_identifier(widget, 0)
            
            # Split the technical path into components
            path_parts = widget_path.split('.')
            
            # Start with the section name
            display_prefix = section
            
            # Build readable path by following the technical path and using readable identifiers
            if pmd_model and pmd_model.presentation:
                section_data = pmd_model.presentation.__dict__.get(section)
                
                # Handle tabs (which is a list, not a dict)
                if isinstance(section_data, list):
                    # Path format: "tabs.0.children.0" or "tabs.0" 
                    # Path may start with section name, so skip it if present
                    path_start_idx = 0
                    if path_parts and path_parts[0] == section:
                        path_start_idx = 1
                    
                    if path_start_idx < len(path_parts) and path_parts[path_start_idx].isdigit():
                        # First part after section is tab index
                        try:
                            tab_index = int(path_parts[path_start_idx])
                            if 0 <= tab_index < len(section_data):
                                tab_item = section_data[tab_index]
                                if isinstance(tab_item, dict):
                                    # Get readable identifier for the tab
                                    tab_id = self._get_readable_identifier(tab_item, tab_index)
                                    display_prefix = f"{section}[{tab_index}]->{tab_id}"
                                    # Continue building path from the tab item, skipping section and tab index
                                    remaining_parts = path_parts[path_start_idx + 1:]
                                    if remaining_parts:
                                        display_prefix = self._build_path_from_data(tab_item, remaining_parts, display_prefix)
                                    # If no remaining parts, we're at the tab itself, so just return the tab info
                                else:
                                    display_prefix = f"{section}[{tab_index}]"
                            else:
                                display_prefix = section
                        except (ValueError, IndexError):
                            display_prefix = section
                    else:
                        # Path doesn't have expected format, fallback
                        display_prefix = section
                elif isinstance(section_data, dict):
                    # Regular dict section (body, title, footer, etc.)
                    # Path may start with section name, so skip it if present
                    path_start_idx = 1 if path_parts and path_parts[0] == section else 0
                    display_prefix = self._build_path_from_data(section_data, path_parts[path_start_idx:], display_prefix)
                else:
                    display_prefix = section
            elif pod_model and pod_model.seed and pod_model.seed.script:
                current_data = pod_model.seed.script
                display_prefix = self._build_path_from_data(current_data, path_parts, display_prefix)
            
            # The display_prefix already includes the widget identifier from the traversal
            return display_prefix
            
        except Exception:
            # Fallback to just the widget identifier
            return self._get_readable_identifier(widget, 0)
    
    def _is_script_syntax(self, widget_id: str) -> bool:
        """
        Check if a widget ID contains script syntax that should be skipped from lowerCamelCase validation.
        
        Script syntax includes:
        - <% %> delimiters
        
        Args:
            widget_id: The widget ID to check
            
        Returns:
            True if the ID contains script syntax and should be skipped from validation
        """
        if not isinstance(widget_id, str):
            return False
        
        # Check for script delimiters
        if '<%' in widget_id and '%>' in widget_id:
            return True
        
        return False
    
    def _validate_script_id_naming(self, widget_id: str) -> List[str]:
        """
        Validate that static string prefixes in script syntax follow lowerCamelCase convention.
        
        Args:
            widget_id: The script widget ID to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not isinstance(widget_id, str):
            return errors
        
        # Extract static string parts from script syntax
        static_parts = self._extract_static_parts_from_script(widget_id)
        
        for static_part in static_parts:
            if static_part and not self._is_lower_camel_case(static_part):
                errors.append(f"Static prefix '{static_part}' should follow lowerCamelCase convention")
        
        return errors
    
    def _extract_static_parts_from_script(self, script_id: str) -> List[str]:
        """
        Extract static string parts from script syntax.
        
        Examples:
        - "<% `question{{id}}`  %>" -> ["question"]
        - "<% `Question{{id}}`  %>" -> ["Question"] 
        - "<% 'myField' + value  %>" -> ["myField"]
        - "<% 'MyField' + value  %>" -> ["MyField"]
        - "<% someStaticText %>" -> ["someStaticText"]
        - "<% 'prefix' + variable + 'suffix' %>" -> ["prefix", "suffix"]
        """
        static_parts = []
        
        if not isinstance(script_id, str):
            return static_parts
        
        import re
        
        # Handle script syntax with string literals: `<% 'myField' + value  %>` or `<% `text{{var}}`  %>`
        if '<%' in script_id and '%>' in script_id:
            # Extract content between <% and %>
            script_content = re.search(r'<%(.*?)%>', script_id)
            if script_content:
                content = script_content.group(1).strip()
                
                # Check if it starts with a variable first
                if re.match(r'^[a-zA-Z_$][a-zA-Z0-9_$]*', content.strip()):
                    # Starts with a variable - ignore entire script (treat as passing)
                    return []
                
                # Look for string literals (single quotes, double quotes, and backticks)
                # Handle regular quotes: 'text' or "text"
                quote_literals = re.findall(r'[\'"]([^\'"]*)[\'"]', content)
                for string_literal in quote_literals:
                    if string_literal.strip():  # Only add non-empty strings
                        static_parts.append(string_literal.strip())
                
                # Handle backticks: `text{{var}}`
                backtick_matches = re.findall(r'`([^`]+)`', content)
                for match in backtick_matches:
                    # Extract static text before template variables
                    static_text = re.split(r'\{\{.*?\}\}', match)[0].strip()
                    static_parts.append(static_text)  # Include empty strings to catch cases like `{{id}}`
                
                # If no string literals found and it's just static text, use the whole content
                if not quote_literals and not backtick_matches and '{{' not in content and '+' not in content:
                    static_parts.append(content)
        
        return static_parts
    
    def _is_lower_camel_case(self, text: str) -> bool:
        """
        Check if a string follows lowerCamelCase convention.
        
        Args:
            text: The text to check
            
        Returns:
            True if the text follows lowerCamelCase convention
        """
        if not text:
            return True
        
        import re
        camel_case_pattern = re.compile(r'^[a-z][a-zA-Z0-9]*$')
        return bool(camel_case_pattern.match(text))
    
    def _build_path_from_data(self, data, path_parts, current_prefix):
        """
        Build readable path by traversing data structure following path_parts.
        Uses the same logic as script rules for consistency.
        """
        if not path_parts or not isinstance(data, dict):
            return current_prefix
        
        current_key = path_parts[0]
        
        if current_key in data:
            current_value = data[current_key]
            
            if isinstance(current_value, list) and len(path_parts) > 1:
                # This is an array, get the index from next path part
                try:
                    index = int(path_parts[1])
                    if 0 <= index < len(current_value):
                        item = current_value[index]
                        if isinstance(item, dict):
                            # Include array index in the path: key[index]->readable_id
                            readable_id = self._get_readable_identifier(item, index)
                            new_prefix = f"{current_prefix}->{current_key}[{index}]->{readable_id}"
                            
                            # Continue with remaining path parts
                            remaining_parts = path_parts[2:] if len(path_parts) > 2 else []
                            return self._build_path_from_data(item, remaining_parts, new_prefix)
                        else:
                            return f"{current_prefix}->{current_key}[{index}]"
                except (ValueError, IndexError):
                    return f"{current_prefix}->{current_key}"
            else:
                # This is a direct field
                new_prefix = f"{current_prefix}->{current_key}"
                remaining_parts = path_parts[1:] if len(path_parts) > 1 else []
                return self._build_path_from_data(current_value, remaining_parts, new_prefix)
        
        return current_prefix

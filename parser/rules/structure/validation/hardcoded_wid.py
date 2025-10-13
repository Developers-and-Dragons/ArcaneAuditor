"""
Rule to detect hardcoded WID (Workday ID) values in PMD and POD files.

WIDs should be configured in app attributes and not hardcoded in the app source.
There are two exceptions that are allowed in the code:
- Business process WIDs: "d9e41a8c446c11de98360015c5e6daf6" and "d9e4223e446c11de98360015c5e6daf6"

A WID can be identified as a 32 character long string that is alphanumeric.
"""
import re
from typing import Generator, List, Dict, Any, Optional
from ...base import Finding
from ....models import PMDModel, PodModel, ProjectContext
from ...common import PMDLineUtils
from ..shared import StructureRuleBase


class HardcodedWidRule(StructureRuleBase):
    """
    Detects hardcoded WID (Workday ID) values that should be configured in app attributes.
    
    This rule checks for:
    - 32-character alphanumeric strings that look like WIDs
    - Excludes allowed business process WIDs
    - Recommends using app attributes instead of hardcoded values
    """
    
    ID = "HardcodedWidRule"
    DESCRIPTION = "Detects hardcoded WID values that should be configured in app attributes"
    SEVERITY = "ADVICE"
    
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
    
    def _check_string_values_for_wids(self, model: Any, file_path: str, pmd_model: PMDModel = None, pod_model: PodModel = None, path: str = "", context: ProjectContext = None) -> Generator[Finding, None, None]:
        """Recursively check string values for hardcoded WIDs."""
        if isinstance(model, dict):
            # Track widget ID for better context
            widget_id = model.get('id') or model.get('widgetId')
            widget_type = model.get('type')
            
            for key, value in model.items():
                if isinstance(value, str):
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
                    
                    yield from self._check_string_for_wids(value, file_path, context_path, pmd_model, pod_model, context)
                elif isinstance(value, (dict, list)):
                    new_path = f"{path}.{key}" if path else key
                    yield from self._check_string_values_for_wids(value, file_path, pmd_model, pod_model, new_path, context)
        elif isinstance(model, list):
            for i, item in enumerate(model):
                if isinstance(item, str):
                    yield from self._check_string_for_wids(item, file_path, f"{path}[{i}]", pmd_model, pod_model, context)
                elif isinstance(item, (dict, list)):
                    yield from self._check_string_values_for_wids(item, file_path, pmd_model, pod_model, f"{path}[{i}]", context)
    
    def _check_string_for_wids(self, text: str, file_path: str, field_name: str, pmd_model: PMDModel = None, pod_model: PodModel = None, context: ProjectContext = None) -> Generator[Finding, None, None]:
        """Check a single string for hardcoded WID values."""
        if not text:
            return
        
        # Check if this is a script field (contains <% %>)
        if '<%' in text and '%>' in text:
            # Use AST-based detection for script fields (respects comments)
            yield from self._check_script_for_wids_ast(text, file_path, field_name, pmd_model, pod_model, context)
        else:
            # Use regex for plain JSON values (no comments possible)
            yield from self._check_string_for_wids_regex(text, file_path, field_name, pmd_model, pod_model)
    
    def _check_string_for_wids_regex(self, text: str, file_path: str, field_name: str, pmd_model: PMDModel = None, pod_model: PodModel = None) -> Generator[Finding, None, None]:
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
            line_num = self._find_wid_line_number(wid_value, pmd_model, pod_model)
            
            yield self._create_finding(
                message=f"Hardcoded WID '{wid_value}' found in {field_name}. Consider configuring WIDs in app attributes instead of hardcoding them.",
                file_path=file_path,
                line=line_num
            )
    
    def _check_script_for_wids_ast(self, script_content: str, file_path: str, field_name: str, pmd_model: PMDModel = None, pod_model: PodModel = None, context: ProjectContext = None) -> Generator[Finding, None, None]:
        """Check a script field for hardcoded WID values using AST (ignores comments)."""
        # Parse with AST using cached parsing (leverage context-level cache)
        ast = self._parse_script_content(script_content, context)
        if not ast:
            # If parsing fails, fall back to regex (but this means comments won't be filtered)
            yield from self._check_string_for_wids_regex(script_content, file_path, field_name, pmd_model, pod_model)
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
                        
                        if re.match(wid_pattern, literal_value, re.IGNORECASE):
                            wid_value = literal_value.lower()
                            
                            if wid_value in self.ALLOWED_WIDS:
                                continue
                            
                            line_num = self._find_wid_line_number(wid_value, pmd_model, pod_model)
                            context_desc = f"in variable '{var_name}' in {field_name}" if var_name else f"in {field_name}"
                            
                            yield self._create_finding(
                                message=f"Hardcoded WID '{wid_value}' found {context_desc}. Consider configuring WIDs in app attributes instead of hardcoding them.",
                                file_path=file_path,
                                line=line_num
                            )
    
    def _find_wid_line_number(self, wid_value: str, pmd_model: PMDModel = None, pod_model: PodModel = None) -> int:
        """Find the line number where a WID value appears in the source content."""
        if pmd_model:
            return self.find_pattern_line_number(pmd_model, wid_value, case_sensitive=False)
        elif pod_model:
            return self.find_pattern_line_number(pod_model, wid_value, case_sensitive=False)
        return 1

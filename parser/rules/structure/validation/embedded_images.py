"""
Rule to detect embedded base64 images in PMD and POD files.

Images should be stored as external files and referenced by path, not embedded directly
as base64 data in the application files.

This rule checks for base64 encoded image data using the pattern:
data:image/[type];base64,[data]
"""
import re
from typing import Generator, Any

from ...base import Finding
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class EmbeddedImagesRule(StructureRuleBase):
    """
    Detects embedded base64 images that should be stored as external files.
    
    This rule checks for base64 encoded image data using the pattern:
    data:image/[type];base64,[data]
    
    Images should be stored as external files and referenced by path instead
    of being embedded directly in the application files.
    """
    
    ID = "EmbeddedImagesRule"
    DESCRIPTION = "Detects embedded images that should be stored as external files"
    SEVERITY = "ADVICE"
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Base64-encoded images bloat your PMD/Pod file sizes dramatically (often 30% larger than the image itself) and make files harder to version control since small image changes create large text diffs. External images load faster, cache better, and keep your code files focused on logic. This significantly improves page load performance and makes code reviews manageable.''',
        'catches': [
            'Base64 encoded images embedded directly in files',
            'Images that should be stored as external files'
        ],
        'examples': '''**Example violations:**

```json
{
  "type": "image",
  "url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..." // ❌ Embedded image
}
```

**Fix:**

```json
{
  "type": "image", 
  "url": "http://example.com/images/logo.png" // ✅ External image file
}
```''',
        'recommendation': 'Store images as external files and reference them by URL instead of embedding base64-encoded data. This reduces file size, improves page load performance, and makes version control more manageable.'
    }
    
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for embedded images."""
        yield from self._check_pmd_embedded_images(pmd_model, context)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for embedded images."""
        yield from self._check_pod_embedded_images(pod_model, context)
    
    def _check_pmd_embedded_images(self, pmd_model: PMDModel, context: ProjectContext = None) -> Generator[Finding, None, None]:
        """Check PMD file for embedded images."""
        # Convert PMD model to dictionary for recursive checking
        pmd_dict = pmd_model.model_dump(exclude={'file_path', 'source_content'})
        yield from self._check_string_values_for_embedded_images(pmd_dict, pmd_model.file_path, context)
    
    def _check_pod_embedded_images(self, pod_model: PodModel, context: ProjectContext = None) -> Generator[Finding, None, None]:
        """Check POD file for embedded images."""
        # Convert POD model to dictionary for recursive checking
        pod_dict = pod_model.model_dump(exclude={'file_path', 'source_content'})
        yield from self._check_string_values_for_embedded_images(pod_dict, pod_model.file_path, context)
    
    def _check_string_values_for_embedded_images(self, model: Any, file_path: str, context: ProjectContext = None) -> Generator[Finding, None, None]:
        """Recursively check string values for embedded images."""
        if isinstance(model, dict):
            for key, value in model.items():
                if isinstance(value, str):
                    yield from self._check_string_for_embedded_images(value, file_path, key, context)
                elif isinstance(value, (dict, list)):
                    yield from self._check_string_values_for_embedded_images(value, file_path, context)
        elif isinstance(model, list):
            for i, item in enumerate(model):
                if isinstance(item, str):
                    yield from self._check_string_for_embedded_images(item, file_path, f"[{i}]", context)
                elif isinstance(item, (dict, list)):
                    yield from self._check_string_values_for_embedded_images(item, file_path, context)
    
    def _check_string_for_embedded_images(self, text: str, file_path: str, field_name: str, context: ProjectContext = None) -> Generator[Finding, None, None]:
        """Check a single string for embedded image data."""
        if not text:
            return
        
        # Check if this is a script field (contains <% %>)
        if '<%' in text and '%>' in text:
            # Use AST-based detection for script fields (respects comments)
            yield from self._check_script_for_embedded_images_ast(text, file_path, field_name, context)
        else:
            # Use regex for plain JSON values (no comments possible)
            yield from self._check_string_for_embedded_images_regex(text, file_path, field_name)
    
    def _check_string_for_embedded_images_regex(self, text: str, file_path: str, field_name: str) -> Generator[Finding, None, None]:
        """Check a plain string (non-script) for embedded images using regex."""
        # Pattern to match base64 encoded images (data:image/...) with minimum length
        base64_image_pattern = r'data:image/[^;]+;base64,[A-Za-z0-9+/=]{20,}'
        
        matches = list(re.finditer(base64_image_pattern, text, re.IGNORECASE))
        for match in matches:
            # Calculate line number using unified method
            line_num = self.get_line_from_text_position(text, match.start())
            
            yield self._create_finding(
                message=f"Embedded base64 image found in {field_name}. Large files can cause performance issues and/or cause pages to exceed the file size limits. Consider linking to an external image file, instead of embedding it directly.",
                file_path=file_path,
                line=line_num,
                path=field_name or None,
            )
    
    def _check_script_for_embedded_images_ast(self, script_content: str, file_path: str, field_name: str, context: ProjectContext = None) -> Generator[Finding, None, None]:
        """Check a script field for embedded images using AST (ignores comments)."""
        # Parse with AST using cached parsing (leverage context-level cache)
        ast = self._parse_script_content(script_content, context)
        if not ast:
            # If parsing fails, fall back to regex (but this means comments won't be filtered)
            yield from self._check_string_for_embedded_images_regex(script_content, file_path, field_name)
            return
        
        # Pattern to match base64 encoded images (with minimum length to avoid false positives)
        base64_image_pattern = r'^data:image/[^;]+;base64,[A-Za-z0-9+/=]{20,}$'
        
        # Extract all string literals from AST with context
        for variable_decl in ast.find_data('variable_declaration'):
            # Extract variable name
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
                        
                        if re.match(base64_image_pattern, literal_value, re.IGNORECASE):
                            context_desc = f"in variable '{var_name}' in {field_name}" if var_name else f"in {field_name}"
                            
                            yield self._create_finding(
                                message=f"Embedded base64 image found {context_desc}. Large files can cause performance issues and/or cause pages to exceed the file size limits. Consider linking to an external image file, instead of embedding it directly.",
                                file_path=file_path,
                                line=1,  # Would need more sophisticated line tracking for AST
                                path=field_name or None,
                            )
    

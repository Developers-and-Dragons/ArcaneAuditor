from abc import ABC, abstractmethod
from enum import Enum
from typing import Generator, Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from ..models import ProjectContext, PMDModel, PodModel
from lark import Tree
import re


class FixStrategy(str, Enum):
    """How an AI agent should handle a rule's findings.

    Values are str-enums so they serialize cleanly to JSON.
    """
    ACTIONABLE = "actionable"        # Finding carries a deterministic fix; agent may surface a suggested_replacement
    HUMAN_REVIEW = "human_review"    # Surface to the human; agent must not attempt to auto-resolve


class Category(str, Enum):
    """Broad classification for grouping/filtering rules."""
    SCRIPT = "script"
    STRUCTURE = "structure"
    ENDPOINT = "endpoint"
    WIDGET = "widget"
    ORCHESTRATION = "orchestration"
    CUSTOM = "custom"


@dataclass
class Finding:
    """Represents a single issue found by a rule."""
    rule: 'Rule'
    message: str
    line: int = 0
    file_path: str = ""
    snippet: Optional[str] = None
    suggested_replacement: Optional[str] = None
    path: Optional[str] = None

    def __post_init__(self):
        # Set derived fields automatically
        self.rule_id = self.rule.__class__.__name__
        self.rule_description = self.rule.DESCRIPTION
        self.severity = self.rule.SEVERITY
        self.category = self.rule.CATEGORY
        self.fix_strategy = self.rule.FIX_STRATEGY
        # Line intentionally excluded so re-runs after a fix still join.
        import hashlib
        raw = f"{self.rule_id}|{self.file_path}|{self.path or ''}|{self.message}"
        self.finding_id = "sha1:" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

    def __repr__(self) -> str:
        return f"[{self.rule_id}:{self.line}] ({self.severity}) in '{self.file_path}': {self.message}"

# The abstract base class that all rule implementations must inherit from.
class Rule(ABC):
    """Abstract base class for all analysis rules."""
    # --- Metadata for the rule ---
    ID: str = "RULE000"
    DESCRIPTION: str = "This is a base rule."
    SEVERITY: str = "ADVICE" # Can be 'ADVICE', 'ACTION'

    # Broad category for filtering/grouping. Default STRUCTURE; ScriptRuleBase overrides to SCRIPT.
    CATEGORY: Category = Category.STRUCTURE

    # How an agent should handle this rule's findings.
    # Default HUMAN_REVIEW (safest — agents should surface, not act).
    FIX_STRATEGY: FixStrategy = FixStrategy.HUMAN_REVIEW

    # Dictionary defining available custom settings.
    # If empty, the rule does not support custom configuration.
    AVAILABLE_SETTINGS: Dict[str, Any] = {}
    
    # Metadata for the UI Grimoire - documentation displayed in the UI
    DOCUMENTATION: Dict[str, Any] = {
        'why': '',           # "Why This Matters" - explanation of the rule's importance
        'catches': [],       # List of strings describing "What it catches"
        'examples': '',      # Code examples (good/bad) - formatted as markdown or plain text
        'recommendation': '' # "Fix" or general advice on how to resolve violations
    }

    @abstractmethod
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """
        The main entry point for a rule, which analyzes the entire project.
        This method should be a generator that yields Finding objects.
        
        Args:
            context: The fully-built ProjectContext containing all application models.
        
        Yields:
            Finding objects for any violations discovered.
        """
        # This is an abstract method; it must be implemented by subclasses.
        # The 'yield from' statement is a convenient way to delegate to
        # more specific visitor methods if you choose to implement them.
        yield from []

    # --- Optional "visitor" methods for convenience ---
    # Subclasses can implement these to organize their logic.
    def visit_pmd(self, pmd_model: PMDModel) -> Generator[Finding, None, None]:
        """Optional visitor method to run logic on a single PMD model."""
        yield from []

    def find_script_fields(self, pmd_model: PMDModel, context=None) -> List[Tuple[str, str, str, int]]:
        """
        Recursively find all fields in a PMD model that contain script content (<% %>).
        Uses context-level caching to avoid repeated expensive parsing operations.
        
        Args:
            pmd_model: The PMD model to search
            context: ProjectContext for caching (optional)
        
        Returns:
            List of tuples: (field_path, field_value, field_name, line_offset)
            - field_path: Full path to the field (e.g., "script", "onLoad")
            - field_value: The actual script content
            - field_name: Just the field name for display purposes
            - line_offset: Line number where the script starts in the original file
        """
        # Use context-level caching if available
        if context is not None:
            cached_fields = context.get_cached_pmd_script_fields(pmd_model.pageId)
            if cached_fields is not None:
                return cached_fields
            
            # If not cached, extract and cache them
            script_fields = self._extract_script_fields(pmd_model)
            context.set_cached_pmd_script_fields(pmd_model.pageId, script_fields)
            return script_fields
        else:
            # Fallback to model-level caching for backward compatibility
            cached_fields = pmd_model.get_cached_script_fields()
            if cached_fields is not None:
                return cached_fields
            
            # If not cached, extract and cache them
            script_fields = self._extract_script_fields(pmd_model)
            pmd_model.set_cached_script_fields(script_fields)
            return script_fields
    
    def get_cached_ast(self, script_content: str, context=None) -> Optional[Tree]:
        """
        Get cached AST for script content, or parse and cache it.
        
        Args:
            script_content: The script content to parse
            context: ProjectContext for caching (optional)
        
        Returns:
            Parsed AST or None if parsing failed
        """
        # Strip PMD wrappers if present
        content = self._strip_pmd_wrappers(script_content)
        if not content:
            return None
        
        # Use context-level caching if available
        if context is not None:
            cache_key = hash(content)
            cached_ast = context.get_cached_ast(cache_key)
            if cached_ast is None:
                try:
                    from ..pmd_script_parser import parse_with_preprocessor
                    parsed_ast = parse_with_preprocessor(content)
                    context.set_cached_ast(cache_key, parsed_ast)
                    return parsed_ast
                except Exception as e:
                    from utils.console import error
                    error(f"Failed to parse script content: {e}")
                    context.set_cached_ast(cache_key, None)
                    return None
            else:
                return cached_ast
        else:
            # Fallback to per-rule caching for backward compatibility
            cache_key = hash(content)
            if not hasattr(self, '_script_ast_cache'):
                self._script_ast_cache = {}
            
            if cache_key not in self._script_ast_cache:
                try:
                    from ..pmd_script_parser import parse_with_preprocessor
                    self._script_ast_cache[cache_key] = parse_with_preprocessor(content)
                except Exception as e:
                    from utils.console import error
                    error(f"Failed to parse script content: {e}")
                    self._script_ast_cache[cache_key] = None
            
            return self._script_ast_cache[cache_key]
    
    def _get_readable_identifier(self, item: Dict[str, Any], fallback_index: int) -> str:
        """
        Extract a readable identifier from a dictionary item.
        
        Priority order:
        1. id (widget ID) - most specific
        2. label - human-readable description
        3. type - widget type
        4. name - for endpoints and other named items
        5. [index] - fallback to array index
        
        Args:
            item: Dictionary to extract identifier from
            fallback_index: Index to use if no other identifier found
            
        Returns:
            Human-readable identifier string
        """
        # Priority 1: id
        if 'id' in item and isinstance(item['id'], str) and item['id'].strip():
            return f"id: {item['id']}"

        # Priority 2: columnId
        if 'columnId' in item and isinstance(item['columnId'], str) and item['columnId'].strip():
            return f"columnId: {item['columnId']}"
        
        # Priority 3: label
        if 'label' in item and isinstance(item['label'], str) and item['label'].strip():
            # Truncate long labels
            label = item['label'][:40] + '...' if len(item['label']) > 40 else item['label']
            return f"label: {label}"
        
        # Priority 4: type
        if 'type' in item and isinstance(item['type'], str) and item['type'].strip():
            return f"type: {item['type']}"
        
        # Priority 5: name (for endpoints, etc.)
        if 'name' in item and isinstance(item['name'], str) and item['name'].strip():
            return f"name: {item['name']}"
        
        # Fallback: index
        return f"[{fallback_index}]"
    
    def _is_multiline_script_block(self, script_value: str) -> bool:
        """
        Determine if a script block is multi-line (content starts on line after <%).
        
        Single-line: <% content %> - content starts on same line as <%
        Multi-line: <% on one line, content on next line - content starts on line after <%
        """
        if not script_value.startswith('<%'):
            return False
        
        # Find where the actual content starts after <%
        idx_after_open = 2  # After '<%'
        
        # Skip whitespace and count newlines after <%
        while idx_after_open < len(script_value):
            if script_value[idx_after_open] == '\n':
                # Found a newline after <% - this is a multi-line script
                return True
            elif script_value[idx_after_open] in ' \t\r':
                idx_after_open += 1
            else:
                # Found first non-whitespace character on same line as <%
                return False
        
        return False

    def _extract_script_fields(self, pmd_model: PMDModel) -> List[Tuple[str, str, str, int]]:
        """Internal method to extract script fields without caching."""
        script_fields = []
        script_pattern = r'<%.*?%>'
        
        # Track the last line found to search forward from there
        last_line_found = 0
        
        # Track which hashes we've already used (for handling duplicates in order)
        used_hashes = {}  # hash -> count of times used
        
        def _search_dict(data: Dict[str, Any], prefix: str = "", file_content: str = "", display_prefix: str = "") -> None:
            """Recursively search a dictionary for script fields."""
            nonlocal last_line_found, used_hashes
            
            for key, value in data.items():
                if isinstance(value, str) and re.search(script_pattern, value, re.DOTALL):
                    field_path = f"{prefix}.{key}" if prefix else key
                    # Use human-readable display name
                    display_name = f"{display_prefix}->{key}" if display_prefix else key
                    
                    # Try hash-based lookup first (exact line numbers for both multiline and single-line)
                    line_offset = pmd_model.get_script_start_line(value)
                    
                    # Fallback to fuzzy search if hash lookup fails
                    # This handles: POD files, edge cases, malformed scripts
                    if line_offset is None:
                        # Compute hash for tracking duplicates
                        import hashlib
                        value_hash = hashlib.sha256(value.encode('utf-8')).hexdigest()
                        
                        # Track occurrence index for duplicates
                        occurrence_index = used_hashes.get(value_hash, 0)
                        used_hashes[value_hash] = occurrence_index + 1
                        
                        # Use fuzzy search with duplicate handling
                        line_offset = self._calculate_script_line_offset(
                            file_content, value, 
                            search_start_line=last_line_found,
                            occurrence_index=occurrence_index
                        ) if file_content else 1
                    
                    last_line_found = line_offset
                    script_fields.append((field_path, value, display_name, line_offset))
                elif isinstance(value, dict):
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    new_display_prefix = f"{display_prefix}->{key}" if display_prefix else key
                    _search_dict(value, new_prefix, file_content, new_display_prefix)
                elif hasattr(value, 'model_dump'):  # Handle Pydantic models
                    # Convert Pydantic model to dictionary
                    model_dict = value.model_dump()
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    new_display_prefix = f"{display_prefix}->{key}" if display_prefix else key
                    _search_dict(model_dict, new_prefix, file_content, new_display_prefix)
                elif isinstance(value, list):
                    for i, item in enumerate(value):
                        if isinstance(item, dict):
                            # Create technical path with index
                            new_prefix = f"{prefix}.{key}.{i}" if prefix else f"{key}.{i}"
                            
                            # Create human-readable path using priority: id -> label -> type -> name -> index
                            readable_id = self._get_readable_identifier(item, i)
                            new_display_prefix = f"{display_prefix}->{key}[{i}]->{readable_id}" if display_prefix else f"{key}[{i}]->{readable_id}"
                            
                            _search_dict(item, new_prefix, file_content, new_display_prefix)
                        elif isinstance(item, str) and re.search(script_pattern, item, re.DOTALL):
                            field_path = f"{prefix}.{key}.{i}" if prefix else f"{key}.{i}"
                            # Use human-readable display name
                            display_name = f"{display_prefix}->{key}[{i}]" if display_prefix else f"{key}[{i}]"
                            
                            # Try hash-based lookup first (exact line numbers)
                            line_offset = pmd_model.get_script_start_line(item)
                            
                            # Fallback to fuzzy search if needed (POD files, edge cases)
                            if line_offset is None:
                                import hashlib
                                value_hash = hashlib.sha256(item.encode('utf-8')).hexdigest()
                                occurrence_index = used_hashes.get(value_hash, 0)
                                used_hashes[value_hash] = occurrence_index + 1
                                
                                line_offset = self._calculate_script_line_offset(
                                    file_content, item, 
                                    search_start_line=last_line_found,
                                    occurrence_index=occurrence_index
                                ) if file_content else 1
                            
                            last_line_found = line_offset
                            script_fields.append((field_path, item, display_name, line_offset))
                        elif hasattr(item, 'model_dump'):  # Handle Pydantic models in lists
                            # Convert Pydantic model to dictionary
                            model_dict = item.model_dump()
                            new_prefix = f"{prefix}.{key}.{i}" if prefix else f"{key}.{i}"
                            
                            # Create human-readable path using priority: id -> label -> type -> name -> index
                            readable_id = self._get_readable_identifier(model_dict, i)
                            new_display_prefix = f"{display_prefix}->{key}[{i}]->{readable_id}" if display_prefix else f"{key}[{i}]->{readable_id}"
                            
                            _search_dict(model_dict, new_prefix, file_content, new_display_prefix)
        
        # Get the source content from the PMD model
        source_content = getattr(pmd_model, 'source_content', '')
        
        # Convert PMD model to dict for recursive search
        pmd_dict = pmd_model.model_dump(exclude={'file_path', 'source_content'})
        _search_dict(pmd_dict, file_content=source_content)
        
        return script_fields
    
    def _calculate_script_line_offset(self, file_content: str, script_content: str, search_start_line: int = 0, occurrence_index: int = 0) -> int:
        """
        Calculate the line number where the script content starts in the original file.
        
        Args:
            file_content: The full source file content
            script_content: The script content to find (from parsed JSON, has real newlines)
            search_start_line: Line number to start searching from (0-based, for avoiding duplicates)
            occurrence_index: Which occurrence to find (0 = first, 1 = second, etc.)
            
        Returns:
            Line number (1-based) where the script starts
        """
        if not file_content or not script_content:
            return 1
        
        lines = file_content.split('\n')
        start_index = max(0, search_start_line)
        
        # Strategy 1: For single-line scripts, search for exact match
        # This works when the entire script is on one line in the JSON
        if '\n' not in script_content:
            # The script_content from parsed JSON has unescaped quotes
            # But the source file has escaped quotes (\")
            # Re-escape for matching
            escaped_content = script_content.replace('"', '\\"')
            
            # Search from BEGINNING for exact matches (not from start_index)
            # because JSON field order doesn't match file order
            matches_found = 0
            for i in range(0, len(lines)):  # Search from beginning
                if script_content in lines[i] or escaped_content in lines[i]:
                    if matches_found == occurrence_index:
                        # For single-line scripts, the exact match IS on the content line
                        # Don't adjust - return i + 1 as-is
                        return i + 1
                    matches_found += 1
            
            # If exact match fails, find the next line with <% after start_index
            # This is reliable for sequential processing
            for i in range(start_index, len(lines)):
                if '<%' in lines[i]:
                    # Check if content starts on same line or next line
                    if self._is_multiline_script_block(script_content):
                        return i + 2  # Content starts on next line
                    else:
                        return i + 1  # Content starts on same line
        
        # Strategy 2: For multi-line scripts, search for distinctive content
        # Search for unique code patterns that would appear in the file
        if '\n' in script_content and script_content.startswith('<%'):
            script_lines = script_content.split('\n')
            # Get distinctive code lines (not just whitespace or braces)
            code_lines = [line.strip() for line in script_lines[1:-1]  # Skip first (<%) and last (%>)
                         if line.strip() and len(line.strip()) > 10
                         and not line.strip() in ['{', '}', '};']]
            
            if code_lines:
                # Use multiple distinctive lines for better matching
                # Try first, middle, and last code lines to find the best match
                search_lines_to_try = []
                if len(code_lines) > 0:
                    search_lines_to_try.append(('first', code_lines[0]))
                if len(code_lines) > 2:
                    search_lines_to_try.append(('middle', code_lines[len(code_lines) // 2]))
                if len(code_lines) > 1:
                    search_lines_to_try.append(('last', code_lines[-1]))
                
                for label, search_line in search_lines_to_try:
                    search_text = search_line[:50]
                    # Re-escape for matching against JSON source
                    search_text_escaped = search_text.replace('\t', '\\t').replace('\n', '\\n')
                    
                    # Search from start_index first (forward search for sequential fields)
                    for i in range(start_index, len(lines)):
                        if search_text in lines[i] or search_text_escaped in lines[i]:
                            # Found the code - now find the opening <% before it (within reasonable distance)
                            for j in range(i, max(0, i - 30), -1):  # Search backward from found line
                                if '<%' in lines[j]:
                                    # Verify this is likely the right <% by checking proximity
                                    if i - j < 25:  # Should be within 25 lines
                                        # Found the <%, now determine where AST line 1 starts
                                        if self._is_multiline_script_block(script_content):
                                            return j + 2  # Multiline: return line after <%
                                        else:
                                            return j + 1  # Single-line: return line with <%
                            return i + 1
                    
                    # If not found forward, search from beginning (handles out-of-order presentation fields)
                    for i in range(0, len(lines)):
                        if search_text in lines[i] or search_text_escaped in lines[i]:
                            # Found the code - now find the opening <% before it
                            for j in range(i, max(0, i - 30), -1):  # Search backward from found line
                                if '<%' in lines[j]:
                                    if i - j < 25:
                                        # Found the <%, now determine where AST line 1 starts
                                        if self._is_multiline_script_block(script_content):
                                            return j + 2  # Multiline: return line after <%
                                        else:
                                            return j + 1  # Single-line: return line with <%
                            return i + 1
        
        # Strategy 3: Search for distinctive content from within the script
        # Extract a unique part of the script that should appear in the file
        stripped = script_content.strip()
        if stripped.startswith('<%') and stripped.endswith('%>'):
            # Get content between <% and %>
            inner = stripped[2:-2].strip()
            if inner:
                # Get first substantial line of code
                code_lines = [line.strip() for line in inner.split('\n') if line.strip() and len(line.strip()) > 5]
                if code_lines:
                    # Search for the first unique line
                    for code_line in code_lines[:3]:  # Try first 3 lines
                        search_text = code_line[:50]
                        if len(search_text) > 15:
                            for i in range(start_index, len(lines)):
                                if search_text in lines[i]:
                                    # Found it - now find the opening <% before this line
                                    for j in range(max(0, i - 10), i + 1):
                                        if '<%' in lines[j]:
                                            return j + 1
                                    return i + 1  # Fallback to line where code was found
        
        # Strategy 4: Search for ANY <% tag from start position
        for i in range(start_index, len(lines)):
            if '<%' in lines[i]:
                return i + 1
        
        # Strategy 5: If nothing found forward, search from beginning for ANY <%
        for i in range(0, len(lines)):
            if '<%' in lines[i]:
                return i + 1
        
        # Fallback: return line 1 (should rarely happen)
        return 1
    
    def _strip_pmd_wrappers(self, script_content):
        """Strip <% and %> wrappers from PMD script content."""
        content = script_content.strip()
        if content.startswith('<%') and content.endswith('%>'):
            content = content[2:-2].strip()
        
        # Unescape all escape sequences that were escaped during JSON processing
        # We need to be careful with single quotes - they should remain escaped for valid PMD Script
        # First, handle the case where we have double backslashes (from PMD source)
        # Convert \\' to \' (double backslash + quote becomes escaped quote)
        content = content.replace('\\\\', '\\')
        
        # Then handle other escape sequences
        content = content.replace('\\n', '\n')
        content = content.replace('\\t', '\t')
        content = content.replace('\\r', '\r')
        content = content.replace('\\"', '"')
        
        # Note: We do NOT unescape single quotes - they should remain as \' for valid PMD Script
        
        return content

    def traverse_widgets_recursively(self, widgets: List[Dict[str, Any]], widget_path: str = "") -> Generator[Tuple[Dict[str, Any], str, int], None, None]:
        """
        Recursively traverse widgets and their children arrays.
        
        Args:
            widgets: List of widget dictionaries to traverse
            widget_path: Current path in the widget hierarchy (e.g., "body.children", "body.children.0.children")
            
        Yields:
            Tuples of (widget, full_path, index) for each widget found
        """
        if not isinstance(widgets, list):
            return
            
        for i, widget in enumerate(widgets):
            if not isinstance(widget, dict):
                continue
                
            # Yield the current widget
            current_path = f"{widget_path}.{i}" if widget_path else str(i)
            yield (widget, current_path, i)
            
            # Check if this widget has children and recurse
            children = widget.get('children', [])
            if isinstance(children, list) and children:
                children_path = f"{current_path}.children"
                yield from self.traverse_widgets_recursively(children, children_path)

    def traverse_presentation_structure(self, presentation_data: Dict[str, Any], base_path: str = "", parent_type: str = None) -> Generator[Tuple[Dict[str, Any], str, int, str, str], None, None]:
        """
        Generic traversal of PMD presentation structure that handles different layout types.
        
        This method can handle:
        - Standard sections with 'children' arrays
        - areaLayout with 'primaryLayout' and 'secondaryLayout' 
        - basicFormLayout with 'sections' containing widgets
        - hubs and other layout types
        - Any nested structure containing widgets
        
        Args:
            presentation_data: The presentation dictionary to traverse
            base_path: Base path for tracking widget locations
            parent_type: Type of parent widget (for context-aware exclusions)
            
        Yields:
            Tuples of (widget, full_path, index, parent_type, container_name) for each widget found
        """
        if not isinstance(presentation_data, dict):
            return
            
        # Known widget container field names
        WIDGET_CONTAINERS = {
            'children', 'primaryLayout', 'secondaryLayout', 'sections', 
            'items', 'navigationTasks', 'cellTemplate', 'columns'
        }
        
        # Known layout types that may contain nested structures
        LAYOUT_TYPES = {
            'areaLayout', 'basicFormLayout', 'section', 'hub',
            'layout', 'panelList', 'grid', 'fieldSet'
        }
        
        def _traverse_container(container_data: Any, container_path: str, container_name: str = "", already_yielded: bool = False, current_parent_type: str = None):
            """Recursively traverse a container that may hold widgets."""
            if isinstance(container_data, list):
                # Direct list of widgets
                for i, item in enumerate(container_data):
                    if isinstance(item, dict):
                        item_path = f"{container_path}.{i}" if container_path else str(i)
                        yield (item, item_path, i, current_parent_type, container_name)
                        
                        # Recursively check for nested containers (mark as already yielded)
                        # The item becomes the new parent
                        item_type = item.get('type')
                        yield from _traverse_container(item, item_path, "", already_yielded=True, current_parent_type=item_type)
            elif isinstance(container_data, dict):
                # If this dict has a 'type' field and hasn't been yielded yet, it's a top-level widget - yield it
                if 'type' in container_data and not already_yielded:
                    yield (container_data, container_path, 0, current_parent_type, container_name)
                
                # Check if this is a widget with nested containers
                widget_type = container_data.get('type', '')
                
                # Look for known widget container fields
                for field_name in WIDGET_CONTAINERS:
                    if field_name in container_data:
                        field_data = container_data[field_name]
                        field_path = f"{container_path}.{field_name}" if container_path else field_name
                        # Pass current widget type as parent for children
                        yield from _traverse_container(field_data, field_path, field_name, already_yielded=False, current_parent_type=widget_type)
                
                # For layout types, also check for any array fields that might contain widgets
                if widget_type in LAYOUT_TYPES:
                    for key, value in container_data.items():
                        if key not in WIDGET_CONTAINERS and isinstance(value, list):
                            # Check if this list contains widget-like objects
                            if value and isinstance(value[0], dict) and 'type' in value[0]:
                                field_path = f"{container_path}.{key}" if container_path else key
                                yield from _traverse_container(value, field_path, key, already_yielded=False, current_parent_type=widget_type)
        
        # Start traversal from the presentation data
        yield from _traverse_container(presentation_data, base_path, "", False, parent_type)
    
    
    def _parse_script_content(self, script_content: str, context=None):
        """Parse script content using the PMD script grammar with context-level caching support."""
        try:
            # Strip PMD wrappers if present
            content = self._strip_pmd_wrappers(script_content)
            if not content:
                return None
            
            # Check if this looks like a string value that contains script blocks rather than actual script
            stripped_content = script_content.strip()
            
            # If the original content has <% %> tags AND content outside the tags, it's a template expression
            if '<%' in stripped_content and '%>' in stripped_content:
                # Simple check: if content doesn't start and end with script tags, it's a template expression
                if not (stripped_content.startswith('<%') and stripped_content.endswith('%>')):
                    from .script.shared.template_expression_preprocessor import TemplateExpressionPreprocessor
                    preprocessor = TemplateExpressionPreprocessor()
                    if preprocessor.is_template_expression(stripped_content):
                        try:
                            return preprocessor.preprocess_template_expression(stripped_content)
                        except Exception as e:
                            from utils.console import warn
                            warn(f"Failed to parse template expression '{stripped_content[:50]}...': {e}")
                            return None
                
            
            # Use context-level caching if available
            if context is not None:
                return self.get_cached_ast(content, context)
            else:
                # Fallback to per-rule caching for backward compatibility
                cache_key = hash(content)
                if not hasattr(self, '_script_ast_cache'):
                    self._script_ast_cache = {}
                
                if cache_key not in self._script_ast_cache:
                    from ..pmd_script_parser import parse_with_preprocessor
                    self._script_ast_cache[cache_key] = parse_with_preprocessor(content)
                
                return self._script_ast_cache[cache_key]
        except Exception as e:
            from utils.console import error
            error(f"Failed to parse script content: {e}")
            # Add parsing error to context if available
            if context is not None:
                context.parsing_errors.append(f"Script parsing failed: {str(e)}")
            return None
    
    # Pod-specific utility methods
    
    def find_pod_script_fields(self, pod_model: PodModel) -> List[Tuple[str, str, str, int]]:
        """
        Find all script content within Pod endpoints and template widgets.
        
        Args:
            pod_model: The Pod model to search
            
        Returns:
            List of tuples containing:
            - field_path: Path to the field (e.g., "seed.endPoints[0].onReceive")
            - script_content: The actual script content
            - display_name: Human-readable field name
            - line_offset: Line number where the script starts
        """
        script_fields = []
        script_pattern = r'<%.*?%>'
        
        # Track which hashes we've used (for duplicates)
        used_hashes = {}
        last_line_found = 0
        
        # Search endpoints in seed for script content (any field with <% %>)
        if pod_model.seed.endPoints:
            for i, endpoint in enumerate(pod_model.seed.endPoints):
                if isinstance(endpoint, dict):
                    for field_name, field_value in endpoint.items():
                        if isinstance(field_value, str) and re.search(script_pattern, field_value, re.DOTALL):
                            field_path = f"seed.endPoints[{i}].{field_name}"
                            endpoint_name = endpoint.get('name', f'endpoint_{i}')
                            display_name = f"endpoint->name: {endpoint_name}->{field_name}"
                            
                            # Try hash-based lookup first (exact line numbers)
                            line_offset = pod_model.get_script_start_line(field_value)
                            
                            # Fallback to fuzzy search if needed
                            if line_offset is None:
                                import hashlib
                                value_hash = hashlib.sha256(field_value.encode('utf-8')).hexdigest()
                                occurrence_index = used_hashes.get(value_hash, 0)
                                used_hashes[value_hash] = occurrence_index + 1
                                
                                line_offset = self._calculate_pod_script_line_offset(
                                    pod_model.source_content, field_value,
                                    search_start_line=last_line_found,
                                    occurrence_index=occurrence_index
                                )
                            
                            last_line_found = line_offset
                            script_fields.append((field_path, field_value, display_name, line_offset))
        
        # Search template widgets for script content (e.g., onClick, onLoad handlers)
        template_scripts = self._find_template_script_fields(pod_model, pod_model.seed.template, "seed.template", used_hashes, last_line_found)
        script_fields.extend(template_scripts)
        
        return script_fields
    
    def _find_template_script_fields(self, pod_model: PodModel, widget_data: Any, path_prefix: str, used_hashes: dict, last_line_found: int) -> List[Tuple[str, str, str, int]]:
        """Recursively search template widgets for script content."""
        script_fields = []
        script_pattern = r'<%.*?%>'
        
        def _search_widget(widget: Dict[str, Any], widget_path: str):
            nonlocal last_line_found
            # Search all widget fields for script content (any field with <% %>)
            for field_name, field_value in widget.items():
                if isinstance(field_value, str) and re.search(script_pattern, field_value, re.DOTALL):
                    field_path = f"{widget_path}.{field_name}"
                    widget_type = widget.get('type', 'unknown')
                    widget_id = widget.get('id', 'unnamed')
                    display_name = f"{widget_type} widget->id: {widget_id}->{field_name}"
                    
                    # Try hash-based lookup first (exact line numbers)
                    line_offset = pod_model.get_script_start_line(field_value)
                    
                    # Fallback to fuzzy search if needed
                    if line_offset is None:
                        import hashlib
                        value_hash = hashlib.sha256(field_value.encode('utf-8')).hexdigest()
                        occurrence_index = used_hashes.get(value_hash, 0)
                        used_hashes[value_hash] = occurrence_index + 1
                        
                        line_offset = self._calculate_pod_script_line_offset(
                            pod_model.source_content, field_value,
                            search_start_line=last_line_found,
                            occurrence_index=occurrence_index
                        )
                    
                    last_line_found = line_offset
                    script_fields.append((field_path, field_value, display_name, line_offset))
            
            # Recursively search children
            if 'children' in widget and isinstance(widget['children'], list):
                for i, child in enumerate(widget['children']):
                    if isinstance(child, dict):
                        child_path = f"{widget_path}.children[{i}]"
                        _search_widget(child, child_path)
        
        if isinstance(widget_data, dict):
            _search_widget(widget_data, path_prefix)
        elif isinstance(widget_data, list):
            for i, item in enumerate(widget_data):
                if isinstance(item, dict):
                    item_path = f"{path_prefix}[{i}]"
                    _search_widget(item, item_path)
        
        return script_fields
    
    def _calculate_pod_script_line_offset(self, file_content: str, script_content: str, search_start_line: int = 0, occurrence_index: int = 0) -> int:
        """
        Calculate the line number where script content starts in a Pod file.
        Uses same strategies as PMD files for consistency.
        
        Args:
            file_content: The full source file content
            script_content: The script content to find
            search_start_line: Line number to start searching from (0-based)
            occurrence_index: Which occurrence to find (0 = first, 1 = second, etc.)
            
        Returns:
            Line number (1-based) where the script starts
        """
        if not file_content or not script_content:
            return 1
        
        lines = file_content.split('\n')
        start_index = max(0, search_start_line)
        
        # Strategy 1: For single-line scripts, search for exact match with re-escaped quotes
        if '\n' not in script_content:
            escaped_content = script_content.replace('"', '\\"')
            
            matches_found = 0
            for i in range(0, len(lines)):  # Search from beginning
                if script_content in lines[i] or escaped_content in lines[i]:
                    if matches_found == occurrence_index:
                        return i + 1
                    matches_found += 1
            
            # Fallback: find next <% tag
            for i in range(start_index, len(lines)):
                if '<%' in lines[i]:
                    return i + 1
        
        # Strategy 2: For multiline scripts, use same logic as PMD files
        # (This reuses the PMD calculation logic)
        return self._calculate_script_line_offset(file_content, script_content, search_start_line, occurrence_index)
    
    def find_pod_widgets(self, pod_model: PodModel) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Find all widgets in a Pod template with their paths.
        
        Args:
            pod_model: The Pod model to search
            
        Returns:
            List of tuples containing:
            - widget_path: Path to the widget (e.g., "seed.template.children[0]")
            - widget_data: The widget dictionary
        """
        widgets = []
        
        def _collect_widgets(widget_data: Any, path: str):
            if isinstance(widget_data, dict) and 'type' in widget_data:
                widgets.append((path, widget_data))
                
                # Recursively search children
                if 'children' in widget_data and isinstance(widget_data['children'], list):
                    for i, child in enumerate(widget_data['children']):
                        child_path = f"{path}.children[{i}]"
                        _collect_widgets(child, child_path)
            elif isinstance(widget_data, list):
                for i, item in enumerate(widget_data):
                    item_path = f"{path}[{i}]"
                    _collect_widgets(item, item_path)
        
        if pod_model.seed.template:
            _collect_widgets(pod_model.seed.template, "seed.template")
        
        return widgets
    
    @staticmethod
    def _create_endpoint_message(field_path: str, field_name: str, issue_description: str) -> str:
        """
        Create a human-readable message for endpoint-related issues.
        
        Args:
            field_path: The technical field path (e.g., "outboundEndpoints[5].url")
            field_name: The display name from script field extraction
            issue_description: Description of the issue (e.g., "uses string concatenation")
            
        Returns:
            Human-readable message like "Outbound endpoint 'bpSubmitPOST' uses string concatenation"
        """
        # Extract endpoint name and type from field_name if it follows the pattern
        # Pattern: "inboundEndpoints[1]->name: bpEventStep->url"
        if "->" in field_name and ("inboundEndpoints" in field_name or "outboundEndpoints" in field_name or "seed.endPoints" in field_name):
            try:
                # Extract: "inboundEndpoints[1]->name: bpEventStep->url"
                parts = field_name.split("->")
                if len(parts) >= 3:
                    endpoint_name = parts[1].split(": ")[1]  # Get "bpEventStep" from "name: bpEventStep"
                    field_part = parts[2]  # Get "url"
                    
                    # Determine endpoint type from field_path
                    if "inboundEndpoints" in field_path:
                        endpoint_type = "Inbound"
                    elif "outboundEndpoints" in field_path:
                        endpoint_type = "Outbound"
                    elif "seed.endPoints" in field_path:
                        endpoint_type = "POD"
                    else:
                        endpoint_type = "Endpoint"
                    
                    return f"{endpoint_type} endpoint '{endpoint_name}' {issue_description}"
            except (IndexError, ValueError):
                pass
        
        # Fallback to original field_name if parsing fails
        return f"File section '{field_name}' {issue_description}"
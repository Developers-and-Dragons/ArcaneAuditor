from pydantic import BaseModel, Field, PrivateAttr
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from lark import Tree

if TYPE_CHECKING:
    from file_processing.context_tracker import AnalysisContext

# --- Lazy import for the Lark parser ---
# This avoids a circular dependency if the parser ever needs the models.
_pmd_script_parser = None

def get_pmd_script_parser():
    """Lazily imports and returns the PMD Script parser to avoid circular imports."""
    global _pmd_script_parser
    if _pmd_script_parser is None:
        from .pmd_script_parser import parse_with_preprocessor
        _pmd_script_parser = parse_with_preprocessor
    return _pmd_script_parser

# -----------------------------------------------------------------------------
# 📄 Models for Individual File Types
# -----------------------------------------------------------------------------

class ScriptModel(BaseModel):
    """Represents the structure of a .script file."""
    source: str
    file_path: str = Field(..., exclude=True) # Exclude from exported model data


class OrchestrationModel(BaseModel):
    """Represents the structure of a .orchestration file (Orchestrate flow)."""
    flow_type: str  # e.g. FlowSync, FlowAsync, FlowBusinessProcessTriggered, IntegrationFrameworkTrigger
    id: str
    name: str
    security_domains: Optional[List[str]] = None
    raw_value: Dict[str, Any] = Field(default_factory=dict)  # full _value dict for rules to traverse
    file_path: str = Field(..., exclude=True)
    source_content: str = Field(default="", exclude=True)


class WQLQueryModel(BaseModel):
    """Represents the structure of a .wqlquery file."""
    id: str
    parameters: Optional[List[str]] = Field(default_factory=list)
    query: Optional[str] = None
    offset: Optional[str] = None
    limit: Optional[str] = None
    file_path: str = Field(..., exclude=True)
    source_content: str = Field(default="", exclude=True)

    # Private attribute to store hash-based line mappings (same as PMDModel/PodModel)
    _hash_to_lines: Optional[Dict[str, List[List[int]]]] = PrivateAttr(default=None)

    def set_hash_to_lines_mapping(self, hash_to_lines: Dict[str, List[List[int]]]):
        """Set the hash-based line mappings for precise line number tracking."""
        self._hash_to_lines = hash_to_lines or {}

    def get_script_start_line(self, script_value: str) -> Optional[int]:
        """
        Get the starting line number for a script value using hash-based mapping.

        Mirrors PMDModel.get_script_start_line() so shared script-field extraction works.
        """
        import hashlib

        if not self._hash_to_lines:
            return None

        content_hash = hashlib.sha256(script_value.encode('utf-8')).hexdigest()
        if content_hash in self._hash_to_lines and self._hash_to_lines[content_hash]:
            line_list = self._hash_to_lines[content_hash].pop(0)
            return line_list[0] if line_list else None

        return None

class PMDIncludes(BaseModel):
    scripts: Optional[List[str]] = Field(default_factory=list)

class PMDPresentation(BaseModel):
    attributes: Dict[str, Any] = Field(default_factory=dict)
    title: Dict[str, Any] = Field(default_factory=dict)
    body: Dict[str, Any] = Field(default_factory=dict)
    footer: Dict[str, Any] = Field(default_factory=dict)
    tabs: Optional[List[Dict[str, Any]]] = None

class PMDModel(BaseModel):
    """Represents the structure of a .pmd page file."""
    pageId: str
    securityDomains: Optional[List[str]] = Field(default_factory=list)
    inboundEndpoints: Optional[List[dict]] = Field(default_factory=list)
    outboundEndpoints: Optional[List[dict]] = Field(default_factory=list)
    presentation: PMDPresentation = None
    onLoad: Optional[str] = None
    script: Optional[str] = None
    includes: Optional[PMDIncludes] = None
    file_path: str = Field(..., exclude=True)
    source_content: str = Field(default="", exclude=True)

    # Private attribute to cache the parsed AST of the 'onLoad' script
    _onLoad_ast: Optional[Tree] = PrivateAttr(default=None)
    # Private attribute to cache the parsed AST of the page-level 'script'
    _script_ast: Optional[Tree] = PrivateAttr(default=None)
    # Private attribute to cache extracted script fields
    _cached_script_fields: Optional[List[tuple]] = PrivateAttr(default=None)
    # Private attribute to store line mappings for script fields
    _line_mappings: Optional[Dict[str, List[int]]] = PrivateAttr(default=None)
    # Private attribute to store hash-based line mappings (hash -> list of line ranges)
    _hash_to_lines: Optional[Dict[str, List[List[int]]]] = PrivateAttr(default=None)

    def _parse_script(self, script_content: Optional[str], context: Optional['ProjectContext'] = None) -> Optional[Tree]:
        """A helper method to parse a script string using the custom Lark parser."""
        if not script_content or not script_content.strip():
            return None
        try:
            parser = get_pmd_script_parser()
            return parser(script_content)
        except Exception as e:
            # Failed to parse, log the error if context is available
            if context is not None:
                context.parsing_errors.append(f"{self.file_path}: Script parsing failed - {str(e)}")
            return None

    def get_onLoad_ast(self, context: Optional['ProjectContext'] = None) -> Optional[Tree]:
        """Parses the onLoad script string and caches the result."""
        if self._onLoad_ast is None:
            self._onLoad_ast = self._parse_script(self.onLoad, context)
        return self._onLoad_ast

    def get_script_ast(self, context: Optional['ProjectContext'] = None) -> Optional[Tree]:
        """Parses the page-level script string and caches the result."""
        if self._script_ast is None:
            self._script_ast = self._parse_script(self.script, context)
        return self._script_ast
    
    def set_line_mappings(self, line_mappings: Dict[str, List[int]]):
        """Set the line mappings for script fields."""
        self._line_mappings = line_mappings
    
    def set_hash_to_lines_mapping(self, hash_to_lines: Dict[str, List[List[int]]]):
        """Set the hash-based line mappings for precise line number tracking."""
        self._hash_to_lines = hash_to_lines or {}
    
    def get_script_start_line(self, script_value: str) -> Optional[int]:
        """
        Get the starting line number for a script value using hash-based mapping.
        
        This method accounts for the fact that AST line 1 corresponds to the first
        line of actual code after the <% tag, not the line with the tag itself.
        
        Args:
            script_value: The full script content (including <% and %>)
            
        Returns:
            Line number (1-based) where AST line 1 starts, or None if not found
        """
        import hashlib
        
        if not self._hash_to_lines:
            return None
        
        # The script_value from the parsed JSON has already had \n converted to real newlines
        # But when it was preprocessed, it was still raw with \n in the multiline buffer
        # We need to hash it the same way the preprocessor did
        
        # The preprocessor hashes the content BEFORE json.dumps escaping
        # So we need to reverse that: the script_value is the result of JSON parsing
        # which means it's already unescaped
        
        # For multiline scripts, the preprocessor joined with '\n'.join(multiline_buffer)
        # So we need to hash the script_value as-is (it already has real newlines)
        content_hash = hashlib.sha256(script_value.encode('utf-8')).hexdigest()
        
        # Pop the next unused occurrence
        if content_hash in self._hash_to_lines and self._hash_to_lines[content_hash]:
            line_list = self._hash_to_lines[content_hash].pop(0)
            
            if line_list:
                # Calculate the offset for AST line 1
                # AST line 1 is the first line of code after <%
                # Count newlines from start to the first code after <%
                offset = self._calculate_ast_line_1_offset(script_value, line_list)
                return offset
        
        return None
    
    def _calculate_ast_line_1_offset(self, script_value: str, line_list: List[int]) -> int:
        """
        Calculate the file line number that corresponds to AST line 1.
        
        AST line 1 is the first line of actual code after the <% tag.
        
        Args:
            script_value: The script content (with <% and %>)
            line_list: List of original file line numbers for this script
            
        Returns:
            Line number (1-based) where AST line 1 begins
        """
        # Handle edge cases
        if not script_value:
            return line_list[0] if line_list else 1
        
        if not line_list:
            return 1
        
        # Handle non-script content (no <% wrapper)
        if not script_value.startswith('<%'):
            # Not a script wrapper, AST line 1 is the first line
            return line_list[0]
        
        # Find where the actual code starts after <%
        # Count newlines from start of string to first code
        idx_after_open = 2  # After '<%'
        newline_count = 0
        
        # Skip whitespace and count newlines after <%
        while idx_after_open < len(script_value):
            char = script_value[idx_after_open]
            if char == '\n':
                newline_count += 1
                idx_after_open += 1
            elif char in ' \t\r':
                idx_after_open += 1
            else:
                # Found first non-whitespace character (start of code)
                break
        
        # Handle edge case: script ends immediately after <% (no code)
        if idx_after_open >= len(script_value):
            # Script is just "<%" or "<% " with no actual code
            return line_list[0]
        
        # AST line 1 corresponds to the file line at index newline_count in line_list
        # (if newline_count is 0, it's on the same line as <%, which is line_list[0])
        if newline_count < len(line_list):
            return line_list[newline_count]
        else:
            # Fallback: if we have more newlines than line_list entries,
            # the code starts after all the lines in line_list
            # This shouldn't happen in normal cases, but handle gracefully
            return line_list[-1] if line_list else 1
    
    def get_original_line_number(self, field_path: str, processed_line: int) -> int:
        """
        Get the original line number for a field at a given processed line.
        
        Args:
            field_path: Path to the field (e.g., "onLoad", "endPoints.0.onSend")
            processed_line: Line number in the processed content
            
        Returns:
            Original line number
        """
        if not self._line_mappings or field_path not in self._line_mappings:
            return processed_line
        
        # For now, return the first line of the script field
        # This could be enhanced to map specific lines within the script
        return self._line_mappings[field_path][0] if self._line_mappings[field_path] else processed_line
    
    def get_cached_script_fields(self) -> Optional[List[tuple]]:
        """Get the cached script fields if available."""
        return self._cached_script_fields
    
    def set_cached_script_fields(self, script_fields: List[tuple]):
        """Set the cached script fields."""
        self._cached_script_fields = script_fields

class PodSeed(BaseModel):
    """Represents the seed configuration within a Pod file."""
    parameters: Optional[List[str]] = Field(default_factory=list)
    endPoints: Optional[List[dict]] = Field(default_factory=list)
    template: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # Note: template can contain complex widget structures including:
    # - Simple widgets: {"type": "text", "value": "text"}
    # - Container widgets: {"type": "section", "children": [...]}
    # - FieldSet widgets: {"type": "fieldSet", "children": [...]}
    # - Any widget that can have children arrays with nested widgets
    # Additional seed properties can be added as needed

class PodModel(BaseModel):
    """Represents the structure of a .pod file."""
    podId: str
    seed: PodSeed
    file_path: str = Field(..., exclude=True)
    source_content: str = Field(default="", exclude=True)
    
    # Private attribute to store hash-based line mappings (same as PMDModel)
    _hash_to_lines: Optional[Dict[str, List[List[int]]]] = PrivateAttr(default=None)
    
    def set_hash_to_lines_mapping(self, hash_to_lines: Dict[str, List[List[int]]]):
        """Set the hash-based line mappings for precise line number tracking (same as PMDModel)."""
        self._hash_to_lines = hash_to_lines or {}
    
    def get_script_start_line(self, script_value: str) -> Optional[int]:
        """
        Get the starting line number for a script value using hash-based mapping.
        Same implementation as PMDModel for consistency.
        
        Args:
            script_value: The full script content (including <% and %>)
            
        Returns:
            Line number (1-based) where AST line 1 starts, or None if not found
        """
        import hashlib
        
        if not self._hash_to_lines:
            return None
        
        content_hash = hashlib.sha256(script_value.encode('utf-8')).hexdigest()
        
        # Pop the next unused occurrence
        if content_hash in self._hash_to_lines and self._hash_to_lines[content_hash]:
            line_list = self._hash_to_lines[content_hash].pop(0)
            
            if line_list:
                # Calculate the offset for AST line 1 (same logic as PMDModel)
                offset = self._calculate_ast_line_1_offset(script_value, line_list)
                return offset
        
        return None
    
    def _calculate_ast_line_1_offset(self, script_value: str, line_list: List[int]) -> int:
        """
        Calculate the file line number that corresponds to AST line 1.
        Same implementation as PMDModel.
        
        Args:
            script_value: The script content (with <% and %>)
            line_list: List of original file line numbers for this script
            
        Returns:
            Line number (1-based) where AST line 1 begins
        """
        # Handle edge cases
        if not script_value:
            return line_list[0] if line_list else 1
        
        if not line_list:
            return 1
        
        # Handle non-script content (no <% wrapper)
        if not script_value.startswith('<%'):
            # Not a script wrapper, AST line 1 is the first line
            return line_list[0]
        
        # Find where the actual code starts after <%
        # Count newlines from start of string to first code
        idx_after_open = 2  # After '<%'
        newline_count = 0
        
        # Skip whitespace and count newlines after <%
        while idx_after_open < len(script_value):
            char = script_value[idx_after_open]
            if char == '\n':
                newline_count += 1
                idx_after_open += 1
            elif char in ' \t\r':
                idx_after_open += 1
            else:
                # Found first non-whitespace character (start of code)
                break
        
        # Handle edge case: script ends immediately after <% (no code)
        if idx_after_open >= len(script_value):
            # Script is just "<%" or "<% " with no actual code
            return line_list[0]
        
        # AST line 1 corresponds to the file line at index newline_count in line_list
        # (if newline_count is 0, it's on the same line as <%, which is line_list[0])
        if newline_count < len(line_list):
            return line_list[newline_count]
        else:
            # Fallback: if we have more newlines than line_list entries,
            # the code starts after all the lines in line_list
            # This shouldn't happen in normal cases, but handle gracefully
            return line_list[-1] if line_list else 1
    
    def get_template_widgets(self) -> List[Dict[str, Any]]:
        """
        Recursively extracts all widgets from the template, including nested children.
        Returns a flat list of all widgets found in the template hierarchy.
        """
        widgets = []
        
        def extract_widgets(widget_data):
            if isinstance(widget_data, dict):
                # Add the current widget
                widgets.append(widget_data)
                
                # If it has children, recursively extract from children
                if 'children' in widget_data and isinstance(widget_data['children'], list):
                    for child in widget_data['children']:
                        extract_widgets(child)
            elif isinstance(widget_data, list):
                # If the data is a list, process each item
                for item in widget_data:
                    extract_widgets(item)
        
        if self.seed.template:
            extract_widgets(self.seed.template)
        
        return widgets
    
    def find_widgets_by_type(self, widget_type: str) -> List[Dict[str, Any]]:
        """
        Finds all widgets of a specific type in the template hierarchy.
        
        Args:
            widget_type: The widget type to search for (e.g., 'text', 'section', 'fieldSet')
        
        Returns:
            List of widgets matching the specified type
        """
        all_widgets = self.get_template_widgets()
        return [widget for widget in all_widgets if widget.get('type') == widget_type]
    
    def get_parameter_references(self) -> List[str]:
        """
        Extracts all parameter references (@@param@@) from the template.
        Useful for validating that all referenced parameters are declared.
        """
        import re
        references = set()
        
        def extract_references(obj):
            if isinstance(obj, str):
                # Find all @@param@@ patterns
                matches = re.findall(r'@@(\w+)@@', obj)
                references.update(matches)
            elif isinstance(obj, dict):
                for value in obj.values():
                    extract_references(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_references(item)
        
        if self.seed.template:
            extract_references(self.seed.template)
        
        return list(references)

class AMDRoute(BaseModel):
    pageId: str
    parameters: Optional[List[str]] = Field(default_factory=list)

class AMDModel(BaseModel):
    """Represents the structure of an .amd application definition file."""
    routes: Dict[str, AMDRoute]
    baseUrls: Optional[Dict[str, str]] = Field(default_factory=dict)
    flows: Optional[Dict[str, Any]] = Field(default_factory=dict)
    dataProviders: Optional[List[Dict[str, str]]] = Field(default_factory=list)
    file_path: str = Field(..., exclude=True)
    source_content: str = Field(default="", exclude=True)
    
class SMDModel(BaseModel):
    """Model representing an SMD (Site Model Definition) file."""
    id: str
    applicationId: str
    siteId: str
    languages: List[Dict[str, str]] = Field(default_factory=list)
    siteAuth: Optional[Dict[str, Any]] = None
    errorPageConfigurations: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    file_path: str = Field(..., exclude=True)
    source_content: str = Field(default="", exclude=True)
    
    def get_language_codes(self) -> List[str]:
        """Get list of language codes from the SMD."""
        return [lang.get("code", "") for lang in self.languages if lang.get("code")]
    
    def get_auth_schemes(self) -> List[str]:
        """Get list of authentication schemes."""
        if not self.siteAuth or "authTypes" not in self.siteAuth:
            return []
        return [auth.get("scheme", "") for auth in self.siteAuth["authTypes"] if auth.get("scheme")]
    
    def get_error_pages(self) -> List[Dict[str, str]]:
        """Get list of error page configurations."""
        return [
            {
                "statusCode": config.get("statusCode", ""),
                "pageId": config.get("page", {}).get("id", "") if config.get("page") else ""
            }
            for config in self.errorPageConfigurations
        ]

# -----------------------------------------------------------------------------
# 🗂️ The Central Project Context
# -----------------------------------------------------------------------------

class ProjectContext:
    """A central repository to hold all parsed models from the application."""
    def __init__(self):
        self.pmds: Dict[str, PMDModel] = {}          # Maps pageId to PMDModel
        self.scripts: Dict[str, ScriptModel] = {}    # Maps file name to ScriptModel
        self.amd: AMDModel = None                    # Assumes one .amd file per app
        self.pods: Dict[str, PodModel] = {}          # Maps podId to PodModel
        self.smd: SMDModel = None                    # Assumes one .smd file per app
        self.wqlqueries: Dict[str, WQLQueryModel] = {}  # Maps id to WQLQueryModel
        self.orchestrations: Dict[str, OrchestrationModel] = {}  # Maps id (or name) to OrchestrationModel
        self.parsing_errors: List[str] = []          # To track files that failed validation
        
        # Context tracking for informing users about missing cross-file dependencies
        self.analysis_context: Optional['AnalysisContext'] = None
        
        # Performance optimization: Cache script fields to avoid repeated extraction
        self._cached_pmd_script_fields: Dict[str, List[tuple]] = {}
        self._cached_pod_script_fields: Dict[str, List[tuple]] = {}
        
        # Performance optimization: Cache ASTs to avoid repeated parsing
        self._cached_asts: Dict[str, Tree] = {}  # Maps script content hash to AST

    def get_script_by_name(self, name: str) -> Optional[ScriptModel]:
        """Retrieves a script model by its file name (e.g., 'utils.script')."""
        return self.scripts.get(name)
    
    @property
    def application_id(self) -> Optional[str]:
        """Gets the applicationId from the SMD file if available."""
        if self.smd:
            return self.smd.applicationId
        return None
    
    def register_skipped_check(self, rule_name: str, check_name: str, reason: str) -> None:
        """
        Convenience method for rules to register when they skip a check due to missing context.
        
        Args:
            rule_name: The ID/name of the rule that skipped the check
            check_name: A descriptive name for the check that was skipped
            reason: Human-readable reason why the check was skipped
        """
        if self.analysis_context:
            self.analysis_context.register_skipped_check(rule_name, check_name, reason)

    def get_pmd_by_id(self, page_id: str) -> Optional[PMDModel]:
        """Retrieves a PMD model by its pageId."""
        return self.pmds.get(page_id)
    
    def get_pod_by_id(self, pod_id: str) -> Optional[PodModel]:
        """Retrieves a Pod model by its podId."""
        return self.pods.get(pod_id)
    
    def get_smd(self) -> Optional[SMDModel]:
        """Retrieves the SMD model."""
        return self.smd
    
    def get_cached_pmd_script_fields(self, pmd_id: str) -> Optional[List[tuple]]:
        """Get cached script fields for a PMD model."""
        return self._cached_pmd_script_fields.get(pmd_id)
    
    def set_cached_pmd_script_fields(self, pmd_id: str, script_fields: List[tuple]):
        """Cache script fields for a PMD model."""
        self._cached_pmd_script_fields[pmd_id] = script_fields
    
    def get_cached_pod_script_fields(self, pod_id: str) -> Optional[List[tuple]]:
        """Get cached script fields for a POD model."""
        return self._cached_pod_script_fields.get(pod_id)
    
    def set_cached_pod_script_fields(self, pod_id: str, script_fields: List[tuple]):
        """Cache script fields for a POD model."""
        self._cached_pod_script_fields[pod_id] = script_fields
    
    def get_cached_ast(self, script_content: str) -> Optional[Tree]:
        """Get cached AST for script content."""
        content_hash = hash(script_content)
        return self._cached_asts.get(content_hash)
    
    def set_cached_ast(self, script_content: str, ast: Tree):
        """Cache AST for script content."""
        content_hash = hash(script_content)
        self._cached_asts[content_hash] = ast
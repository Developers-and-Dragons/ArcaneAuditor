"""Base detector class for script analysis."""

import os
from abc import ABC, abstractmethod
from typing import Any, List
from lark import Tree
from .violation import Violation


class ScriptDetector(ABC):
    """
    Base class for script analysis detectors.
    
    LINE NUMBER CALCULATION STANDARD:
    =================================
    
    All script detectors MUST use the standardized formula for line number calculations:
    
        file_line = self.line_offset + ast.line - 1
    
    Where:
    - `self.line_offset`: The file line number where AST line 1 begins (calculated by PMDModel.get_script_start_line())
    - `ast.line`: The line number within the parsed script content (1-based)
    - `file_line`: The actual line number in the source file (1-based)
    
    This formula ensures consistent line number reporting across all detectors and eliminates
    the off-by-1 errors that were previously common.
    
    IMPLEMENTATION REQUIREMENTS:
    ============================
    
    1. Use get_line_number_from_token() for token-based line numbers
    2. Use get_line_from_tree_node() for AST node-based line numbers  
    3. Add debug logging with _debug_line_calc() during development
    4. Never use raw ast.line or token.line without applying the formula
    
    DEBUG LOGGING:
    ==============
    
    Set DEBUG_LINE_NUMBERS=true environment variable to enable detailed line calculation logging.
    This helps verify correct line number calculations during development and debugging.
    
    EXAMPLES:
    =========
    
    # Correct usage:
    line_number = self.get_line_number_from_token(token)
    line_number = self.get_line_from_tree_node(node)
    
    # With debug logging:
    line_number = self.line_offset + ast.line - 1
    self._debug_line_calc(ast.line, self.line_offset, line_number, "context_description")
    
    # Incorrect usage (DO NOT DO THIS):
    line_number = ast.line  # Missing offset calculation
    line_number = token.line  # Missing offset calculation
    """
    
    # Debug flag for line number calculations
    DEBUG_LINE_NUMBERS = os.environ.get('DEBUG_LINE_NUMBERS', 'false').lower() == 'true'
    
    def __init__(self, file_path: str = "", line_offset: int = 1, source_text: str = ""):
        """Initialize detector with file context."""
        self.file_path = file_path
        self.line_offset = line_offset
        self.source_text = source_text  # Store the original source text for physical line counting
        # Cache for function context maps to avoid rebuilding for each violation
        self._function_context_cache = {}
    
    def _debug_line_calc(self, ast_line: int, line_offset: int, result: int, context: str = ""):
        """Helper to log line number calculations."""
        if self.DEBUG_LINE_NUMBERS:
            from utils.console import info
            info(f"[{self.__class__.__name__}] {context}")
            info(f"   ast.line={ast_line}, line_offset={line_offset}")
            info(f"   formula: {line_offset} + {ast_line} - 1 = {result}")
            if hasattr(self, 'file_path'):
                info(f"   file: {self.file_path}")
    
    def detect(self, ast: Any) -> List[Violation]:
        """
        Analyze AST and return list of violations.
        
        Args:
            ast: Parsed AST node
            
        Returns:
            List of Violation objects
        """
        violations = []
        
        # Handle template expressions specially
        if hasattr(ast, 'data') and ast.data == 'template_expression':
            violations.extend(self._detect_template_expression(ast))
        else:
            # Handle regular script analysis
            violations.extend(self._detect_regular_script(ast))
        
        return violations
    
    def _detect_template_expression(self, template_ast: Any) -> List[Violation]:
        """
        Analyze template expression by traversing each script block.
        
        Args:
            template_ast: template_expression AST node
            
        Returns:
            List of Violation objects found in script blocks
        """
        violations = []
        
        if not hasattr(template_ast, 'children'):
            return violations
        
        # Traverse each child of the template expression
        for child in template_ast.children:
            if hasattr(child, 'data') and child.data == 'template_script_block':
                # This is a script block - analyze its AST
                if hasattr(child, 'children') and len(child.children) > 0:
                    script_ast = child.children[0]
                    # Recursively analyze the script block AST
                    violations.extend(self._detect_regular_script(script_ast))
            # Skip template_text nodes - they don't contain script to analyze
        
        return violations
    
    def _detect_regular_script(self, ast: Any) -> List[Violation]:
        """
        Analyze regular script AST (to be implemented by subclasses).
        
        Args:
            ast: Parsed AST node
            
        Returns:
            List of Violation objects
        """
        # This method should be overridden by subclasses
        # For now, return empty list to avoid breaking existing detectors
        return []
    
    def get_line_number(self, node: Any) -> int:
        """Get line number from AST node with offset."""
        from ...common import ASTLineUtils
        return ASTLineUtils.get_line_number(node, self.line_offset)
    
    def get_line_number_from_token(self, token: Any) -> int:
        """Get line number from token with offset using standardized formula."""
        # First try direct token access (most reliable for Lark tokens)
        if hasattr(token, 'line') and token.line is not None:
            # Standard formula: line_offset + ast.line - 1
            result = self.line_offset + token.line - 1
            self._debug_line_calc(token.line, self.line_offset, result, "get_line_number_from_token")
            return result
        elif hasattr(token, 'children'):
            # If token doesn't have line info, search children for line numbers
            for child in token.children:
                if hasattr(child, 'line') and child.line is not None:
                    # Standard formula: line_offset + ast.line - 1
                    result = self.line_offset + child.line - 1
                    self._debug_line_calc(child.line, self.line_offset, result, "get_line_number_from_token (child)")
                    return result
                # Recursively search deeper if needed
                if hasattr(child, 'children'):
                    for grandchild in child.children:
                        if hasattr(grandchild, 'line') and grandchild.line is not None:
                            # Standard formula: line_offset + ast.line - 1
                            result = self.line_offset + grandchild.line - 1
                            self._debug_line_calc(grandchild.line, self.line_offset, result, "get_line_number_from_token (grandchild)")
                            return result
        
        # Default to line_offset if no line info found
        self._debug_line_calc(1, self.line_offset, self.line_offset, "get_line_number_from_token (fallback)")
        return self.line_offset
    
    def get_line_from_tree_node(self, node: Any) -> int:
        """Get line number from a Tree node by finding the first token with line info."""
        if hasattr(node, 'children') and len(node.children) > 0:
            for child in node.children:
                # Check if child has line info directly
                if hasattr(child, 'line') and child.line is not None:
                    result = self.line_offset + child.line - 1
                    self._debug_line_calc(child.line, self.line_offset, result, "get_line_from_tree_node")
                    return result
                # If child is a Tree, recurse into it
                elif hasattr(child, 'children') and len(child.children) > 0:
                    for grandchild in child.children:
                        if hasattr(grandchild, 'line') and grandchild.line is not None:
                            result = self.line_offset + grandchild.line - 1
                            self._debug_line_calc(grandchild.line, self.line_offset, result, "get_line_from_tree_node (grandchild)")
                            return result
        
        # Default to line_offset if no line info found
        self._debug_line_calc(1, self.line_offset, self.line_offset, "get_line_from_tree_node (fallback)")
        return self.line_offset
    
    def get_function_context_for_node(self, node: Any, ast: Any) -> str:
        """Get the function name that contains the given node, or None if not in a function."""
        # Always rebuild function context map to avoid caching issues
        function_contexts = self._build_function_context_map(ast)
        
        # Find the enclosing function name
        return self._get_enclosing_function_name(node, function_contexts)
    
    def _build_function_context_map(self, ast: Any) -> dict:
        """Build a map of AST nodes to their enclosing function names."""
        function_contexts = {}
        
        # Recursively find all function expressions in the AST
        self._find_and_map_functions(ast, function_contexts)
        
        return function_contexts
    
    def _find_and_map_functions(self, node: Any, function_contexts: dict):
        """Recursively find function expressions and map their nodes."""
        if hasattr(node, 'data'):
            # Check if this is a variable statement that contains a function
            if node.data == 'variable_statement' and len(node.children) > 1:
                var_declaration = node.children[1]
                if hasattr(var_declaration, 'data') and var_declaration.data == 'variable_declaration':
                    # Check if this variable declaration contains a function expression
                    for child in var_declaration.children:
                        if hasattr(child, 'data') and child.data in ['function_expression', 'arrow_function_expression']:
                            # Found a function! Get the variable name (function name)
                            if len(var_declaration.children) > 0:
                                var_name_token = var_declaration.children[0]
                                if hasattr(var_name_token, 'value'):
                                    function_name = var_name_token.value
                                    # Map all nodes within this function to the function name
                                    self._map_function_nodes(child, function_name, function_contexts)
        
        # Recursively process children
        if hasattr(node, 'children'):
            for child in node.children:
                self._find_and_map_functions(child, function_contexts)
    
    def _map_function_nodes(self, function_node: Any, function_name: str, function_contexts: dict):
        """Recursively map all nodes within a function to the function name."""
        function_contexts[function_node] = function_name
        
        if hasattr(function_node, 'children'):
            for child in function_node.children:
                # Map both Tree nodes and Token nodes
                function_contexts[child] = function_name
                if hasattr(child, 'data'):  # Tree nodes - recurse
                    self._map_function_nodes(child, function_name, function_contexts)
    
    def _get_enclosing_function_name(self, node: Any, function_contexts: dict) -> str:
        """Find the name of the function that contains the given node."""
        # Check if this node is directly mapped to a function
        if node in function_contexts:
            return function_contexts[node]
        
        # Check if any parent node is mapped to a function
        # Since we don't have parent references, we'll use a different approach
        # We'll check if the node is a descendant of any function node
        # Find the closest (most specific) function by checking depth
        closest_function = None
        closest_depth = float('inf')
        
        for func_node, func_name in function_contexts.items():
            if self._is_descendant(node, func_node):
                # Calculate depth to find the closest function
                depth = self._calculate_descendant_depth(node, func_node)
                if depth < closest_depth:
                    closest_depth = depth
                    closest_function = func_name
        
        return closest_function
    
    def _calculate_descendant_depth(self, node: Any, ancestor: Any) -> int:
        """Calculate the depth of a node within an ancestor (0 = direct child)."""
        if node == ancestor:
            return 0
        
        if hasattr(ancestor, 'children'):
            for child in ancestor.children:
                if hasattr(child, 'data'):  # Only check Tree nodes
                    if self._is_descendant(node, child):
                        return 1 + self._calculate_descendant_depth(node, child)
        
        return float('inf')
    
    def _is_descendant(self, node: Any, ancestor: Any) -> bool:
        """Check if node is a descendant of ancestor."""
        if node == ancestor:
            return True
        
        if hasattr(ancestor, 'children'):
            for child in ancestor.children:
                if hasattr(child, 'data'):  # Only check Tree nodes
                    if self._is_descendant(node, child):
                        return True
        
        return False
    
    def clear_function_context_cache(self):
        """Clear the function context cache. Useful for testing or processing multiple files."""
        self._function_context_cache.clear()
    
    def extract_variable_from_empty_expression(self, node) -> str:
        """
        Extract variable name from empty expression nodes.
        Handles both empty keyword and empty() function cases.
        
        Args:
            node: AST node (empty_expression, not_empty_expression, or empty_function_expression)
            
        Returns:
            Variable name string, or empty string if not found
        """
        if not hasattr(node, 'data') or not hasattr(node, 'children'):
            return ""
        
        # Handle different AST structures for empty keyword vs empty() function
        if node.data == 'empty_function_expression':
            # empty_function_expression: ['empty', '(', 'expression', ')']
            if len(node.children) > 2:
                return self._extract_variable_from_node(node.children[2])
        else:
            # empty_expression: ['empty', 'expression'] 
            if len(node.children) > 1:
                child = node.children[1]
                # Check if it's a parenthesized expression (empty(variable) case)
                if child.data == 'parenthesized_expression' and len(child.children) > 0:
                    # Look inside the parentheses
                    inner_expr = child.children[0]
                    return self._extract_variable_from_node(inner_expr)
                else:
                    return self._extract_variable_from_node(child)
        
        return ""
    
    def extract_variable_from_not_empty_expression(self, node) -> str:
        """
        Extract variable name from not_expression containing empty expressions.
        Handles both !empty variable and !empty(variable) cases.
        
        Args:
            node: AST node (not_expression)
            
        Returns:
            Variable name string, or empty string if not found
        """
        if not hasattr(node, 'data') or not hasattr(node, 'children'):
            return ""
        
        if node.data == 'not_expression':
            if len(node.children) > 0 and isinstance(node.children[0], Tree) and node.children[0].data == 'empty_function_expression':
                # not_expression -> empty_function_expression: ['empty', '(', 'expression', ')']
                empty_func = node.children[0]
                if len(empty_func.children) > 2:
                    return self._extract_variable_from_node(empty_func.children[2])
            elif len(node.children) > 0 and isinstance(node.children[0], Tree) and node.children[0].data == 'empty_expression':
                # not_expression -> empty_expression -> parenthesized_expression (!empty(variable) case)
                empty_expr = node.children[0]
                if len(empty_expr.children) > 1:
                    child = empty_expr.children[1]
                    if child.data == 'parenthesized_expression' and len(child.children) > 0:
                        inner_expr = child.children[0]
                        return self._extract_variable_from_node(inner_expr)
                    else:
                        # not_expression -> empty_expression -> identifier_expression (!empty variable case)
                        return self._extract_variable_from_node(child)
        
        return ""
    
    def _extract_variable_from_node(self, node) -> str:
        """Extract variable name from a node."""
        if not hasattr(node, 'data'):
            return ""
            
        if node.data == 'identifier_expression' and len(node.children) > 0:
            return node.children[0].value if hasattr(node.children[0], 'value') else str(node.children[0])
        elif node.data == 'member_dot_expression':
            # Extract property chain
            return self._extract_property_chain(node) or ""
        
        return ""
    
    def count_physical_lines(self, start_line: int, end_line: int) -> int:
        """
        Count physical lines in the source text between start_line and end_line (inclusive).
        
        This method counts actual lines in the source text, including:
        - All code lines
        - Closing braces
        - Blank lines (unless skip_blank_lines=True)
        - Comments (unless skip_comments=True)
        
        Args:
            start_line: Starting line number (1-based)
            end_line: Ending line number (1-based, inclusive)
            
        Returns:
            The number of lines between start_line and end_line
        """
        if not hasattr(self, 'source_text') or not self.source_text:
            # Fallback: if no source text, just return line span
            return end_line - start_line + 1
        
        # Split source into lines
        source_lines = self.source_text.split('\n')
        
        # Adjust for 0-based indexing (line numbers are 1-based)
        start_idx = start_line - 1
        end_idx = end_line - 1
        
        # Ensure indices are within bounds
        if start_idx < 0:
            start_idx = 0
        if end_idx >= len(source_lines):
            end_idx = len(source_lines) - 1
        
        # Count lines, optionally filtering blank lines and comments
        line_count = 0
        in_block_comment = False
        
        for line_idx in range(start_idx, end_idx + 1):
            line = source_lines[line_idx]
            
            # Check if we should count this line
            should_count = True
            
            # Skip blank lines if flag is set
            if hasattr(self, 'skip_blank_lines') and self.skip_blank_lines:
                if line.strip() == '':
                    should_count = False
            
            # Skip comment lines if flag is set
            if hasattr(self, 'skip_comments') and self.skip_comments and should_count:
                stripped = line.strip()
                
                # Single-line comments
                if stripped.startswith('//'):
                    should_count = False
                # Block comments - track state across lines
                elif '/*' in line or '*/' in line or in_block_comment:
                    # Check if this line starts a new block comment
                    if '/*' in line and '*/' not in line:
                        in_block_comment = True
                        should_count = False
                    # Check if this line ends a block comment
                    elif '*/' in line:
                        in_block_comment = False
                        should_count = False
                    # Check if we're in the middle of a block comment
                    elif in_block_comment:
                        should_count = False
                    # Handle inline block comments that start and end on the same line
                    elif '/*' in line and '*/' in line:
                        should_count = False
            
            if should_count:
                line_count += 1
        
        return line_count
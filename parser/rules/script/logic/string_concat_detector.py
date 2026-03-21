"""String concatenation detection logic for ScriptStringConcatRule."""

from typing import Generator, List
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation
from ...base import Rule


class StringConcatDetector(ScriptDetector):
    """Detects string concatenation using + operator in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect string concatenation using + operator in the AST."""
        # Find all addition expressions in the AST
        addition_expressions = ast.find_data('additive_expression')
        
        # Track reported lines to avoid duplicate violations for nested concatenations
        reported_lines = set()
        
        for add_expr in addition_expressions:
            if self._is_string_concatenation(add_expr):
                line_number = self.get_line_from_tree_node(add_expr)
                
                # Skip if we've already reported a violation on this line
                if line_number in reported_lines:
                    continue
                
                reported_lines.add(line_number)
                
                # Extract the concatenation expression for better error message
                concat_text = self._extract_expression_text(add_expr)
                
                # Check if this string concatenation is inside a function
                function_name = self.get_function_context_for_node(add_expr, ast)
                
                # Create better message using the utility method
                # Extract field_path from field_name if it follows the pattern
                field_path = ""
                if "->" in field_name and ("inboundEndpoints" in field_name or "outboundEndpoints" in field_name or "seed.endPoints" in field_name):
                    # Pattern: "inboundEndpoints[1]->name: bpEventStep->url"
                    # Extract the endpoint array part
                    parts = field_name.split("->")
                    if len(parts) >= 2:
                        field_path = parts[0]  # Get "inboundEndpoints[1]"
                
                # Use the utility method to create a better message
                if function_name:
                    issue_description = f"uses string concatenation with + operator in function '{function_name}': '{concat_text}'. Consider using PMD template strings with backticks and {{{{ }}}} syntax instead (e.g., `Hello {{{{name}}}}!`)."
                else:
                    issue_description = f"uses string concatenation with + operator: '{concat_text}'. Consider using PMD template strings with backticks and {{{{ }}}} syntax instead (e.g., `Hello {{{{name}}}}!`)."
                message = Rule._create_endpoint_message(field_path, field_name, issue_description)
                
                yield Violation(
                    message=message,
                    line=line_number
                )
    
    def _is_string_concatenation(self, add_expr: Tree) -> bool:
        """Check if an addition expression is actually string concatenation."""
        if not isinstance(add_expr, Tree) or add_expr.data != 'additive_expression':
            return False
        
        # Check if any operand involves strings
        # The AST structure shows that additive expressions can have multiple operands
        # when there are chained + operations like "a" + b + "c"
        for operand in add_expr.children:
            if self._involves_string(operand):
                return True
            # Recursively check if any operand is itself a string concatenation
            if isinstance(operand, Tree) and self._is_string_concatenation(operand):
                return True
        
        return False
    
    def _involves_string(self, node) -> bool:
        """Check if a node involves string operations."""
        if not isinstance(node, Tree):
            return False
        
        # Check if it's a string literal
        if node.data == 'literal_expression':
            if len(node.children) > 0:
                child = node.children[0]
                if hasattr(child, 'value') and isinstance(child.value, str) and child.value.startswith(('"', "'")):
                    return True
        
        # Check if it's a template literal (backticks)
        if node.data == 'literal_expression':
            if len(node.children) > 0:
                child = node.children[0]
                if hasattr(child, 'value') and isinstance(child.value, str) and child.value.startswith('`'):
                    return True
        
        # Check if it's a POD parameter (valid in POD context)
        if node.data == 'pod_parameter_expression':
            return True
        
        # Recursively check child nodes for string operations
        for child in node.children:
            if isinstance(child, Tree) and self._involves_string(child):
                return True
        
        return False
    
    def _extract_expression_text(self, node: Tree) -> str:
        """
        Extract readable text representation of an expression from AST.
        
        Preserves operators (+, .) and proper expression structure.
        """
        if not isinstance(node, Tree):
            if hasattr(node, 'value'):
                return str(node.value)
            return str(node)
        
        # Handle additive expressions: a + b + c
        if node.data == 'additive_expression':
            parts = []
            for i, child in enumerate(node.children):
                if i > 0:
                    parts.append(' + ')
                parts.append(self._extract_expression_text(child) if isinstance(child, Tree) 
                           else str(child.value) if hasattr(child, 'value') 
                           else str(child))
            return ''.join(parts)
        
        # Handle simple literal values
        elif node.data == 'literal_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                return node.children[0].value
        
        # Handle simple identifiers
        elif node.data == 'identifier_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                return node.children[0].value
        
        # Handle POD parameters
        elif node.data == 'pod_parameter_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                return node.children[0].value
        
        # Handle member expressions: obj.property
        elif node.data in ['member_dot_expression', 'member_expression', 'member_bracket_expression']:
            parts = []
            for i, child in enumerate(node.children):
                if i > 0:
                    parts.append('.')
                parts.append(self._extract_expression_text(child) if isinstance(child, Tree)
                           else str(child.value) if hasattr(child, 'value')
                           else str(child))
            return ''.join(parts)
        
        # Default: concatenate all child text
        parts = []
        for child in node.children:
            if hasattr(child, 'value'):
                parts.append(str(child.value))
            elif isinstance(child, Tree):
                parts.append(self._extract_expression_text(child))
        
        return ''.join(parts) if parts else str(node.data)

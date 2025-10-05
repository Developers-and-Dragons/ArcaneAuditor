"""Console log detection logic for ScriptConsoleLogRule."""

from typing import Generator, List
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class ConsoleLogDetector(ScriptDetector):
    """Detects console method calls in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
        self.console_methods = {'info', 'warn', 'error', 'debug'}
    
    def detect(self, ast: Tree, field_name: str) -> Generator[Violation, None, None]:
        """Detect console method calls in the AST."""
        # Find all member_dot_expression nodes (e.g., console.debug, console.info)
        member_expressions = ast.find_data('member_dot_expression')
        
        for member_expr in member_expressions:
            if len(member_expr.children) >= 2:
                object_node = member_expr.children[0]
                method_node = member_expr.children[1]
                
                # Check if it's a console method call
                if self._is_console_method_call(object_node, method_node):
                    method_name = self._extract_method_name(method_node)
                    line_number = self.get_line_from_tree_node(member_expr)
                    
                    yield Violation(
                        message=f"File section '{field_name}' contains console.{method_name} statement. Remove debug statements from production code.",
                        line=line_number
                    )
    
    def _is_console_method_call(self, object_node, method_node) -> bool:
        """Check if the member expression is a console method call."""
        # Check if the object is 'console'
        if (hasattr(object_node, 'children') and 
            len(object_node.children) > 0 and
            hasattr(object_node.children[0], 'value') and
            object_node.children[0].value == 'console'):
            
            # Check if the method is a known console method
            method_name = self._extract_method_name(method_node)
            return method_name in self.console_methods
        
        return False
    
    def _extract_method_name(self, method_node) -> str:
        """Extract the method name from the method node."""
        if hasattr(method_node, 'value'):
            return method_node.value
        elif hasattr(method_node, 'children') and len(method_node.children) > 0:
            child = method_node.children[0]
            if hasattr(child, 'value'):
                return child.value
        else:
            # The method node might be a token without children
            return str(method_node)
        return str(method_node)

"""Detector for unused variables in script code."""

from typing import Any, List, Set, Dict
from ...script.shared import ScriptDetector, Violation
from ...common import ASTLineUtils


class UnusedVariableDetector(ScriptDetector):
    """Detects unused variables in script code with scope awareness."""

    def __init__(self, file_path: str = "", line_offset: int = 1, is_global_scope: bool = False, global_functions: Set[str] = None):
        """Initialize detector with file context and scope information."""
        super().__init__(file_path, line_offset)
        self.is_global_scope = is_global_scope
        self.global_functions = global_functions or set()

    def detect(self, ast: Any, field_name: str = "") -> List[Violation]:
        """
        Analyze AST and return list of unused variable violations.
        
        Args:
            ast: Parsed AST node
            field_name: Name of the field being analyzed
            
        Returns:
            List of Violation objects
        """
        violations = []
        
        # Handle template expressions specially
        if hasattr(ast, 'data') and ast.data == 'template_expression':
            # Analyze each script block in the template expression
            if hasattr(ast, 'children'):
                for child in ast.children:
                    if hasattr(child, 'data') and child.data == 'template_script_block':
                        # This is a script block - analyze its AST
                        if hasattr(child, 'children') and len(child.children) > 0:
                            script_ast = child.children[0]
                            # Recursively analyze the script block AST
                            violations.extend(self.detect(script_ast, field_name))
            return violations
        
        # Handle regular script analysis
        # Analyze the script with scope awareness
        scope_analysis = self._analyze_script_scope(ast, self.is_global_scope, self.global_functions)
        
        # Check for unused variables in each scope
        for scope_info in scope_analysis['scopes']:
            scope_type = scope_info['type']
            scope_name = scope_info['name']
            declared_vars = scope_info['declared_vars']
            used_vars = scope_info['used_vars']
            
            # Check for unused variables in this scope
            for var_name, var_info in declared_vars.items():
                if var_name not in used_vars:
                    # Skip function declarations - they're handled by ScriptUnusedFunctionRule
                    if var_info.get('is_function', False):
                        continue
                    
                    # Skip variables that are used in other scopes (global scope variables)
                    if scope_type == 'global' and var_name in scope_analysis['global_used_vars']:
                        continue
                    
                    # Create violation with context information
                    if scope_type == 'function':
                        message = f"Unused variable '{var_name}' in function '{scope_name}'"
                    else:
                        # Use field_name for better context instead of generic scope type
                        if field_name and field_name != 'script':
                            message = f"Unused variable '{var_name}' in {field_name}"
                        else:
                            message = f"Unused variable '{var_name}' in script"
                    
                    violations.append(Violation(
                        message=message,
                        line=self.get_line_from_tree_node(var_info['node']),
                        metadata={
                            'variable_name': var_name,
                            'scope_type': scope_type,
                            'scope_name': scope_name
                        }
                    ))
        
        return violations

    def _analyze_script_scope(self, ast: Any, is_global_scope: bool, global_functions: Set[str]) -> Dict:
        """Analyze script scope and variable usage."""
        scope_analysis = {
            'scopes': [],
            'global_used_vars': set()
        }
        
        # Find all scopes in the script
        scopes = self._find_scopes(ast, is_global_scope, global_functions)
        scope_analysis['scopes'] = scopes
        
        # Collect all variables used across all scopes
        for scope in scopes:
            scope_analysis['global_used_vars'].update(scope['used_vars'])
        
        return scope_analysis

    def _find_scopes(self, ast: Any, is_global_scope: bool, global_functions: Set[str]) -> List[Dict]:
        """Find all scopes in the script."""
        scopes = []
        
        # Always analyze the top-level scope (whether it's global script or onSend/onLoad/etc.)
        # The is_global_scope parameter just determines the scope type name
        scope_type = 'global' if is_global_scope else 'script'
        top_level_scope = self._analyze_scope(ast, scope_type, scope_type, global_functions)
        scopes.append(top_level_scope)
        
        # Function scopes - look for variable statements that contain function expressions
        for node in ast.find_data('variable_statement'):
            # Check if this variable statement contains a function expression
            function_expr = None
            function_name = None
            
            for child in node.children:
                if hasattr(child, 'data') and child.data == 'variable_declaration':
                    # Get the variable name (function name)
                    if len(child.children) > 0:
                        var_name_token = child.children[0]
                        if hasattr(var_name_token, 'value'):
                            function_name = var_name_token.value
                    
                    # Check if this variable declaration contains a function expression
                    for grandchild in child.children:
                        if hasattr(grandchild, 'data') and grandchild.data == 'function_expression':
                            function_expr = grandchild
                            break
            
            if function_expr and function_name:
                function_scope = self._analyze_scope(function_expr, 'function', function_name, global_functions)
                scopes.append(function_scope)
        
        return scopes

    def _analyze_scope(self, ast: Any, scope_type: str, scope_name: str, global_functions: Set[str]) -> Dict:
        """Analyze a specific scope for variable declarations and usage."""
        declared_vars = {}
        used_vars = set()
        
        if scope_type == 'global':
            # For global scope, only look for top-level variable statements
            # that are not inside function expressions
            for node in ast.find_data('variable_statement'):
                # Check if this variable statement is at the top level
                # (not inside a function_expression)
                if self._is_top_level_variable_statement(node, ast):
                    var_name = self._get_variable_name_from_statement(node)
                    if var_name:
                        # Check if this variable statement contains a function expression
                        is_function = self._contains_function_expression(node)
                        declared_vars[var_name] = {
                            'node': node,
                            'is_function': is_function
                        }
        else:
            # For function scope, look for variable statements within the function
            # but exclude those that are inside nested functions
            for node in ast.find_data('variable_statement'):
                # Only include variable statements that are direct children of this function
                # (not nested inside other function expressions)
                if self._is_direct_child_of_function(node, ast):
                    var_name = self._get_variable_name_from_statement(node)
                    if var_name:
                        declared_vars[var_name] = {
                            'node': node,
                            'is_function': False
                        }
        
        # Find function declarations within this scope
        for node in ast.find_data('function_expression'):
            func_name = self._get_function_name(node)
            if func_name:
                declared_vars[func_name] = {
                    'node': node,
                    'is_function': True
                }
        
        # Find variable usage
        for node in ast.find_data('identifier_expression'):
            var_name = self._get_identifier_name(node)
            if var_name:
                used_vars.add(var_name)
        
        # Find variable usage in template literals
        # Template literals are parsed as literal_expression nodes containing TEMPLATE_LITERAL tokens
        for node in ast.find_data('literal_expression'):
            if hasattr(node, 'children') and node.children:
                # Check if this literal_expression contains a TEMPLATE_LITERAL token
                for child in node.children:
                    if hasattr(child, 'type') and child.type == 'TEMPLATE_LITERAL':
                        template_vars = self._extract_variables_from_template(child)
                        used_vars.update(template_vars)
                        break
        
        # Also check for template_literal_expression nodes (if preprocessed)
        for node in ast.find_data('template_literal_expression'):
            template_vars = self._extract_variables_from_template_expression(node)
            used_vars.update(template_vars)
        
        # Add global functions to used vars (they're available in all scopes)
        used_vars.update(global_functions)
        
        return {
            'type': scope_type,
            'name': scope_name,
            'declared_vars': declared_vars,
            'used_vars': used_vars
        }

    def _contains_function_expression(self, node: Any) -> bool:
        """Check if a variable statement contains a function expression."""
        for child in node.children:
            if hasattr(child, 'data') and child.data == 'variable_declaration':
                for grandchild in child.children:
                    if hasattr(grandchild, 'data') and grandchild.data == 'function_expression':
                        return True
        return False

    def _is_top_level_variable_statement(self, node: Any, root_ast: Any) -> bool:
        """Check if a variable statement is at the top level (not inside a function)."""
        # For our simple test case, if the root is a variable_statement,
        # then this node is the root itself, so it's top-level
        if node == root_ast:
            return True
        
        # Check if this node is a direct child of the root
        for child in root_ast.children:
            if child == node:
                return True
        
        return False

    def _is_direct_child_of_function(self, node: Any, function_ast: Any) -> bool:
        """Check if a variable statement is a direct child of the function (not nested in other functions)."""
        # Find the function body and check if the variable statement is directly within it
        # Look for the function body (block_statement) within the function
        for block_node in function_ast.find_data('block_statement'):
            # Check if this variable statement is a direct child of the function body
            if hasattr(block_node, 'children'):
                for child in block_node.children:
                    if child == node:
                        # Found the variable statement as a direct child of the function body
                        return True
        
        # If we didn't find it as a direct child of any block_statement in the function,
        # it might be nested inside another function
        return False

    def _get_variable_name_from_statement(self, node: Any) -> str:
        """Extract variable name from a variable statement node."""
        if hasattr(node, 'children') and len(node.children) > 1:
            # The second child should be the variable_declaration
            var_decl_node = node.children[1]
            if hasattr(var_decl_node, 'children') and len(var_decl_node.children) > 0:
                var_name_token = var_decl_node.children[0]
                if hasattr(var_name_token, 'value'):
                    return var_name_token.value
        return ""

    def _get_variable_name(self, node: Any) -> str:
        """Extract variable name from a variable declaration node."""
        if hasattr(node, 'children') and node.children:
            var_node = node.children[0]
            if hasattr(var_node, 'children') and var_node.children:
                identifier = var_node.children[0]
                if hasattr(identifier, 'value'):
                    return identifier.value
        return ""

    def _get_function_name(self, node: Any) -> str:
        """Extract function name from a function expression node."""
        # The function name is not in the function_expression node itself,
        # but in the parent variable_declaration node. We need to traverse up
        # to find the variable declaration that contains this function.
        # For now, return empty string - function names will be handled differently
        return ""

    def _get_identifier_name(self, node: Any) -> str:
        """Extract identifier name from an identifier expression node."""
        if hasattr(node, 'children') and node.children:
            identifier = node.children[0]
            if hasattr(identifier, 'value'):
                return identifier.value
        return ""
    
    def _extract_variables_from_template(self, token: Any) -> Set[str]:
        """
        Extract variable names from template literal token.
        
        PMD Script uses {{expression}} syntax for template interpolations.
        This method parses the template literal token value to find variable usage.
        
        Args:
            token: A TEMPLATE_LITERAL token with a value like `The number is {{foo}}`
        """
        variables = set()
        
        # Get the template literal content from the token value
        if not hasattr(token, 'value'):
            return variables
        
        template_content = token.value
        
        # Remove the backticks if present
        if template_content.startswith('`') and template_content.endswith('`'):
            template_content = template_content[1:-1]
        
        if not template_content:
            return variables
        
        # Use regex to find {{...}} interpolation blocks
        import re
        interpolation_pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(interpolation_pattern, template_content)
        
        for match in matches:
            # Extract identifiers from the interpolation content
            # Handle cases like: variable, obj.prop, namespace:func
            interpolation_content = match.strip()
            
            # Split by common operators to find identifiers
            # This is a simple approach - more sophisticated parsing would require grammar changes
            parts = re.split(r'[+\-*/=<>!&|?:,;()\[\]{}.\s]+', interpolation_content)
            
            for part in parts:
                part = part.strip()
                # Check if it looks like a variable name (alphanumeric, underscore, no spaces)
                if part and re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', part):
                    variables.add(part)
        
        return variables
    
    def _extract_variables_from_template_expression(self, node: Any) -> Set[str]:
        """
        Extract variable names from template_literal_expression nodes (preprocessed template literals).
        
        Template literal expressions have template_interpolation children that contain
        the actual expressions with identifier_expression nodes.
        
        Args:
            node: A template_literal_expression Tree node
        """
        variables = set()
        
        if not hasattr(node, 'children'):
            return variables
        
        # Look for template_interpolation nodes
        for child in node.children:
            if hasattr(child, 'data') and child.data == 'template_interpolation':
                # Extract identifiers from the interpolation expression
                if hasattr(child, 'children') and child.children:
                    expr_node = child.children[0]
                    # Recursively find all identifier_expression nodes in the interpolation
                    for identifier_node in expr_node.find_data('identifier_expression'):
                        var_name = self._get_identifier_name(identifier_node)
                        if var_name:
                            variables.add(var_name)
        
        return variables

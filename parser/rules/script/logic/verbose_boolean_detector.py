"""Verbose boolean detection logic for ScriptVerboseBooleanCheckRule."""

from typing import Generator, Dict, Any, Optional
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class VerboseBooleanDetector(ScriptDetector):
    """Detects overly verbose boolean checks in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
        self._original_script_content = ""
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect overly verbose boolean patterns in the AST."""
        # Find verbose boolean patterns in if statements and ternary expressions
        yield from self._find_verbose_if_statements(ast, field_name)
        yield from self._find_verbose_ternary_expressions(ast, field_name)
    
    def set_original_content(self, content: str):
        """Set the original script content for operator detection."""
        self._original_script_content = content
    
    def _find_verbose_if_statements(self, ast: Tree, field_name: str):
        """Find verbose boolean patterns in if statements."""
        # Find all if_statement nodes in the AST
        if_statements = ast.find_data('if_statement')
        for if_stmt in if_statements:
            verbose_info = self._analyze_if_statement_for_verbosity(if_stmt)
            if verbose_info:
                # Get line number from the if statement
                line_number = self.get_line_from_tree_node(if_stmt)

                # Check if this verbose boolean check is inside a function
                function_name = self.get_function_context_for_node(if_stmt, ast)

                if function_name:
                    message = f"File section '{field_name}' has verbose boolean check in function '{function_name}': '{verbose_info['pattern']}'. Consider simplifying to '{verbose_info['suggestion']}'."
                else:
                    message = f"File section '{field_name}' has verbose boolean check: '{verbose_info['pattern']}'. Consider simplifying to '{verbose_info['suggestion']}'."

                # For if-statements, a substring swap requires a structural
                # rewrite: replace the whole `if/else` block with `return X;`
                # so the result is grammatical at the statement boundary.
                target_text, swap_replacement = self._build_substring_swap(
                    if_stmt, structural_replacement=f"return {verbose_info['suggestion']};"
                )
                yield Violation(
                    message=message,
                    line=line_number,
                    suggested_replacement=swap_replacement if target_text else verbose_info['suggestion'],
                    target_text=target_text,
                    replacement_context="substring" if target_text else None,
                )

    def _find_verbose_ternary_expressions(self, ast: Tree, field_name: str):
        """Find verbose boolean patterns in ternary expressions."""
        # Find all ternary_expression nodes in the AST (including nested ones)
        ternary_expressions = ast.find_data('ternary_expression')
        for ternary_expr in ternary_expressions:
            verbose_info = self._analyze_ternary_expression_for_verbosity(ternary_expr)
            if verbose_info:
                # Get line number from the ternary expression
                line_number = self.get_line_from_tree_node(ternary_expr)

                # Check if this verbose boolean check is inside a function
                function_name = self.get_function_context_for_node(ternary_expr, ast)

                if function_name:
                    message = f"File section '{field_name}' has verbose boolean check in function '{function_name}': '{verbose_info['pattern']}'. Consider simplifying to '{verbose_info['suggestion']}'."
                else:
                    message = f"File section '{field_name}' has verbose boolean check: '{verbose_info['pattern']}'. Consider simplifying to '{verbose_info['suggestion']}'."

                # Ternary is an expression — the suggestion (`x` / `!x`)
                # substitutes cleanly for the entire ternary text.
                target_text, _ = self._build_substring_swap(ternary_expr)
                yield Violation(
                    message=message,
                    line=line_number,
                    suggested_replacement=verbose_info['suggestion'],
                    target_text=target_text,
                    replacement_context="substring" if target_text else None,
                )

    def _build_substring_swap(self, node, structural_replacement: str = None):
        """Return (target_text, structural_replacement) suitable for a substring
        swap, or (None, None) if the slice would be unsafe.

        Uses Lark's propagated positions to slice the literal source from
        ``self.source_text`` (the stripped script content). Skips enrichment
        when:
          - position info is unavailable on the AST node, or
          - the slice contains characters that JSON-encoding would have
            transformed (``"`` or ``\\``). When the script lives inside a
            PMD/POD JSON string those would not appear verbatim in the source
            file, so a substring search would fail.
        """
        if not self.source_text:
            return None, None
        meta = getattr(node, 'meta', None)
        if meta is None or getattr(meta, 'empty', True):
            return None, None
        start = getattr(meta, 'start_pos', None)
        end = getattr(meta, 'end_pos', None)
        if start is None or end is None or end <= start:
            return None, None
        slice_text = self.source_text[start:end]
        if '"' in slice_text or '\\' in slice_text:
            return None, None
        return slice_text, structural_replacement
    
    def _analyze_if_statement_for_verbosity(self, if_node):
        if not hasattr(if_node, 'children') or len(if_node.children) < 5:
            return None
        
        # Based on actual AST structure: [IF, condition, then_statement, ELSE, else_statement]
        condition = if_node.children[1]  # equality_expression
        then_statement = if_node.children[2]  # return_statement
        else_statement = if_node.children[4] if len(if_node.children) > 4 else None  # return_statement
        
        # Check if this is a verbose boolean pattern
        return self._check_verbose_boolean_condition(condition, then_statement, else_statement)
    
    def _analyze_ternary_expression_for_verbosity(self, ternary_node):
        """Analyze a ternary expression to see if it's a verbose boolean pattern."""
        if not hasattr(ternary_node, 'children') or len(ternary_node.children) < 3:
            return None
        
        # Get condition, true_value, and false_value
        condition = ternary_node.children[0]
        true_value = ternary_node.children[1]
        false_value = ternary_node.children[2]
        
        # Check if this is a verbose boolean pattern
        return self._check_verbose_ternary_condition(condition, true_value, false_value)
    
    def _check_verbose_boolean_condition(self, condition, then_stmt, else_stmt):
        """Check if condition + then/else statements form a verbose boolean pattern."""
        # Extract the condition pattern
        condition_info = self._extract_condition_info(condition)
        if not condition_info:
            return None
        
        # Check if then and else statements are simple return statements
        then_return = self._extract_simple_return_value(then_stmt)
        else_return = self._extract_simple_return_value(else_stmt)
        
        if then_return is None or else_return is None:
            return None
        
        # Check for verbose patterns
        return self._check_verbose_pattern(condition_info, then_return, else_return, "if")
    
    def _check_verbose_ternary_condition(self, condition, true_value, false_value):
        """Check if ternary condition + values form a verbose boolean pattern."""
        # Extract the condition pattern
        condition_info = self._extract_condition_info(condition)
        if not condition_info:
            return None
        
        # Check if true and false values are boolean literals
        true_literal = self._extract_boolean_literal(true_value)
        false_literal = self._extract_boolean_literal(false_value)
        
        if true_literal is None or false_literal is None:
            return None
        
        # Check for verbose patterns
        return self._check_verbose_pattern(condition_info, true_literal, false_literal, "ternary")
    
    def _check_verbose_pattern(self, condition_info, true_return, false_return, pattern_type="if"):
        """Check for verbose boolean patterns and return suggestion."""
        variable = condition_info['variable']
        operator = condition_info['operator']
        comparison = condition_info['comparison']
        
        # Only check for verbose patterns where we return boolean literals
        if true_return not in ['true', 'false'] or false_return not in ['true', 'false']:
            return None
        
        # Determine if this is a verbose pattern and what the suggestion should be
        if true_return == 'true' and false_return == 'false':
            # Pattern: if(condition) return true else return false
            # Suggestion: just the condition
            suggestion = variable
        elif true_return == 'false' and false_return == 'true':
            # Pattern: if(condition) return false else return true  
            # Suggestion: negated condition
            suggestion = f"!{variable}"
        else:
            # Not a verbose boolean pattern
            return None
        
        # Generate the pattern description based on type
        if pattern_type == "ternary":
            pattern = f"{variable} ? {true_return} : {false_return}"
        else:
            pattern = f"if({variable}) return {true_return} else return {false_return}"
        
        return {
            'pattern': pattern,
            'suggestion': suggestion
        }
    
    def _extract_condition_info(self, condition_node):
        """Extract information about a comparison condition."""
        if not hasattr(condition_node, 'data'):
            return None
        
        # Handle parenthesized expressions by extracting the inner expression
        if condition_node.data == 'parenthesized_expression':
            if len(condition_node.children) > 0:
                # Extract the inner expression from the parentheses
                inner_expression = condition_node.children[0]
                return self._extract_condition_info(inner_expression)
        
        # Handle simple identifier expressions (for ternary conditions)
        if condition_node.data == 'identifier_expression':
            if len(condition_node.children) > 0 and hasattr(condition_node.children[0], 'value'):
                variable_name = condition_node.children[0].value
                return {
                    'variable': variable_name,
                    'operator': 'direct',
                    'comparison': 'boolean_value'
                }
        
        # Handle function calls that return boolean values (like empty())
        if condition_node.data == 'call_expression':
            function_name = self._extract_function_name(condition_node)
            if function_name in ['empty', 'notEmpty', 'hasValue', 'isNull', 'isNotNull']:
                return {
                    'variable': self._extract_function_call_string(condition_node),
                    'operator': 'function_call',
                    'comparison': 'boolean_function'
                }
        
        # Handle PMD-specific expressions that return boolean values
        if condition_node.data == 'empty_expression':
            if len(condition_node.children) > 1:
                # Extract the argument to empty (without parentheses)
                argument = condition_node.children[1]
                argument_str = self._extract_expression_string(argument)
                return {
                    'variable': f"empty {argument_str}",
                    'operator': 'function_call',
                    'comparison': 'boolean_function'
                }
        
        if condition_node.data == 'empty_function_expression':
            if len(condition_node.children) > 2:
                # Extract the argument to empty() (with parentheses)
                argument = condition_node.children[2]
                argument_str = self._extract_expression_string(argument)
                return {
                    'variable': f"empty({argument_str})",
                    'operator': 'function_call',
                    'comparison': 'boolean_function'
                }
        
        if condition_node.data == 'equality_expression':
            if len(condition_node.children) >= 2:
                left = condition_node.children[0]
                right = condition_node.children[1]
                
                # Extract variable name from left side
                variable_name = self._extract_identifier_name(left)
                if not variable_name:
                    return None
                
                # Extract comparison value from right side
                comparison_value = self._extract_boolean_literal(right)
                if comparison_value is None:
                    return None
                
                # Detect the actual operator by examining the source content
                operator_str = self._detect_operator_from_source(condition_node, variable_name, comparison_value)
                
                return {
                    'variable': variable_name,
                    'operator': operator_str,
                    'comparison': comparison_value
                }
        
        return None
    
    def _extract_identifier_name(self, node):
        """Extract identifier name from a node."""
        if hasattr(node, 'data') and node.data == 'identifier_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                return node.children[0].value
        return None
    
    def _extract_function_name(self, node):
        """Extract function name from a call expression node."""
        if hasattr(node, 'data') and node.data == 'call_expression':
            if len(node.children) > 0:
                function_node = node.children[0]
                if hasattr(function_node, 'data') and function_node.data == 'identifier_expression':
                    if len(function_node.children) > 0 and hasattr(function_node.children[0], 'value'):
                        return function_node.children[0].value
        return None
    
    def _extract_function_call_string(self, node):
        """Extract the full function call string for display purposes."""
        if hasattr(node, 'data') and node.data == 'call_expression':
            if len(node.children) > 0:
                function_node = node.children[0]
                if hasattr(function_node, 'data') and function_node.data == 'identifier_expression':
                    if len(function_node.children) > 0 and hasattr(function_node.children[0], 'value'):
                        function_name = function_node.children[0].value
                        # For now, just return the function name. In a more sophisticated implementation,
                        # we could reconstruct the full call with arguments
                        return f"{function_name}(...)"
        return None
    
    def _extract_expression_string(self, node):
        """Extract a string representation of an expression for display purposes."""
        if hasattr(node, 'data'):
            if node.data == 'member_dot_expression':
                if len(node.children) >= 2:
                    left = self._extract_expression_string(node.children[0])
                    # The second child might be a token (leaf) or a node
                    if hasattr(node.children[1], 'value'):
                        right = node.children[1].value
                    else:
                        right = self._extract_expression_string(node.children[1])
                    return f"{left}.{right}"
            elif node.data == 'identifier_expression':
                if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                    return node.children[0].value
            elif node.data == 'literal_expression':
                if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                    return str(node.children[0].value)
            elif node.data == 'call_expression':
                if len(node.children) > 0:
                    function_name = self._extract_function_name(node)
                    if function_name:
                        return f"{function_name}(...)"
            elif node.data == 'parenthesized_expression':
                if len(node.children) > 0:
                    return f"({self._extract_expression_string(node.children[0])})"
        return "..."
    
    def _extract_boolean_literal(self, node):
        """Extract boolean literal value from a node."""
        # Check if it's a literal_expression with boolean value
        if hasattr(node, 'data') and node.data == 'literal_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                value = node.children[0].value
                if value in ['true', 'false']:
                    return value
        
        # Check if it's an identifier_expression with boolean value (true/false can be identifiers)
        if hasattr(node, 'data') and node.data == 'identifier_expression':
            if len(node.children) > 0 and hasattr(node.children[0], 'value'):
                value = node.children[0].value
                if value in ['true', 'false']:
                    return value
                    
        return None
    
    def _extract_simple_return_value(self, stmt_node):
        """Extract simple return value from a statement."""
        if not hasattr(stmt_node, 'data'):
            return None
        
        if stmt_node.data == 'return_statement':
            if len(stmt_node.children) > 1:
                return_node = stmt_node.children[1]  # The actual return value
                return self._extract_boolean_literal(return_node)
        
        elif stmt_node.data == 'statement_list':
            # Handle statement lists - look for the first non-empty statement
            if len(stmt_node.children) > 0:
                for child in stmt_node.children:
                    if hasattr(child, 'data') and child.data != 'empty_statement':
                        return self._extract_simple_return_value(child)
        
        elif stmt_node.data == 'expression_statement':
            # Handle expression statements like "true;" or "false;"
            if len(stmt_node.children) > 0:
                return self._extract_boolean_literal(stmt_node.children[0])
        
        # Direct boolean literal (like "true;" or "false;")
        return self._extract_boolean_literal(stmt_node)
    
    def _detect_operator_from_source(self, condition_node, variable_name, comparison_value):
        """Detect the actual operator used in the source by examining the original script content."""
        import re
        
        if not self._original_script_content:
            return "=="  # Default fallback
        
        # Create a regex pattern to find the comparison in the source
        # Look for patterns like "variable == true" or "variable != true"
        pattern = rf'{re.escape(variable_name)}\s*([!=]+)\s*{re.escape(comparison_value)}'
        
        matches = re.findall(pattern, self._original_script_content)
        if matches:
            operator = matches[0]
            if operator == '==':
                return '=='
            elif operator == '!=':
                return '!='
        
        # Default fallback
        return "=="

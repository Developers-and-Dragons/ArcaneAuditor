"""Variable usage detection logic for ScriptVarUsageRule."""

from typing import Generator
from lark import Tree
from ..shared.detector import ScriptDetector
from ...common import Violation


class VarUsageDetector(ScriptDetector):
    """Detects use of 'var' instead of 'let' or 'const' in script content."""
    
    def __init__(self, file_path: str = "", line_offset: int = 1):
        super().__init__(file_path, line_offset)
    
    def detect(self, ast: Tree, field_name: str = "") -> Generator[Violation, None, None]:
        """Detect use of 'var' declarations in the AST."""
        # Find all variable_statement nodes in the AST
        var_statements = ast.find_data('variable_statement')
        for var_stmt in var_statements:
            # Check if the variable statement uses VAR keyword
            if len(var_stmt.children) > 0 and hasattr(var_stmt.children[0], 'type') and var_stmt.children[0].type == 'VAR':
                # Get the variable declaration (second child)
                var_declaration = var_stmt.children[1]
                if hasattr(var_declaration, 'data') and var_declaration.data == 'variable_declaration':
                    var_token = var_stmt.children[0]
                    name_token = var_declaration.children[0]
                    var_name = name_token.value
                    line_number = self.get_line_number_from_token(var_token)

                    # Check if this var statement is inside a function
                    function_name = self.get_function_context_for_node(var_stmt, ast)

                    if function_name:
                        message = f"File section '{field_name}' uses 'var' declaration for variable '{var_name}' in function '{function_name}'. Consider using 'let' or 'const' instead."
                    else:
                        message = f"File section '{field_name}' uses 'var' declaration for variable '{var_name}'. Consider using 'let' or 'const' instead."

                    target_text, replacement = self._build_swap(var_token, name_token, var_name)
                    yield Violation(
                        message=message,
                        line=line_number,
                        suggested_replacement=replacement,
                        target_text=target_text,
                        replacement_context="substring" if target_text else None,
                    )

        # Find all for_var_statement nodes (for loops with var declarations)
        for_var_statements = ast.find_data('for_var_statement')
        for for_stmt in for_var_statements:
            # Get the variable declaration list (second child)
            var_declaration_list = for_stmt.children[1]
            if hasattr(var_declaration_list, 'data') and var_declaration_list.data == 'variable_declaration_list':
                # Process each variable declaration in the list
                for var_declaration in var_declaration_list.children:
                    if hasattr(var_declaration, 'data') and var_declaration.data == 'variable_declaration':
                        var_token = for_stmt.children[0]
                        name_token = var_declaration.children[0]
                        var_name = name_token.value
                        line_number = self.get_line_number_from_token(var_token)

                        target_text, replacement = self._build_swap(var_token, name_token, var_name)
                        yield Violation(
                            message=f"File section '{field_name}' uses 'var' declaration for variable '{var_name}' in for loop. Consider using 'let' or 'const' instead.",
                            line=line_number,
                            suggested_replacement=replacement,
                            target_text=target_text,
                            replacement_context="substring" if target_text else None,
                        )

        # Find all for_var_in_statement nodes (for-in loops with var declarations)
        for_var_in_statements = ast.find_data('for_var_in_statement')
        for for_stmt in for_var_in_statements:
            var_token = for_stmt.children[0]
            name_token = for_stmt.children[1]
            var_name = name_token.value
            line_number = self.get_line_number_from_token(var_token)

            target_text, replacement = self._build_swap(var_token, name_token, var_name)
            yield Violation(
                message=f"File section '{field_name}' uses 'var' declaration for variable '{var_name}' in for-in loop. Consider using 'let' or 'const' instead.",
                line=line_number,
                suggested_replacement=replacement,
                target_text=target_text,
                replacement_context="substring" if target_text else None,
            )

    def _build_swap(self, var_token, name_token, var_name: str):
        """Build a (target_text, replacement) pair anchored on the variable name.

        Slices ``var <name>`` from source using the VAR token's start and the
        identifier's end position; the keyword + identifier together is
        specific enough to avoid matching `var` substrings inside other
        identifiers. The replacement keeps any whitespace between the keyword
        and name exactly as it appears in source. Falls back to a plain
        keyword-only replacement if position info is unavailable.
        """
        fallback = (None, "let")
        if not self.source_text:
            return fallback
        start = getattr(var_token, 'start_pos', None)
        end = getattr(name_token, 'end_pos', None)
        if start is None or end is None or end <= start:
            return fallback
        slice_text = self.source_text[start:end]
        # Confirm the slice begins with the keyword and ends with the name —
        # otherwise the AST and source have drifted and a substring swap is
        # not safe.
        if not slice_text.startswith("var") or not slice_text.endswith(var_name):
            return fallback
        return slice_text, "let" + slice_text[len("var"):]
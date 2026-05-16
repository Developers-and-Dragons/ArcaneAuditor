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

                    # Check if this console statement is inside a function
                    function_name = self.get_function_context_for_node(member_expr, ast)

                    if function_name:
                        message = f"File section '{field_name}' contains console.{method_name} statement in function '{function_name}'. Remove debug statements from production code."
                    else:
                        message = f"File section '{field_name}' contains console.{method_name} statement. Remove debug statements from production code."

                    # Locate the enclosing statement so the substring swap
                    # comments the *whole* console call (including trailing
                    # `;`) and not just the member_dot_expression. If we can
                    # extract it cleanly, emit a substring swap; otherwise
                    # fall back to the legacy whole-line replacement.
                    stmt_slice = self._extract_enclosing_statement_text(ast, member_expr)
                    if stmt_slice is not None:
                        yield Violation(
                            message=message,
                            line=line_number,
                            suggested_replacement=f"// {stmt_slice}",
                            target_text=stmt_slice,
                            replacement_context="substring",
                        )
                    else:
                        yield Violation(
                            message=message,
                            line=line_number,
                            suggested_replacement=self._build_commented_line(line_number),
                        )

    def _extract_enclosing_statement_text(self, ast: Tree, member_expr) -> str:
        """Return the source slice for the call expression containing
        ``member_expr``, with any trailing ``;`` included, or ``None`` if
        positions are unavailable or the slice would be unsafe to
        substring-swap.

        The grammar emits ``arguments_expression`` for ``console.foo(...)``
        (no wrapping ``expression_statement``); the trailing ``;`` lives in a
        sibling ``eos`` token. We find the smallest enclosing
        ``arguments_expression`` and absorb optional whitespace + ``;`` after
        it. Skips enrichment when the slice contains ``"`` or ``\\`` — those
        characters get JSON-escaped when the script lives inside a PMD/POD
        string, so a literal substring search in the source file would miss.
        """
        if not self.source_text:
            return None
        target_meta = getattr(member_expr, 'meta', None)
        if target_meta is None or getattr(target_meta, 'empty', True):
            return None
        target_start = getattr(target_meta, 'start_pos', None)
        target_end = getattr(target_meta, 'end_pos', None)
        if target_start is None or target_end is None:
            return None

        best_span = None
        for stmt in ast.find_data('arguments_expression'):
            meta = getattr(stmt, 'meta', None)
            if meta is None or getattr(meta, 'empty', True):
                continue
            s = getattr(meta, 'start_pos', None)
            e = getattr(meta, 'end_pos', None)
            if s is None or e is None:
                continue
            if s <= target_start and e >= target_end:
                if best_span is None or (e - s) < (best_span[1] - best_span[0]):
                    best_span = (s, e)
        if best_span is None:
            return None
        s, e = best_span
        # Absorb trailing whitespace + single `;` if present.
        scan = e
        while scan < len(self.source_text) and self.source_text[scan] in ' \t':
            scan += 1
        if scan < len(self.source_text) and self.source_text[scan] == ';':
            e = scan + 1
        slice_text = self.source_text[s:e]
        if '"' in slice_text or '\\' in slice_text:
            return None
        return slice_text
    
    def _build_commented_line(self, file_line: int):
        """Return the violation's source line prefixed with `// `, preserving indentation."""
        if not self.source_text:
            return None
        ast_line = file_line - self.line_offset + 1
        if ast_line < 1:
            return None
        lines = self.source_text.split('\n')
        if ast_line > len(lines):
            return None
        original = lines[ast_line - 1].rstrip()
        stripped = original.lstrip()
        if not stripped:
            return None
        indent = original[:len(original) - len(stripped)]
        return f"{indent}// {stripped}"

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

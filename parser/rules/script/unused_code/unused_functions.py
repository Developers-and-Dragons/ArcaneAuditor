"""Script unused functions rule using unified architecture."""

from typing import Generator, Set, List, Tuple
from ...script.shared import ScriptRuleBase
from ...base import Finding, FixStrategy
from .unused_functions_detector import UnusedFunctionsDetector


class ScriptUnusedFunctionRule(ScriptRuleBase):
    """Validates that functions are not declared but never used."""

    DESCRIPTION = "Ensures functions are not declared but never used"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.LOCALIZED
    DETECTOR = UnusedFunctionsDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Unused functions add unnecessary code that developers must read and maintain, creating mental overhead when trying to understand what the page actually does. They also increase parsing time and memory usage. Removing unused functions keeps your PMD/Pod files focused and makes the actual logic easier to follow.

**What This Rule Does:** This rule tracks function usage within PMD and Pod files. Unlike standalone `.script` files that use export patterns, embedded scripts don't have formal exports. This rule identifies function variables that are declared but never called anywhere in the script or across related script sections in the same file.

**Note:** This rule is separate from `ScriptDeadCodeRule`, which validates export patterns in standalone `.script` files. Use `ScriptDeadCodeRule` for `.script` files and `ScriptUnusedFunctionRule` for embedded scripts in PMD/Pod files.''',
        'catches': [
            'Function variables declared but never called',
            'Functions that were intended to be used but aren\'t referenced',
            'Dead code that should be removed'
        ],
        'examples': '''**Example violations:**

```javascript
// In myPage.pmd
<%
  const processData = function(data) {  // ✅ Used below
    return data.filter(item => item.active);
  };
  
  const unusedHelper = function(val) {  // ❌ Never called - unused function
    return val * 2;
  };
  
  const results = processData(pageVariables.items);
%>
```

**Fix:**

```javascript
// In myPage.pmd
<%
  const processData = function(data) {  // ✅ Used
    return data.filter(item => item.active);
  };
  
  // ✅ Removed unusedHelper - it was never called
  
  const results = processData(pageVariables.items);
%>
```''',
        'recommendation': 'Remove unused functions from PMD/Pod embedded scripts. If a function is not called anywhere in the file, it should be removed to reduce code complexity and improve maintainability.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

    def _analyze_fields(self, model, script_fields: List[Tuple[str, str, str, int]], context=None) -> Generator[Finding, None, None]:
        """Analyze script fields with proper global/local scoping."""
        # Separate global and local script fields
        global_fields = []
        local_fields = []
        
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and field_value.strip():
                if self._is_global_script_field(field_name):
                    global_fields.append((field_path, field_value, field_name, line_offset))
                else:
                    local_fields.append((field_path, field_value, field_name, line_offset))
        
        # Analyze global functions (can be called from anywhere)
        if global_fields:
            yield from self._analyze_global_functions(model, global_fields, local_fields, context)
        
        # Analyze local functions (only checked within their own scope)
        yield from self._analyze_local_functions(model, local_fields, context)

    def _is_global_script_field(self, field_name: str) -> bool:
        """Check if a script field is in global scope (script section)."""
        return 'script' in field_name.lower()

    def _analyze_global_functions(self, model, global_fields: List[Tuple[str, str, str, int]], 
                                 local_fields: List[Tuple[str, str, str, int]], context=None) -> Generator[Finding, None, None]:
        """Analyze global functions - can be called from anywhere on the page."""
        # Collect all function declarations from global fields
        all_declared_functions = set()
        all_function_calls = set()
        global_field_asts = {}
        
        # First pass: collect declarations from global fields
        for field_path, field_value, field_name, line_offset in global_fields:
            ast = self._parse_script_content(field_value, context)
            if ast:
                global_field_asts[(field_path, field_name, line_offset)] = ast
                all_declared_functions.update(self._collect_function_declarations(ast))
        
        # Second pass: collect calls from ALL fields (global + local)
        all_fields = global_fields + local_fields
        for field_path, field_value, field_name, line_offset in all_fields:
            ast = self._parse_script_content(field_value, context)
            if ast:
                all_function_calls.update(self._collect_function_calls(ast))
        
        # Third pass: check for unused global functions
        for (field_path, field_name, line_offset), ast in global_field_asts.items():
            detector = self.DETECTOR(model.file_path, line_offset, all_declared_functions, all_function_calls)
            violations = detector.detect(ast, field_name)
            
            for violation in violations:
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=violation.line,
                    file_path=model.file_path
                )

    def _analyze_local_functions(self, model, local_fields: List[Tuple[str, str, str, int]], 
                                context=None) -> Generator[Finding, None, None]:
        """Analyze local functions - only checked within their own scope."""
        for field_path, field_value, field_name, line_offset in local_fields:
            ast = self._parse_script_content(field_value, context)
            if ast:
                # For local functions, only check within the same field
                local_declared_functions = self._collect_function_declarations(ast)
                local_function_calls = self._collect_function_calls(ast)
                
                detector = self.DETECTOR(model.file_path, line_offset, local_declared_functions, local_function_calls)
                violations = detector.detect(ast, field_name)
                
                for violation in violations:
                    yield Finding(
                        rule=self,
                        message=violation.message,
                        line=violation.line,
                        file_path=model.file_path
                    )

    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None, path=None) -> Generator[Finding, None, None]:
        """Check script content using the detector - not used in file-level analysis."""
        # This method is not used when _analyze_fields is overridden
        # Return empty generator to avoid NoneType iteration errors
        yield from []
    
    def _collect_function_declarations(self, ast) -> Set[str]:
        """
        Collect all function declarations from the AST.
        
        In PMD Script, all functions are anonymous and assigned to variables.
        We track the variable names, not function names.
        
        Patterns to detect:
        - var funcName = function() { ... }
        - let funcName = function() { ... }
        - const funcName = function() { ... }
        - var funcName = () => { ... }  (arrow functions)
        """
        declared_functions = set()
        
        try:
            # Find all variable declarations recursively (including nested ones)
            for var_decl_node in ast.find_data('variable_statement'):
                # Look for variables that are assigned to functions
                variable_names = self._extract_function_variable_names(var_decl_node)
                declared_functions.update(variable_names)
            
            # Also check for assignment expressions that assign functions
            # This handles cases where the parser incorrectly parses function declarations as assignments
            for assignment_node in ast.find_data('assignment_expression'):
                function_name = self._extract_function_from_assignment(assignment_node)
                if function_name:
                    declared_functions.add(function_name)
        except Exception:
            pass  # If AST traversal fails, return empty set
        
        return declared_functions
    
    def _collect_function_calls(self, ast) -> Set[str]:
        """
        Collect all references to identifiers that could be function calls.
        
        This includes:
        - Direct calls: myFunc()
        - Function references passed as arguments: array.map(myFunc)
        - Function references in expressions: var x = myFunc
        """
        function_calls = set()
        
        try:
            # Collect all identifiers that are referenced (not declarations)
            # We'll filter by collecting identifiers used in various contexts
            
            # 1. Direct function calls
            for call_node in ast.find_data('call_expression'):
                func_name = self._extract_identifier_from_expression(call_node.children[0] if call_node.children else None)
                if func_name:
                    function_calls.add(func_name)
            
            # 2. Identifiers used as function arguments (e.g., array.map(myFunc))
            for call_node in ast.find_data('arguments_expression'):
                # Get all identifiers in the arguments
                for arg_node in call_node.find_data('identifier_expression'):
                    if len(arg_node.children) > 0 and hasattr(arg_node.children[0], 'value'):
                        function_calls.add(arg_node.children[0].value)
            
            # 3. Identifiers in assignments (e.g., var x = myFunc)
            for assignment_node in ast.find_data('assignment_expression'):
                if len(assignment_node.children) >= 2:
                    right_side = assignment_node.children[1]
                    func_name = self._extract_identifier_from_expression(right_side)
                    if func_name:
                        function_calls.add(func_name)
            
            # 4. Return statements that return a function reference
            for return_node in ast.find_data('return_statement'):
                if len(return_node.children) > 0:
                    func_name = self._extract_identifier_from_expression(return_node.children[0])
                    if func_name:
                        function_calls.add(func_name)
        except Exception:
            pass
        
        return function_calls
    
    def _extract_identifier_from_expression(self, node):
        """Extract identifier name from an expression node."""
        if node is None:
            return ""
        if hasattr(node, 'value'):
            return node.value
        if hasattr(node, 'children') and node.children:
            # For member expressions, get the last identifier (method name)
            for child in node.children:
                if hasattr(child, 'value'):
                    return child.value
        return ""
    
    def _extract_function_variable_names(self, var_statement_node) -> Set[str]:
        """
        Extract variable names that are assigned to functions.
        
        For example, from: var myFunc = function() { ... }
        We extract: "myFunc"
        """
        function_vars = set()
        
        try:
            # Traverse the variable statement to find variable declarations
            for child in var_statement_node.iter_subtrees():
                if child.data == 'variable_declaration':
                    # Get the variable name (first child is IDENTIFIER)
                    if len(child.children) >= 1:
                        identifier = child.children[0]
                        if hasattr(identifier, 'value'):
                            var_name = identifier.value
                            
                            # Check if it's assigned to a function
                            # Look for initializer -> function_expression or arrow_function_expression
                            if len(child.children) >= 2:
                                initializer = child.children[1]
                                if self._is_function_assignment(initializer):
                                    function_vars.add(var_name)
        except Exception:
            pass
        
        return function_vars
    
    def _is_function_assignment(self, initializer_node) -> bool:
        """
        Check if an initializer node assigns a function (not a function call result).
        """
        try:
            # First, check if the initializer node ITSELF is a function expression
            # (This handles cases where there's no wrapper)
            if hasattr(initializer_node, 'data'):
                if initializer_node.data in ('function_expression', 'arrow_function_expression'):
                    return True
            
            if not hasattr(initializer_node, 'children') or not initializer_node.children:
                return False
            
            # Look through ALL children (not just first) to find function expressions
            for child in initializer_node.children:
                # Skip tokens (like "=" operator)
                if not hasattr(child, 'data'):
                    continue
                
                # Direct function assignment ✅
                if child.data in ('function_expression', 'arrow_function_expression'):
                    return True
                
                # Parenthesized function ✅
                if child.data == 'parenthesized_expression':
                    if hasattr(child, 'children') and child.children:
                        for inner in child.children:
                            if hasattr(inner, 'data') and inner.data in ('function_expression', 'arrow_function_expression'):
                                return True
                
                # Call expression = returns result, NOT a function ❌
                if child.data == 'call_expression':
                    return False
                
                # Member expression (property access) = not a function ❌
                if child.data == 'member_dot_expression':
                    return False
            
            # No function found
            return False
            
        except Exception as e:
            from utils.console import warn
            warn(f"Exception in _is_function_assignment: {e}")
            return False
    
    def _extract_function_from_assignment(self, assignment_node) -> str:
        """
        Extract function name from assignment expressions that assign functions.
        
        This handles cases where the parser incorrectly parses function declarations as assignments.
        For example: const funcName = function() { ... } might be parsed as an assignment.
        """
        try:
            # Check if this is an assignment to a function
            if len(assignment_node.children) >= 2:
                left_side = assignment_node.children[0]
                right_side = assignment_node.children[1]
                
                # Check if left side is an identifier (variable name)
                if (hasattr(left_side, 'data') and left_side.data == 'identifier_expression' and
                    len(left_side.children) >= 1 and hasattr(left_side.children[0], 'value')):
                    
                    variable_name = left_side.children[0].value
                    
                    # Check if right side is a function expression
                    if self._is_function_assignment(right_side):
                        return variable_name
        except Exception:
            pass
        return None
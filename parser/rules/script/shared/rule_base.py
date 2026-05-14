"""Base rule class for script analysis rules."""

from abc import ABC, abstractmethod
from typing import Any, Generator, List, Tuple
from ...base import Rule, Finding, Category
from ....models import PMDModel, PodModel, ScriptModel
from .violation import Violation
from .detector import ScriptDetector


class ScriptRuleBase(Rule, ABC):
    """Base class for script analysis rules with unified structure."""

    CATEGORY = Category.SCRIPT

    # Subclasses must define these
    DETECTOR: type[ScriptDetector]
    
    @abstractmethod
    def get_description(self) -> str:
        """Get rule description - must be implemented by subclasses."""
        pass
    
    def apply_settings(self, settings: dict):
        """
        Apply custom settings to the rule.
        This method is called by the rules engine to apply configuration.
        
        Args:
            settings: Dictionary containing custom settings
        """
        # Store settings for use in detector instantiation
        self._custom_settings = settings
    
    def analyze(self, context) -> Generator[Finding, None, None]:
        """Main analysis entry point."""
        pmds = getattr(context, "pmds", None) or {}
        pods = getattr(context, "pods", None) or {}
        scripts = getattr(context, "scripts", None) or {}
        wqlqueries = getattr(context, "wqlqueries", None) or {}
        # Analyze PMD files
        for pmd in pmds.values():
            yield from self._analyze_pmd(pmd, context)
        
        # Analyze POD files
        for pod in pods.values():
            yield from self._analyze_pod(pod, context)

        # Analyze WQL query files (offset/limit/query fields only)
        for wql_model in wqlqueries.values():
            yield from self._analyze_wqlquery(wql_model, context)
        
        # Analyze script files
        for script in scripts.values():
            yield from self._analyze_script(script, context)

    def _analyze_wqlquery(self, wql_model, context=None) -> Generator[Finding, None, None]:
        """Analyze .wqlquery file for script fields in query/offset/limit."""
        for field in ("query", "offset", "limit"):
            value = getattr(wql_model, field, None)
            if isinstance(value, str) and "<%" in value and "%>" in value:
                try:
                    yield from self._check(
                        value,
                        f"wqlquery.{field}",
                        wql_model.file_path,
                        1,
                        context
                    )
                except Exception as e:
                    from utils.console import warn
                    warn(f"Failed to analyze wqlquery {wql_model.file_path} field {field}: {e}")
    
    def _analyze_pmd(self, pmd_model: PMDModel, context) -> Generator[Finding, None, None]:
        """Analyze PMD file for script fields."""
        script_fields = self.find_script_fields(pmd_model, context)
        yield from self._analyze_fields(pmd_model, script_fields, context)
    
    def _analyze_pod(self, pod_model: PodModel, context=None) -> Generator[Finding, None, None]:
        """Analyze POD file for script fields."""
        script_fields = self.find_pod_script_fields(pod_model)
        yield from self._analyze_fields(pod_model, script_fields, context)
    
    def _analyze_script(self, script_model: ScriptModel, context=None) -> Generator[Finding, None, None]:
        """Analyze standalone script file."""
        try:
            yield from self._check(
                script_model.source, 
                "script", 
                script_model.file_path, 
                1,
                context
            )
        except Exception as e:
            from utils.console import warn
            warn(f"Failed to analyze script file {script_model.file_path}: {e}")
    
    def _analyze_fields(self, model, script_fields: List[Tuple[str, str, str, int]], context=None) -> Generator[Finding, None, None]:
        """Analyze script fields from a model."""
        for field_path, field_value, field_name, line_offset in script_fields:
            if field_value and field_value.strip():
                check_result = self._check(field_value, field_name, model.file_path, line_offset, context)
                if check_result is not None:
                    yield from check_result
    
    def _check(self, script_content: str, field_name: str, file_path: str, line_offset: int = 1, context=None) -> Generator[Finding, None, None]:
        """Check script content using the detector."""
        # Strip <% %> tags from script content if present
        clean_script_content = self._strip_script_tags(script_content)
        
        # Parse the script content with context for caching
        ast = self._parse_script_content(clean_script_content, context)
        if not ast:
            # Parsing failed - error should already be logged to context by _parse_script_content
            return  # Return empty generator
        
        # Use detector to find violations
        detector = self.DETECTOR(file_path, line_offset)
        
        # Apply custom settings to detector if available
        if hasattr(self, '_custom_settings') and hasattr(detector, 'apply_settings'):
            detector.apply_settings(self._custom_settings)
        
        violations = detector.detect(ast, field_name)
        
        # Convert violations to findings
        # Handle both List[Violation] and Generator[Violation, None, None]
        if violations is not None and hasattr(violations, '__iter__') and not isinstance(violations, str):
            for violation in violations:
                yield Finding(
                    rule=self,
                    message=violation.message,
                    line=violation.line,
                    file_path=file_path
                )
    
    def _extract_variable_from_empty_expression(self, node) -> str:
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
    
    def _extract_variable_from_not_empty_expression(self, node) -> str:
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
            if len(node.children) > 0 and hasattr(node.children[0], 'data') and node.children[0].data == 'empty_function_expression':
                # not_expression -> empty_function_expression: ['empty', '(', 'expression', ')']
                empty_func = node.children[0]
                if len(empty_func.children) > 2:
                    return self._extract_variable_from_node(empty_func.children[2])
            elif len(node.children) > 0 and hasattr(node.children[0], 'data') and node.children[0].data == 'empty_expression':
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
    
    def _strip_script_tags(self, script_content: str) -> str:
        """
        Strip <% %> tags from script content if present.
        
        Args:
            script_content: Raw script content (may include <% %> tags)
            
        Returns:
            Clean script content without tags
        """
        if not script_content:
            return script_content
        
        # Check if content starts with <%
        if script_content.strip().startswith('<%'):
            # Find the end tag
            end_pos = script_content.find('%>')
            if end_pos != -1:
                # Extract content between <% and %>
                start_pos = script_content.find('<%')
                if start_pos != -1:
                    # Get content after <% and before %>
                    clean_content = script_content[start_pos + 2:end_pos].strip()
                    return clean_content
        
        # No tags found, return as-is
        return script_content
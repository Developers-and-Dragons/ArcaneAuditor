"""
Shared components for structure rules using unified architecture.

This module provides base classes and utilities for structure validation rules
that analyze PMD and POD files for structural compliance issues.
"""
from abc import ABC, abstractmethod
from typing import Generator, List, Dict, Any, Optional
from ...base import Rule, Finding
from ....models import PMDModel, PodModel, ProjectContext, WQLQueryModel


class StructureRuleBase(Rule, ABC):
    """Base class for structure analysis rules with unified structure."""
    
    @abstractmethod
    def get_description(self) -> str:
        """Get rule description - must be implemented by subclasses."""
        pass
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Main analysis entry point."""
        # Analyze PMD files
        for pmd_model in context.pmds.values():
            yield from self._analyze_pmd(pmd_model, context)
        
        # Analyze POD files
        for pod_model in context.pods.values():
            yield from self._analyze_pod(pod_model, context)
        
        # Analyze AMD file if present
        if context.amd:
            yield from self._analyze_amd(context.amd, context)

        # Analyze WQL query files if present
        for wql_model in getattr(context, "wqlqueries", {}).values():
            yield from self._analyze_wqlquery(wql_model, context)

    def _analyze_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD file - must be implemented by subclasses."""
        yield from self.visit_pmd(pmd_model, context)
    
    def _analyze_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD file - must be implemented by subclasses."""
        yield from self.visit_pod(pod_model, context)
    
    def _analyze_amd(self, amd_model, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze AMD file - can be overridden by subclasses."""
        yield from self.visit_amd(amd_model, context)

    def _analyze_wqlquery(self, wql_model: WQLQueryModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze WQL query file - can be overridden by subclasses."""
        yield from self.visit_wqlquery(wql_model, context)

    @abstractmethod
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Visit PMD model - must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Visit POD model - must be implemented by subclasses."""
        pass
    
    def visit_amd(self, amd_model, context: ProjectContext) -> Generator[Finding, None, None]:
        """Visit AMD model - can be overridden by subclasses."""
        # Default implementation does nothing
        return

    def visit_wqlquery(self, wql_model: WQLQueryModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Visit WQL query model - can be overridden by subclasses."""
        # Default implementation does nothing
        return
        yield  # This line is never reached, but makes it a generator
    
    def _create_finding(self, message: str, file_path: str, line: int = 1) -> Finding:
        """Create a finding with consistent formatting."""
        return Finding(
            rule=self,
            message=message,
            line=line,
            file_path=file_path
        )
    
    # Unified line calculation methods
    def get_field_line_number(self, model, field_name: str, field_value: str) -> int:
        """Get line number for a specific field with a specific value."""
        from ...common import PMDLineUtils
        return PMDLineUtils.find_field_line_number(model, field_name, field_value)
    
    def get_section_line_number(self, model, section_name: str) -> int:
        """Get line number for a specific section."""
        from ...common import PMDLineUtils
        return PMDLineUtils.find_section_line_number(model, section_name)
    
    def get_field_after_entity_line_number(self, model, entity_field: str, entity_value: str, target_field: str) -> int:
        """Get line number for a field that appears after a specific entity."""
        from ...common import PMDLineUtils
        return PMDLineUtils.find_field_after_entity(model, entity_field, entity_value, target_field)
    
    def find_pattern_line_number(self, model, pattern: str, case_sensitive: bool = False) -> int:
        """Find line number where a pattern appears in the source content."""
        if not hasattr(model, 'source_content') or not model.source_content:
            return 1
        
        try:
            lines = model.source_content.split('\n')
            for i, line in enumerate(lines):
                if case_sensitive:
                    if pattern in line:
                        return i + 1
                else:
                    if pattern.lower() in line.lower():
                        return i + 1
            return 1
        except Exception:
            return 1
    
    def get_line_from_text_position(self, text: str, position: int) -> int:
        """Get line number from a text position (character offset)."""
        if not text or position < 0:
            return 1
        try:
            return text[:position].count('\n') + 1
        except Exception:
            return 1
    
    def extract_nearest_container_from_path(self, widget_path: str) -> str:
        """
        Extract the nearest meaningful container field name from a widget path.
        
        This generically finds the last non-numeric segment in the path, which represents
        the container field that holds the widget (e.g., "cellTemplate", "primaryLayout", etc.).
        
        Examples:
            "body.children.1.columns.0.cellTemplate" -> "cellTemplate"
            "body.primaryLayout" -> "primaryLayout"
            "body.children.2" -> "children"
            "footer.children.0.items.1" -> "items"
        
        Args:
            widget_path: The full widget path
            
        Returns:
            The nearest container field name, or None if not found
        """
        if not widget_path:
            return None
        
        # Split path by dots and filter out numeric indices
        path_segments = widget_path.split('.')
        
        # Iterate backwards to find the last non-numeric, non-root segment
        for segment in reversed(path_segments):
            # Skip numeric indices
            if segment.isdigit():
                continue
            # Skip root sections like 'body', 'title', 'footer'
            if segment in ['body', 'title', 'footer', 'template']:
                continue
            # This is a meaningful container field
            return segment
        
        return None
    
    def find_context_line(self, lines: list, context: str, start: int, end: int) -> int:
        """
        Find the line number where a specific context field appears.
        
        This generically searches for any field name in the JSON structure
        (e.g., 'cellTemplate', 'primaryLayout', 'columns').
        
        Args:
            lines: List of source code lines
            context: Context field to search for
            start: Start line index
            end: End line index
            
        Returns:
            Line index where context is found, or -1 if not found
        """
        for i in range(start, end):
            if f'"{context}"' in lines[i]:
                return i
        return -1
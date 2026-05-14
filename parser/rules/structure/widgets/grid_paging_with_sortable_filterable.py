"""
Rule to detect grids with paging and sortableAndFilterable columns.

Combining paging with sortable/filterable columns can cause severe performance 
degradation due to how data is fetched and processed.

This rule checks PMD and POD grid widgets.
"""
from typing import Generator, Dict, Any

from ...base import Finding, Category
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class GridPagingWithSortableFilterableRule(StructureRuleBase):
    """
    Detects grids with paging and sortableAndFilterable columns.
    
    This rule checks:
    - Grid widgets in PMD files
    - Grid widgets in POD files
    
    Flags grids that have:
    - autoPaging: true OR pagingInfo present
    - AND any column with sortableAndFilterable: true
    """
    
    ID = "GridPagingWithSortableFilterableRule"
    DESCRIPTION = "Detects grids with paging and sortableAndFilterable columns which can cause performance issues"
    SEVERITY = "ACTION"
    CATEGORY = Category.WIDGET
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Combining paging with sortable/filterable columns can cause severe performance degradation due to how data is fetched and processed. This combination forces the system to fetch, sort, and filter data on every page change, leading to slow response times and potential timeout issues.''',
        'catches': [
            'Grids with `autoPaging: true` OR `pagingInfo` present',
            'AND any column with `sortableAndFilterable: true`'
        ],
        'examples': '''**Example violations:**

```json
{
  "type": "grid",
  "id": "workerGrid",
  "autoPaging": true,  // ❌ Paging enabled
  "columns": [
    {
      "columnId": "workerName",
      "sortableAndFilterable": true  // ❌ Sortable/filterable with paging
    }
  ]
}
```

**Fix:**

```json
{
  "type": "grid",
  "id": "workerGrid",
  "autoPaging": true,  // ✅ Keep paging
  "columns": [
    {
      "columnId": "workerName",
      "sortableAndFilterable": false  // ✅ Disable sortable/filterable when using paging
    }
  ]
}
```

**OR remove paging if sorting/filtering is required:**

```json
{
  "type": "grid",
  "id": "workerGrid",
  // ✅ No paging
  "columns": [
    {
      "columnId": "workerName",
      "sortableAndFilterable": true  // ✅ Can use sortable/filterable without paging
    }
  ]
}
```''',
        'recommendation': 'Either remove paging from grids that need sortable/filterable columns, or disable sortableAndFilterable on all columns when using paging. This combination causes severe performance issues.'
    }
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for grids with paging and sortableAndFilterable columns."""
        if not pmd_model.presentation:
            return
        
        # Use generic traversal to find all widgets
        presentation_dict = pmd_model.presentation.__dict__
        
        for section_name, section_data in presentation_dict.items():
            if isinstance(section_data, dict):
                for widget, path, index, parent_type, container_name in self.traverse_presentation_structure(section_data, section_name):
                    if isinstance(widget, dict) and widget.get('type') == 'grid':
                        yield from self._check_grid_paging_and_sortable(widget, pmd_model, section_name, path)
            elif isinstance(section_data, list):
                # Handle tabs list (tabs is a list of section widgets)
                for i, tab_item in enumerate(section_data):
                    if isinstance(tab_item, dict):
                        tab_path = f"{section_name}.{i}"
                        for widget, path, index, parent_type, container_name in self.traverse_presentation_structure(tab_item, tab_path):
                            if isinstance(widget, dict) and widget.get('type') == 'grid':
                                yield from self._check_grid_paging_and_sortable(widget, pmd_model, section_name, path)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for grids with paging and sortableAndFilterable columns."""
        # Find all widgets in POD template
        widgets = self.find_pod_widgets(pod_model)
        
        for widget_path, widget_data in widgets:
            if isinstance(widget_data, dict) and widget_data.get('type') == 'grid':
                yield from self._check_grid_paging_and_sortable(widget_data, None, 'template', widget_path, pod_model)
    
    def _check_grid_paging_and_sortable(self, grid_widget: Dict[str, Any], pmd_model=None, section='body', widget_path="", pod_model=None):
        """Check if a grid has both paging and sortableAndFilterable columns."""
        if not isinstance(grid_widget, dict):
            return
        
        grid_id = grid_widget.get('id', 'unknown_grid')
        
        # Check if grid has paging enabled
        has_auto_paging = grid_widget.get('autoPaging') is True
        has_paging_info = 'pagingInfo' in grid_widget and grid_widget.get('pagingInfo') is not None
        
        if not (has_auto_paging or has_paging_info):
            return  # No paging, no issue
        
        # Check columns for sortableAndFilterable
        columns = grid_widget.get('columns', [])
        if not isinstance(columns, list):
            return
        
        for column in columns:
            if isinstance(column, dict):
                column_id = column.get('columnId', 'unknown_column')
                is_sortable_filterable = column.get('sortableAndFilterable')
                
                if is_sortable_filterable is True or (isinstance(is_sortable_filterable, str) and is_sortable_filterable.lower() == 'true'):
                    # Get line number
                    line_number = 1
                    if pmd_model and hasattr(pmd_model, 'source_content'):
                        # Try to find the column in source
                        line_number = self.get_field_line_number(pmd_model, 'columnId', column_id)
                    elif pod_model and hasattr(pod_model, 'source_content'):
                        line_number = self.get_field_line_number(pod_model, 'columnId', column_id)
                    
                    paging_type = "autoPaging" if has_auto_paging else "pagingInfo"
                    
                    yield self._create_finding(
                        message=f"Grid '{grid_id}' has paging ({paging_type}) and column '{column_id}' with sortableAndFilterable: true. This can cause major performance issues. Either remove paging or set sortableAndFilterable: false on all columns.",
                        file_path=pmd_model.file_path if pmd_model else pod_model.file_path,
                        line=line_number
                    )


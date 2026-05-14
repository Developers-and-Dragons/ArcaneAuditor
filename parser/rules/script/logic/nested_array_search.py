"""Script nested array search rule using unified architecture."""

from ...base import FixStrategy
from ...script.shared import ScriptRuleBase
from .nested_array_search_detector import NestedArraySearchDetector


class ScriptNestedArraySearchRule(ScriptRuleBase):
    """Rule to detect nested array search patterns that cause severe performance issues."""

    DESCRIPTION = "Detects nested array search patterns that cause severe performance issues"
    SEVERITY = "ADVICE"
    FIX_STRATEGY = FixStrategy.REFACTOR
    DETECTOR = NestedArraySearchDetector
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Nested array searches (like `workers.map(worker => orgData.find(org => org.id == worker.orgId))`) create O(n²) performance problems that can cause out-of-memory issues with large datasets. For every item in the outer array, the inner array is searched completely, leading to exponential performance degradation. This pattern is especially problematic in Workday Extend where data arrays can contain thousands of records.''',
        'catches': [
            'Nested array searches using `find()` or `filter()` inside `map()`, `forEach()`, or `filter()` callbacks',
            'Performance anti-patterns that cause exponential time complexity',
            'Code that searches external arrays from within iteration callbacks'
        ],
        'examples': '''**Example violations:**

```javascript
// ❌ Nested search - searches entire orgData for each worker
const result = workers.map(worker => 
    orgData.find(org => org.id == worker.orgId)
);

// ❌ Nested filter - filters entire teams array for each department
departments.forEach(department => {
    const team = teams.filter(team => team.deptId == department.id);
});
```

**Fix:**

```javascript
// ✅ Use list:toMap for efficient O(1) lookups
const orgById = list:toMap(orgData, 'id');
const result = workers.map(worker => orgById[worker.orgId]);

// ✅ Or use a single filter with proper indexing
const teamByDeptId = list:toMap(teams, 'deptId');
departments.forEach(department => {
    const team = teamByDeptId[department.id];
});
```''',
        'recommendation': 'Use `list:toMap()` to convert arrays to maps for O(1) lookups instead of nested searches. This dramatically improves performance, especially with large datasets.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION

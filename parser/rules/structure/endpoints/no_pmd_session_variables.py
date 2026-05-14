"""
Rule to detect outboundVariable endpoints with variableScope: session.

PMD session variables persist for the entire user session, consuming memory and 
potentially causing performance issues as sessions accumulate data. Use flow 
scope instead.

This rule only checks outbound endpoints (not inbound).
"""
from typing import Generator

from ...base import Finding, FixStrategy, Category
from ....models import PMDModel, ProjectContext
from ..shared import StructureRuleBase


class NoPMDSessionVariablesRule(StructureRuleBase):
    """
    Detects outboundVariable endpoints with variableScope: session.
    
    This rule checks:
    - Outbound endpoints in PMD files only
    - Flags endpoints with type: "outboundVariable" AND variableScope: "session"
    
    Note: POD files don't use this pattern, so they're not checked.
    """
    
    ID = "NoPMDSessionVariablesRule"
    DESCRIPTION = "Detects outboundVariable endpoints with variableScope: session which can cause performance degradation"
    SEVERITY = "ACTION"
    CATEGORY = Category.ENDPOINT
    FIX_STRATEGY = FixStrategy.LOCALIZED
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Session-scoped variables persist for the entire user session (potentially hours), continuously consuming memory even after the user leaves your page. This memory isn't released until logout, degrading performance over time and potentially causing issues for long-running sessions.''',
        'catches': [
            'Outbound endpoints with `type: "outboundVariable"` AND `variableScope: "session"`'
        ],
        'examples': '''**Example violations:**

```json
{
  "outboundEndpoints": [
    {
      "name": "saveUserPreference",
      "type": "outboundVariable",
      "variableScope": "session"  // ❌ Lasts entire session - performance issue
    }
  ]
}
```

**Fix:**

```json
{
  "outboundEndpoints": [
    {
      "name": "saveUserPreference",
      "type": "outboundVariable",
      "variableScope": "flow"  // ✅ Use a flow variable, instead
    }
  ]
}
```''',
        'recommendation': 'Use `variableScope: "flow"` instead of `"session"` for outboundVariable endpoints to prevent memory accumulation and performance degradation.'
    }
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for session-scoped outboundVariable endpoints."""
        # Only check outbound endpoints
        if pmd_model.outboundEndpoints:
            if isinstance(pmd_model.outboundEndpoints, list):
                for i, endpoint in enumerate(pmd_model.outboundEndpoints):
                    if isinstance(endpoint, dict):
                        yield from self._check_endpoint_session_variable(endpoint, pmd_model, i)
    
    def visit_pod(self, pod_model, context: ProjectContext) -> Generator[Finding, None, None]:
        """POD files don't use this pattern, so nothing to check."""
        return
        yield  # Make it a generator
    
    def _check_endpoint_session_variable(self, endpoint, pmd_model, index):
        """Check if an outbound endpoint is a session-scoped variable."""
        if not isinstance(endpoint, dict):
            return
        
        endpoint_name = endpoint.get('name', f'endpoint[{index}]')
        endpoint_type = endpoint.get('type')
        variable_scope = endpoint.get('variableScope')
        
        # Check if it's an outboundVariable with session scope
        if endpoint_type == "outboundVariable" and variable_scope == "session":
            line_number = self._get_endpoint_line_number(pmd_model, endpoint_name)
            
            yield self._create_finding(
                message=f"Outbound endpoint '{endpoint_name}' uses session-scoped variable (variableScope: session) which can cause performance degradation. Use 'flow' scope instead.",
                file_path=pmd_model.file_path,
                line=line_number
            )
    
    def _get_endpoint_line_number(self, pmd_model: PMDModel, endpoint_name: str) -> int:
        """Get line number for the variableScope field."""
        if hasattr(pmd_model, 'source_content'):
            # Use pattern search to find the variableScope field
            return self.find_pattern_line_number(pmd_model, '"variableScope": "session"')
        return 1


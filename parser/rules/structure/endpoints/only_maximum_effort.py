"""
Rule to ensure endpoints do not use bestEffort.

Using bestEffort: true on endpoints can silently mask API failures, leading to data 
inconsistency and hard-to-debug issues.

This rule checks both inbound and outbound endpoints.
"""
from typing import Generator

from ...base import Finding, FixStrategy, Category
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase
from utils.jsonpath import endpoint_jsonpath


class OnlyMaximumEffortRule(StructureRuleBase):
    """
    Ensures endpoints do not use bestEffort to prevent masked failures.
    
    This rule checks:
    - Inbound endpoints in PMD files
    - Outbound endpoints in PMD files
    - Endpoints in POD files
    """
    
    ID = "OnlyMaximumEffortRule"
    DESCRIPTION = "Ensures endpoints do not use bestEffort to prevent masked API failures"
    SEVERITY = "ACTION"
    CATEGORY = Category.ENDPOINT
    FIX_STRATEGY = FixStrategy.ACTIONABLE
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Using `bestEffort: true` on endpoints silently swallows API failures, causing your code to continue executing as if the call succeeded when it actually failed. This leads to data inconsistency, partial updates, and bugs that are extremely hard to debug because you have no visibility into the failure.''',
        'catches': [
            'Endpoints with `bestEffort: true` on inbound and outbound endpoints',
            'Includes PMD and POD endpoints'
        ],
        'examples': '''**Example violations:**

```json
{
  "name": "getWorkers",
  "bestEffort": true  // ❌ Can mask API failures
}
```

**Fix:**

```json
{
  "name": "getWorkers"
  // ✅ Remove bestEffort property
}
```''',
        'recommendation': 'Remove `bestEffort: true` from all endpoints to ensure API failures are properly caught and handled, preventing silent failures and data inconsistencies.'
    }
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for bestEffort on endpoints."""
        # Check inbound endpoints
        if pmd_model.inboundEndpoints:
            for i, endpoint in enumerate(pmd_model.inboundEndpoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_best_effort(endpoint, pmd_model, 'inbound', i)
        
        # Check outbound endpoints
        if pmd_model.outboundEndpoints:
            if isinstance(pmd_model.outboundEndpoints, list):
                for i, endpoint in enumerate(pmd_model.outboundEndpoints):
                    if isinstance(endpoint, dict):
                        yield from self._check_endpoint_best_effort(endpoint, pmd_model, 'outbound', i)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for bestEffort on endpoints."""
        if pod_model.seed.endPoints:
            for i, endpoint in enumerate(pod_model.seed.endPoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_best_effort(endpoint, pod_model, 'pod', i)
    
    # Matches: "bestEffort": true | "bestEffort":true | "bestEffort": "true" | "bestEffort":"true"
    _BEST_EFFORT_TRUE_RE = r'"bestEffort"\s*:\s*"?true"?'
    _NAME_FIELD_RE = r'"name"\s*:\s*"{name}"'

    def _check_endpoint_best_effort(self, endpoint, model, endpoint_type, index):
        """Check if an endpoint has bestEffort: true."""
        if not isinstance(endpoint, dict):
            return

        endpoint_name = endpoint.get('name', f'endpoint[{index}]')
        best_effort = endpoint.get('bestEffort')

        # Check if bestEffort is set to true (handle both boolean and string)
        if not (best_effort is True or (isinstance(best_effort, str) and best_effort.lower() == 'true')):
            return

        line_number, target_text, replacement = self._locate_best_effort(model, endpoint.get('name'))

        yield self._create_finding(
            message=f"{endpoint_type.title()} endpoint '{endpoint_name}' has bestEffort: true which can mask API failures. It is advised to avoid using bestEffort.",
            file_path=model.file_path,
            line=line_number,
            suggested_replacement=replacement if replacement is not None else "false",
            path=endpoint_jsonpath(endpoint_type, endpoint.get('name'), index=index, subkey='bestEffort'),
            target_text=target_text,
            replacement_context="substring" if target_text else None,
        )

    def _locate_best_effort(self, model, endpoint_name):
        """Locate the bestEffort assignment for a named endpoint in the source.

        Strategy: find the endpoint's `"name": "<endpoint_name>"` occurrence in
        the source, then search forward for the next `bestEffort: true` match.
        This avoids the multi-match collision that occurs when several endpoints
        share the same bestEffort spelling.

        Returns ``(line_number, target_text, replacement)``. When source-based
        location fails, falls back to ``(1, None, None)`` so the agent receives
        the bare ``"false"`` suggestion and the human still sees a finding.
        """
        import re
        source = getattr(model, 'source_content', None)
        if not source or not endpoint_name:
            return 1, None, None

        # Find the endpoint's name field occurrence.
        name_match = re.search(self._NAME_FIELD_RE.format(name=re.escape(endpoint_name)), source)
        search_start = name_match.end() if name_match else 0

        be_match = re.search(self._BEST_EFFORT_TRUE_RE, source[search_start:], re.IGNORECASE)
        if not be_match:
            return 1, None, None

        absolute_pos = search_start + be_match.start()
        line_number = source.count('\n', 0, absolute_pos) + 1
        target = be_match.group(0)
        replacement = re.sub(r'true', 'false', target, count=1, flags=re.IGNORECASE)
        return line_number, target, replacement


from typing import Generator
from ...base import Finding, FixStrategy, Category
from ...common import PMDLineUtils
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase
from utils.jsonpath import endpoint_jsonpath


class EndpointFailOnStatusCodesRule(StructureRuleBase):
    """Ensures endpoints have proper failOnStatusCodes structure with required codes 400 and 403."""

    DESCRIPTION = "Ensures endpoints have failOnStatusCodes with minimum required codes 400 and 403"
    SEVERITY = "ACTION"
    CATEGORY = Category.ENDPOINT
    FIX_STRATEGY = FixStrategy.ACTIONABLE
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Without proper error handling (failOnStatusCodes), your endpoints silently swallow errors like "400 Bad Request" or "403 Forbidden", causing your application to proceed as if the call succeeded when it actually failed. This leads to data inconsistencies, broken workflows, and debugging nightmares. Explicit error handling ensures failures are properly caught and handled.''',
        'catches': [
            'Missing error handling for 4xx status codes that Extend doesn\'t treat as failures by default'
        ],
        'examples': '''**Example violations:**

```json
{
  "endPoints": [{
    "name": "getCurrentUser",
    "url": "/users/me"
    // ❌ Missing failOnStatusCodes
  }]
}
```

**Fix:**

```json
{
  "endPoints": [{
    "name": "getCurrentUser", 
    "url": "/users/me",
    "failOnStatusCodes": [
      {"code": 400},
      {"code": 403}
    ]
  }]
}
```''',
        'recommendation': 'Always include `failOnStatusCodes` with at least codes 400 and 403 on all endpoints to ensure errors are properly caught and handled, preventing silent failures.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyzes endpoints for proper failOnStatusCodes structure."""
        # Check inbound endpoints
        if pmd_model.inboundEndpoints:
            for i, endpoint in enumerate(pmd_model.inboundEndpoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_fail_on_status_codes(endpoint, pmd_model, 'inbound', i)
        
        # Check outbound endpoints
        if pmd_model.outboundEndpoints:
            if isinstance(pmd_model.outboundEndpoints, list):
                for i, endpoint in enumerate(pmd_model.outboundEndpoints):
                    if isinstance(endpoint, dict):
                        yield from self._check_endpoint_fail_on_status_codes(endpoint, pmd_model, 'outbound', i)

    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyzes endpoints in POD seed configuration."""
        # Check POD endpoints (assuming they're inbound-type based on user guidance)
        if pod_model.seed.endPoints:
            for i, endpoint in enumerate(pod_model.seed.endPoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_fail_on_status_codes(endpoint, pod_model, 'pod', i)

    def _check_endpoint_fail_on_status_codes(self, endpoint, model, endpoint_type, index):
        """Check if an endpoint has proper failOnStatusCodes structure."""
        endpoint_name = endpoint.get('name')
        
        # Skip outbound endpoints that have variableScope (these are outboundVariables, not regular endpoints)
        if endpoint_type == 'outbound' and 'variableScope' in endpoint:
            return
        
        fail_on_status_codes = endpoint.get('failOnStatusCodes', None)
        
        # Check if failOnStatusCodes exists
        if fail_on_status_codes is None:
            line_number = self._get_endpoint_line_number(model, endpoint_name, endpoint_type)
            yield self._create_finding(
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' is missing required 'failOnStatusCodes' field.",
                file_path=model.file_path,
                line=line_number,
                # `field_insert`: location.path points to the endpoint object;
                # suggested_replacement is the new "key": value pair to add.
                suggested_replacement='"failOnStatusCodes": [{"code": 400}, {"code": 403}]',
                path=endpoint_jsonpath(endpoint_type, endpoint_name, index=index),
                replacement_context="field_insert",
            )
            return

        codes_found = set()
        for i, status_code_entry in enumerate(fail_on_status_codes):
            if isinstance(status_code_entry, dict):
                # Only check for 'code' field, ignore 'codeName' entirely
                if 'code' in status_code_entry:
                    code = status_code_entry['code']
                    # Convert to integer to handle both string and int values
                    try:
                        code_int = int(code)
                        codes_found.add(code_int)
                    except (ValueError, TypeError):
                        from utils.console import warn
                        warn(f"Invalid status code value '{code}' at index {i} in endpoint '{endpoint_name}' - must be a number")
                        continue
                # Silently ignore entries with 'codeName' or other unexpected structures
                continue
            else:
                from utils.console import warn
                warn(f"Unexpected failOnStatusCodes entry type at index {i} in endpoint '{endpoint_name}': {type(status_code_entry)} - {status_code_entry}")
                continue
        
        # Check for required codes 400 and 403 (as integers)
        required_codes = {400, 403}
        # Remove codes found from required codes. Empty set if all required codes are found.
        missing_codes = required_codes - codes_found
        
        # If there are missing codes, yield a finding
        if missing_codes:
            line_number = self._get_fail_on_status_codes_line_number(model, endpoint_name, endpoint_type)
            sorted_missing = sorted(missing_codes)
            missing_codes_str = ', '.join(map(str, sorted_missing))
            # Replacement is the entries to ADD, not the full array. Agent splices
            # into the existing array; any existing non-required codes (e.g. 500)
            # are preserved. Distinguishable from the field-missing case (above)
            # by the lack of the "failOnStatusCodes": and []  wrapper.
            replacement = ', '.join(f'{{"code": {c}}}' for c in sorted_missing)
            yield self._create_finding(
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' is missing required status codes: {missing_codes_str}.",
                file_path=model.file_path,
                line=line_number,
                # `array_splice`: location.path points to the failOnStatusCodes
                # array; suggested_replacement is the comma-separated elements
                # to insert. Existing entries (e.g., {"code": 500}) are preserved.
                suggested_replacement=replacement,
                path=endpoint_jsonpath(endpoint_type, endpoint_name, index=index, subkey='failOnStatusCodes'),
                replacement_context="array_splice",
            )

    def _get_endpoint_line_number(self, model, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the endpoint name field."""
        if endpoint_name and hasattr(model, 'source_content'):
            # For PMD models, use the unified method to find the name field
            if isinstance(model, PMDModel):
                return self.get_field_line_number(model, 'name', endpoint_name)
            # For POD models, return a basic line number (could be enhanced later)
            return 1
        return 1

    def _get_fail_on_status_codes_line_number(self, model, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the failOnStatusCodes field."""
        if endpoint_name and hasattr(model, 'source_content'):
            # For PMD models, use the unified method
            if isinstance(model, PMDModel):
                return self.get_field_after_entity_line_number(model, 'name', endpoint_name, 'failOnStatusCodes')
            # For POD models, return a basic line number (could be enhanced later)
            return 1
        return 1

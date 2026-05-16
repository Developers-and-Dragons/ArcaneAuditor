from ...base import Finding, FixStrategy, Category
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase
from utils.jsonpath import endpoint_jsonpath


class EndpointBaseUrlTypeRule(StructureRuleBase):
    """Ensures endpoint URLs don't include hardcoded workday.com or apiGatewayEndpoint values."""

    DESCRIPTION = "Ensures endpoint URLs for Workday APIs utilize dataProviders and baseUrlType"
    SEVERITY = "ADVICE"
    CATEGORY = Category.ENDPOINT
    FIX_STRATEGY = FixStrategy.HUMAN_REVIEW
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Workday APIs are heavily used within most Extend applications. Creating a re-usable definition in the AMD dataProviders array is recommended. When dataProviders are defined, developers can use `baseUrlType` on inbound and outbound endpoints (like 'workday-common' or 'workday-app'). This prevents the developer from explicitly including the entire URL both within and across pages. It has the added benefit of reducing the length of URLs on your endpoint definitions, making them easier to read and maintain.''',
        'catches': [
            'Hardcoded *.workday.com domains in endpoint URLs',
            'Hardcoded apiGatewayEndpoint values in URLs',
            'Endpoints that should use baseUrlType instead of Hardcoded values',
            'Both patterns promote extracting Workday endpoints to shared AMD data providers'
        ],
        'examples': '''**Example violations:**

```json
// Hardcoded workday.com URL
{
  "name": "getWorker",
  "url": "https://api.workday.com/common/v1/workers/me"  // ❌ Hardcoded workday.com
}

// Direct apiGatewayEndpoint usage
{
  "name": "getWorker",
  "url": "<% apiGatewayEndpoint + '/common/v1/workers/me' %>"  // ❌ Should use baseUrlType
}
```

**Fix:**

```json
{
  "name": "getWorker",
  "url": "/workers/me",  // ✅ Relative URL
  "baseUrlType": "workday-common"  // ✅ Use baseUrlType instead
}
```''',
        'recommendation': 'Extract Workday API endpoints to shared AMD dataProviders and use `baseUrlType` on endpoints instead of hardcoded URLs. This reduces duplication and makes URLs easier to read and maintain.'
    }

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext):
        """Analyzes endpoints for hardcoded URL violations."""
        # Check inbound endpoints
        if pmd_model.inboundEndpoints:
            for i, endpoint in enumerate(pmd_model.inboundEndpoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_url(endpoint, pmd_model, 'inbound', i)
        
        # Check outbound endpoints
        if pmd_model.outboundEndpoints:
            if isinstance(pmd_model.outboundEndpoints, list):
                for i, endpoint in enumerate(pmd_model.outboundEndpoints):
                    if isinstance(endpoint, dict):
                        yield from self._check_endpoint_url(endpoint, pmd_model, 'outbound', i)

    def visit_pod(self, pod_model: PodModel, context: ProjectContext):
        """Analyzes endpoints in POD seed configuration."""
        # Check POD endpoints for URL violations
        if pod_model.seed.endPoints:
            for i, endpoint in enumerate(pod_model.seed.endPoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_url(endpoint, pod_model, 'pod', i)

    def _check_endpoint_url(self, endpoint, model, endpoint_type, index):
        """Check if an endpoint URL contains hardcoded values."""
        endpoint_name = endpoint.get('name')
        url = endpoint.get('url', '')
        base_url_type = endpoint.get('baseUrlType', '')
        
        if not url:
            return
        
        # Check for hardcoded workday.com or apiGatewayEndpoint
        hardcoded_patterns = ['workday.com', 'apigatewayendpoint']
        found_patterns = []
        
        for pattern in hardcoded_patterns:
            if pattern in url.lower():
                found_patterns.append(pattern)
        
        if found_patterns:
            line_number = self._get_endpoint_url_line_number(model, endpoint_name, endpoint_type)
            
            yield self._create_finding(
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' is pointing to a Workday API, but not leveraging a baseUrlType. "
                       f"Extract Workday endpoints to shared AMD data providers to avoid duplication.",
                file_path=model.file_path,
                line=line_number,
                path=endpoint_jsonpath(endpoint_type, endpoint_name, index=index, subkey='baseUrlType'),
            )

    def _get_endpoint_url_line_number(self, model, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the endpoint URL field."""
        if endpoint_name and isinstance(model, PMDModel):
            # Use the existing base class method to find the URL field after the endpoint name
            return self.get_field_after_entity_line_number(model, 'name', endpoint_name, 'url')
        return 1

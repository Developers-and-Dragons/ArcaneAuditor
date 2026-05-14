from typing import Generator
from ...base import Finding, FixStrategy, Category
from ...common_validations import validate_lower_camel_case
from ...common import PMDLineUtils
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class EndpointNameLowerCamelCaseRule(StructureRuleBase):
    """Validates that endpoint names follow lowerCamelCase convention (style guide)."""

    ID = "EndpointNameLowerCamelCaseRule"
    DESCRIPTION = "Ensures endpoint names follow lowerCamelCase naming convention (style guide)"
    SEVERITY = "ADVICE"
    CATEGORY = Category.ENDPOINT
    FIX_STRATEGY = FixStrategy.CASCADING_RENAME
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''LowerCamelCase is the Workday Extend standard for endpoint names. Following the convention improves team collaboration and makes code more professional.''',
        'catches': [
            'Endpoint names that don\'t follow camelCase naming',
            'Inconsistent naming conventions across endpoints'
        ],
        'examples': '''**Example violations:**

```json
{
  "endPoints": [
    {
      "name": "get_user_data"  // ❌ snake_case
    }, 
    {
      "name": "GetUserProfile" // ❌ PascalCase
    }
  ]
}
```

**Fix:**

```json
{
  "endPoints": [
    {
      "name": "getUserData"    // ✅ lowerCamelCase
    }, 
    {
      "name": "getUserProfile" // ✅ lowerCamelCase
    }
  ]
}
```''',
        'recommendation': 'Use lowerCamelCase for all endpoint names to follow Workday Extend standards and improve code consistency.'
    }
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for endpoint name naming conventions."""
        # Check inbound endpoints
        if pmd_model.inboundEndpoints:
            for i, endpoint in enumerate(pmd_model.inboundEndpoints):
                if isinstance(endpoint, dict) and 'name' in endpoint:
                    yield from self._check_endpoint_naming(endpoint, pmd_model, 'inbound', i)
        
        # Check outbound endpoints
        if pmd_model.outboundEndpoints:
            if isinstance(pmd_model.outboundEndpoints, list):
                for i, endpoint in enumerate(pmd_model.outboundEndpoints):
                    if isinstance(endpoint, dict) and 'name' in endpoint:
                        yield from self._check_endpoint_naming(endpoint, pmd_model, 'outbound', i)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for endpoint name naming conventions."""
        if pod_model.seed.endPoints:
            for i, endpoint in enumerate(pod_model.seed.endPoints):
                if isinstance(endpoint, dict) and 'name' in endpoint:
                    yield from self._check_endpoint_naming(endpoint, None, 'pod_seed', i, pod_model)
    
    def _check_endpoint_naming(self, endpoint, pmd_model=None, context='inbound', index=0, pod_model=None):
        """Check if an endpoint name follows lowerCamelCase convention."""
        if not isinstance(endpoint, dict) or 'name' not in endpoint:
            return
        
        endpoint_name = endpoint.get('name', '')
        endpoint_type = f"{context} endpoint"
        
        # Validate the name follows lowerCamelCase convention
        validation_errors = validate_lower_camel_case(endpoint_name, 'name', endpoint_type, endpoint_name)
        
        if validation_errors:
            # Get line number
            line_number = 1
            if pmd_model:
                line_number = self._get_endpoint_line_number(pmd_model, endpoint_name)
            elif pod_model:
                line_number = self._get_pod_endpoint_line_number(pod_model, endpoint_name)
            
            yield self._create_finding(
                message=f"{endpoint_type.title()} '{endpoint_name}' doesn't follow naming conventions. Must follow lowerCamelCase convention (e.g., 'myField', 'userName').",
                file_path=pmd_model.file_path if pmd_model else pod_model.file_path,
                line=line_number
            )
    
    def _get_endpoint_line_number(self, pmd_model: PMDModel, endpoint_name: str) -> int:
        """Get line number for endpoint name field."""
        if endpoint_name:
            return self.get_field_line_number(pmd_model, 'name', endpoint_name)
        return 1
    
    def _get_pod_endpoint_line_number(self, pod_model: PodModel, endpoint_name: str) -> int:
        """Get line number for endpoint name field in POD."""
        if endpoint_name:
            return self.get_field_line_number(pod_model, 'name', endpoint_name)
        return 1

#!/usr/bin/env python3
"""Hardcoded Workday API rule."""

import re
from typing import Generator, List, Dict, Any
from parser.rules.structure.shared.rule_base import StructureRuleBase
from parser.rules.base import Finding, FixStrategy
from parser.models import ProjectContext, PMDModel, PodModel, AMDModel
from utils.jsonpath import data_provider_jsonpath, endpoint_jsonpath


class HardcodedWorkdayAPIRule(StructureRuleBase):
    """Rule to check for hardcoded *.workday.com URLs that should use apiGatewayEndpoint for regional awareness."""

    ID = "HardcodedWorkdayAPIRule"
    DESCRIPTION = "Detects hardcoded *.workday.com URLs that should use apiGatewayEndpoint for regional awareness"
    SEVERITY = "ACTION"
    FIX_STRATEGY = FixStrategy.ACTIONABLE
    AVAILABLE_SETTINGS = {}  # This rule does not support custom configuration
    
    DOCUMENTATION = {
        'why': '''Hardcoded workday.com URLs are not update safe and lack regional awareness. Using the `apiGatewayEndpoint` variable ensures your endpoints work across all environments and regions without code changes. If Workday adds additional regional endpoints or changes infrastructure, using the `apiGatewayEndpoint` application variable keeps your app update safe and regionally aware.''',
        'catches': [
            'Hardcoded *.workday.com URLs in AMD dataProviders',
            'Hardcoded *.workday.com URLs in PMD inbound and outbound endpoint URLs',
            'Hardcoded *.workday.com URLs in POD endpoint URLs',
            'URLs that should use apiGatewayEndpoint variable instead'
        ],
        'examples': '''**Example violations:**

```json
// AMD dataProvider
{
  "dataProviders": [
    {
      "key": "workday-common",
      "value": "https://api.workday.com/common/v1/"  // ❌ Hardcoded workday.com URL
    }
  ]
}

// PMD endpoint
{
  "name": "getWorker",
  "url": "https://api.workday.com/common/v1/workers/me"  // ❌ Hardcoded workday.com URL
}
```

**Fix:**

```json
// AMD dataProvider
{
  "dataProviders": [
    {
      "key": "workday-common",
      "value": "<% apiGatewayEndpoint + '/common/v1/' %>"  // ✅ Use apiGatewayEndpoint
    }
  ]
}

// PMD/POD endpoint
{
  "name": "getWorker",
  "url": "<% apiGatewayEndpoint + '/common/v1/workers/me' %>"  // ✅ Use apiGatewayEndpoint
}
```''',
        'recommendation': 'Use the `apiGatewayEndpoint` application variable instead of hardcoded *.workday.com URLs. This ensures your endpoints work across all environments and regions, and keeps your app update safe if Workday changes infrastructure.'
    }

    def __init__(self):
        """Initialize the rule."""
        super().__init__()
        # Pattern to match *.workday.com URLs (protocol optional)
        self.workday_url_pattern = re.compile(
            r'(?:https?://)?[a-zA-Z0-9.-]*\.workday\.com[^\s\'"]*',
            re.IGNORECASE
        )
        # Same pattern with the path captured, for building the replacement.
        self._workday_with_path = re.compile(
            r'(?:https?://)?[a-zA-Z0-9.-]*\.workday\.com([^\s\'"]*)',
            re.IGNORECASE
        )

    def _build_replacement(self, url: str):
        """Strip the workday.com host and wrap the remaining path in apiGatewayEndpoint."""
        m = self._workday_with_path.search(url)
        if not m:
            return None
        path = m.group(1)
        return f"<% apiGatewayEndpoint + '{path}' %>"

    def _build_swap(self, value: str):
        """Return (target_text, replacement) for a substring swap.

        Matches just the workday.com URL substring so the rule works whether
        the field is a bare URL (``"https://api.workday.com/..."``) or a value
        with surrounding context. Returns ``(None, None)`` if the URL can't
        be located — callers should treat that as 'enrichment unavailable'.
        """
        url_match = self.workday_url_pattern.search(value)
        if not url_match:
            return None, None
        target_text = url_match.group(0)
        replacement = self._build_replacement(target_text)
        return target_text, replacement
    
    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Main analysis entry point."""
        # Run analysis on available files
        yield from super().analyze(context)

    def visit_pmd(self, pmd_model, context: ProjectContext) -> Generator[Finding, None, None]:
        """Check PMD inbound and outbound endpoints for hardcoded *.workday.com URLs."""
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

    def visit_pod(self, pod_model, context: ProjectContext) -> Generator[Finding, None, None]:
        """Check POD endpoints for hardcoded *.workday.com URLs."""
        # Check POD endpoints for URL violations
        if pod_model.seed.endPoints:
            for i, endpoint in enumerate(pod_model.seed.endPoints):
                if isinstance(endpoint, dict):
                    yield from self._check_endpoint_url(endpoint, pod_model, 'pod', i)

    def visit_amd(self, amd_model, context: ProjectContext) -> Generator[Finding, None, None]:
        """
        Analyze AMD file for hardcoded *.workday.com URLs in dataProviders.
        
        Args:
            amd_model: AMD model from ProjectContext
            context: ProjectContext containing file information
            
        Yields:
            Finding objects for each violation
        """
        # Check if dataProviders exist in the AMD model
        data_providers = amd_model.dataProviders or []
        if not data_providers:
            return
        
        # Check each dataProvider
        for provider in data_providers:
            if not isinstance(provider, dict):
                continue
                
            key = provider.get("key", "")
            value = provider.get("value", "")
            
            if not isinstance(value, str):
                continue
            
            # Check if the value contains hardcoded *.workday.com URLs
            target_text, replacement = self._build_swap(value)
            if target_text is not None:
                line_number = self._get_amd_data_provider_line_number(amd_model, key, value)
                finding = Finding(
                    rule=self,
                    message=f"AMD dataProvider '{key}' uses hardcoded *.workday.com URL: '{value}'. "
                           f"Use apiGatewayEndpoint instead of hardcoded Workday URLs for regional awareness.",
                    line=line_number,
                    file_path=amd_model.file_path,
                    suggested_replacement=replacement,
                    path=data_provider_jsonpath(key),
                    target_text=target_text,
                    replacement_context="substring",
                )
                yield finding

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def _check_endpoint_url(self, endpoint, model, endpoint_type, index):
        """Check if an endpoint URL contains hardcoded *.workday.com URLs."""
        endpoint_name = endpoint.get('name')
        url = endpoint.get('url', '')
        
        if not url:
            return
        
        # Check for hardcoded *.workday.com URLs
        target_text, replacement = self._build_swap(url)
        if target_text is not None:
            line_number = self._get_endpoint_url_line_number(model, endpoint_name, endpoint_type)

            yield self._create_finding(
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' uses hardcoded *.workday.com URL: '{url}'. "
                       f"Use apiGatewayEndpoint instead of hardcoded Workday URLs for regional awareness.",
                file_path=model.file_path,
                line=line_number,
                suggested_replacement=replacement,
                path=endpoint_jsonpath(endpoint_type, endpoint_name, index=index, subkey='url'),
                target_text=target_text,
                replacement_context="substring",
            )

    def _get_endpoint_url_line_number(self, model, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the endpoint URL field."""
        if endpoint_name and hasattr(model, 'source_content') and model.source_content:
            # For PMD models, use the existing base class method
            if hasattr(model, 'pageId'):  # PMDModel has pageId
                return self.get_field_after_entity_line_number(model, 'name', endpoint_name, 'url')
            # For POD models, use a simpler pattern search
            else:
                return self.find_pattern_line_number(model, f'"{endpoint_name}"')
        return 1
    
    def _get_amd_data_provider_line_number(self, amd_model, provider_key: str, provider_value: str) -> int:
        """Get line number for AMD dataProvider with hardcoded URL."""
        if hasattr(amd_model, 'source_content') and amd_model.source_content:
            # Search for the actual URL value in the source content for more accurate line number
            return self.find_pattern_line_number(amd_model, provider_value)
        return 1

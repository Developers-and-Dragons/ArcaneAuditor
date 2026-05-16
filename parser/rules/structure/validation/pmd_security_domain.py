from typing import Generator
from ...base import Rule, Finding
from ....models import ProjectContext, PMDModel


class PMDSecurityDomainRule(Rule):
    """Ensures PMD pages have required security domains with selective exclusions."""
    
    DESCRIPTION = "Ensures PMD pages have at least one security domain defined (excludes microConclusion and error pages unless strict mode is enabled)"
    SEVERITY = "ACTION"
    AVAILABLE_SETTINGS = {
        'strict': {'type': 'bool', 'default': False, 'description': 'When enabled, requires security domains for ALL PMD pages, including microConclusion and error pages'}
    }
    
    DOCUMENTATION = {
        'why': '''Security domains control who can access your PMD pages in Workday. Missing security domains means your page is accessible to all users, which could lead to a security incident.

**Smart Exclusions (configurable):**
- **MicroConclusion pages**: Pages with `presentation.microConclusion: true` are excluded (unless strict mode)
- **Error pages**: Pages whose ID appears in SMD `errorPageConfigurations` are excluded (unless strict mode)''',
        'catches': [
            'PMD pages missing `securityDomains` list',
            'Empty `securityDomains` arrays',
            'Enforces security best practices for Workday applications'
        ],
        'examples': '''**Example violations:**

```javascript
// ❌ Missing security domains
{
  "id": "myPage",
  "presentation": {
    "body": { ... }
  }
}

// ✅ Proper security domains
{
  "id": "myPage", 
  "securityDomains": ["ViewAdminPages"],
  "presentation": {
    "body": { ... }
  }
}

// ✅ MicroConclusion page (excluded in normal mode)
{
  "id": "microPage",
  "presentation": {
    "microConclusion": true,
    "body": { ... }
  }
}
```''',
        'recommendation': 'Always define at least one security domain for PMD pages to control access and prevent security incidents. Use strict mode to enforce security domains on all pages, including microConclusion and error pages.'
    }

    def __init__(self):
        super().__init__()
        self.strict_mode = False  # Default to non-strict mode

    def apply_settings(self, custom_settings: dict):
        """Apply custom settings from configuration."""
        if 'strict' in custom_settings:
            self.strict_mode = custom_settings['strict']
    
    def get_description(self) -> str:
        """Get rule description."""
        if self.strict_mode:
            return "Ensures ALL PMD pages have at least one security domain defined (strict mode - no exclusions)"
        return self.DESCRIPTION

    def analyze(self, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze all PMD models for security domain requirements."""
        # Register skipped check once if SMD is missing (not per PMD file)
        if not context.smd and not self.strict_mode:
            context.register_skipped_check(
                rule_name="PMDSecurityDomainRule",
                check_name="error_page_exclusion",
                reason="Requires SMD file"
            )
        
        for pmd_model in context.pmds.values():
            yield from self.visit_pmd(pmd_model, context)

    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Check if a PMD model has required security domains with selective exclusions."""
        # In strict mode, skip all exclusions and require security domains for ALL pages
        if not self.strict_mode:
            # Check if this page should be excluded from security domain requirements
            
            # Exclusion 1: MicroConclusion pages (presentation.microConclusion: true)
            if self._is_micro_conclusion_page(pmd_model):
                return  # Skip security domain check for microConclusion pages
            
            # Exclusion 2: Error pages (page ID in SMD errorPageConfigurations)
            if self._is_error_page(pmd_model, context):
                return  # Skip security domain check for error pages
        
        # Check if securityDomains is missing or empty for pages that require it
        # The compiler ensures domain validity, so we only check for presence
        if not pmd_model.securityDomains or len(pmd_model.securityDomains) == 0:
            if self.strict_mode:
                message = "PMD page is missing required securityDomains list. ALL PMD pages must define at least one security domain (strict mode enabled)."
            else:
                message = "PMD page is missing required securityDomains list. All PMD pages must define at least one security domain (excludes microConclusion and error pages)."
            
            yield Finding(
                rule=self,
                file_path=pmd_model.file_path,
                line=1,  # Security domains are typically defined at the top of PMD files
                message=message,
                path="$.securityDomains",
            )
    
    def _is_micro_conclusion_page(self, pmd_model: PMDModel) -> bool:
        """Check if the PMD page is a microConclusion page."""
        if not pmd_model.presentation:
            return False
        
        # Check if presentation.microConclusion is true
        # microConclusion is stored in the attributes dictionary
        return pmd_model.presentation.attributes.get('microConclusion', False) is True
    
    def _is_error_page(self, pmd_model: PMDModel, context: ProjectContext) -> bool:
        """Check if the PMD page is an error page defined in any SMD."""
        if not context.smd:
            # SMD is missing - already registered in analyze()
            return False  # Treat as non-error page (conservative)
        
        # Get all error page IDs from the SMD file
        error_page_ids = set()
        error_pages = context.smd.get_error_pages()
        for error_page in error_pages:
            page_id = error_page.get('pageId', '')
            if page_id:
                error_page_ids.add(page_id)
        
        # Check if this PMD's pageId is in the error pages list
        return pmd_model.pageId in error_page_ids

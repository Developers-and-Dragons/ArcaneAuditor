"""
Rule to detect hardcoded applicationId values in PMD and POD files.

The applicationId value from the SMD file should never be hardcoded in PMD or POD files.
Instead, users should use the site.applicationId variable.

Note: AMD files are allowed to have applicationId as they are application configuration files.
"""
import re
from typing import Generator, List, Dict, Any, Optional

from ...base import Finding
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class HardcodedApplicationIdRule(StructureRuleBase):
    """
    Detects hardcoded applicationId values that should be replaced with site.applicationId.
    
    This rule checks for:
    - Hardcoded applicationId strings in JSON values
    - Hardcoded applicationId strings in script expressions
    - Any string literal containing the applicationId value
    """
    
    ID = "HardcodedApplicationIdRule"
    DESCRIPTION = "Detects hardcoded applicationId values that should be replaced with site.applicationId"
    SEVERITY = "ADVICE"
    
    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze PMD model for hardcoded applicationId values."""
        if not context.application_id:
            return  # No applicationId to check against
        
        yield from self._check_pmd_hardcoded_app_id(pmd_model, context.application_id)
    
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyze POD model for hardcoded applicationId values."""
        if not context.application_id:
            return  # No applicationId to check against
        
        yield from self._check_pod_hardcoded_app_id(pod_model, context.application_id)
    
    def _check_pmd_hardcoded_app_id(self, pmd_model: PMDModel, app_id: str) -> Generator[Finding, None, None]:
        """Check PMD file for hardcoded applicationId values."""
        # Use original source content for accurate line numbers
        if pmd_model.source_content:
            yield from self._check_source_content_for_app_id(pmd_model.source_content, app_id, pmd_model.file_path)
        else:
            # Fallback to dictionary checking if no source content
            pmd_dict = pmd_model.model_dump(exclude={'file_path', 'source_content'})
            yield from self._check_string_values_for_app_id(pmd_dict, app_id, pmd_model.file_path, pmd_model=pmd_model)
    
    def _check_pod_hardcoded_app_id(self, pod_model: PodModel, app_id: str) -> Generator[Finding, None, None]:
        """Check POD file for hardcoded applicationId values."""
        # Convert POD model to dictionary for recursive checking
        pod_dict = pod_model.model_dump(exclude={'file_path', 'source_content'})
        yield from self._check_string_values_for_app_id(pod_dict, app_id, pod_model.file_path, pod_model=pod_model)
    
    def _check_source_content_for_app_id(self, source_content: str, app_id: str, file_path: str) -> Generator[Finding, None, None]:
        """Check source content for hardcoded applicationId values."""
        if not source_content or not app_id:
            return
        
        # Use a single comprehensive pattern that matches all variations
        # This pattern will match:
        # - "applicationId": "template_nkhlsq"
        # - 'applicationId': 'template_nkhlsq'
        # - "template_nkhlsq"
        # - 'template_nkhlsq'
        # - template_nkhlsq (with word boundaries)
        comprehensive_pattern = rf'(?:["\']applicationId["\']\s*:\s*)?["\']?{re.escape(app_id)}["\']?'
        
        matches = re.finditer(comprehensive_pattern, source_content, re.IGNORECASE)
        for match in matches:
            # Skip if this is already using site.applicationId correctly
            context_before = source_content[max(0, match.start() - 50):match.start()]
            context_after = source_content[match.end():min(len(source_content), match.end() + 50)]
            
            # If we see site.applicationId nearby, this might be correct usage
            if 'site.applicationId' in context_before or 'site.applicationId' in context_after:
                continue
            
            # Calculate line number from position in source content
            line_num = self.get_line_from_text_position(source_content, match.start())
            
            yield self._create_finding(
                message=f"Hardcoded applicationId '{app_id}' found. Use site.applicationId instead.",
                file_path=file_path,
                line=line_num
            )
    
    def _check_string_values_for_app_id(self, model: Any, app_id: str, file_path: str, pmd_model: PMDModel = None, pod_model: PodModel = None) -> Generator[Finding, None, None]:
        """Recursively check string values for hardcoded applicationId."""
        if isinstance(model, dict):
            for key, value in model.items():
                if isinstance(value, str):
                    yield from self._check_string_for_app_id(value, app_id, file_path, key, pmd_model, pod_model)
                elif isinstance(value, (dict, list)):
                    yield from self._check_string_values_for_app_id(value, app_id, file_path, pmd_model, pod_model)
        elif isinstance(model, list):
            for i, item in enumerate(model):
                if isinstance(item, str):
                    yield from self._check_string_for_app_id(item, app_id, file_path, f"[{i}]", pmd_model, pod_model)
                elif isinstance(item, (dict, list)):
                    yield from self._check_string_values_for_app_id(item, app_id, file_path, pmd_model, pod_model)
    
    def _check_string_for_app_id(self, text: str, app_id: str, file_path: str, field_name: str, pmd_model: PMDModel = None, pod_model: PodModel = None) -> Generator[Finding, None, None]:
        """Check a single string for hardcoded applicationId values."""
        if not text or not app_id:
            return
        
        # Use a single comprehensive pattern that matches all variations
        # This pattern will match:
        # - "applicationId": "template_nkhlsq"
        # - 'applicationId': 'template_nkhlsq'
        # - "template_nkhlsq"
        # - 'template_nkhlsq'
        # - template_nkhlsq (with word boundaries)
        comprehensive_pattern = rf'(?:["\']applicationId["\']\s*:\s*)?["\']?{re.escape(app_id)}["\']?'
        
        matches = re.finditer(comprehensive_pattern, text, re.IGNORECASE)
        for match in matches:
            # Skip if this is already using site.applicationId correctly
            context_before = text[max(0, match.start() - 50):match.start()]
            context_after = text[match.end():min(len(text), match.end() + 50)]
            
            # If we see site.applicationId nearby, this might be correct usage
            if 'site.applicationId' in context_before or 'site.applicationId' in context_after:
                continue
            
            # Calculate line number using the base class method
            line_num = self.get_line_from_text_position(text, match.start())
            
            yield self._create_finding(
                message=f"Hardcoded applicationId '{app_id}' found in {field_name}. Use site.applicationId instead.",
                file_path=file_path,
                line=line_num
            )

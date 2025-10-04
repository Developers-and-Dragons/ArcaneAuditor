from typing import Generator
from ...base import Finding
from ...common import PMDLineUtils
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class FooterPodRequiredRule(StructureRuleBase):
    """Ensures footer uses pod structure - either direct pod or footer with pod children."""
    
    DESCRIPTION = "Ensures footer uses pod structure (direct pod or footer with pod children). Excludes PMD pages with tabs, hub pages, and microConclusion pages."
    SEVERITY = "ADVICE"

    def get_description(self) -> str:
        """Get rule description."""
        return self.DESCRIPTION
    
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """Analyzes the footer structure within a PMD model."""
        if not pmd_model.presentation:
            return

        # Skip PMD pages that use tabs - tabs don't require footer pods
        # Check if tabs section exists (None means no tabs, [] or populated means tabs exist)
        if hasattr(pmd_model.presentation, 'tabs') and pmd_model.presentation.tabs is not None:
            return

        # Skip hub pages - hub pages don't require footer pods
        if self._is_hub_page(pmd_model):
            return

        # Skip microConclusion pages - microConclusion pages don't require footer pods
        if self._is_micro_conclusion_page(pmd_model):
            return

        footer = pmd_model.presentation.footer
        if not isinstance(footer, dict):
            return

        # Check if footer is missing entirely or empty
        if not footer or len(footer) == 0:
            yield self._create_finding(
                message="Footer section is missing. Footer should use pod structure.",
                file_path=pmd_model.file_path,
                line=1
            )
            return

        # Check if footer uses direct pod structure
        if footer.get('type') == 'pod':
            return  # Valid pod structure

        # Check if footer uses footer type with pod children
        if footer.get('type') == 'footer':
            children = footer.get('children', [])
            if not isinstance(children, list) or len(children) == 0:
                line_number = self._get_footer_line_number(pmd_model)
                yield self._create_finding(
                    message="Footer must utilize a pod.",
                    file_path=pmd_model.file_path,
                    line=line_number
                )
                return

            # Check if the first (and only expected) child is a pod
            if len(children) > 0:
                child = children[0]
                if isinstance(child, dict) and child.get('type') == 'pod':
                    return  # Valid pod child
                else:
                    line_number = self._get_footer_line_number(pmd_model)
                    yield self._create_finding(
                        message="Footer must utilize a pod.",
                        file_path=pmd_model.file_path,
                        line=line_number
                    )
            else:
                line_number = self._get_footer_line_number(pmd_model)
                yield self._create_finding(
                    message="Footer must utilize a pod.",
                    file_path=pmd_model.file_path,
                    line=line_number
                )
            return

        # If we get here, footer has invalid structure
        line_number = self._get_footer_line_number(pmd_model)
        yield self._create_finding(
            message="Footer must utilize a pod.",
            file_path=pmd_model.file_path,
            line=line_number
        )

    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        """POD files don't have footers, so this rule doesn't apply to them."""
        return
        yield  # This line will never be reached, but makes it a generator

    def _get_footer_line_number(self, pmd_model: PMDModel) -> int:
        """Get approximate line number for the footer section."""
        return PMDLineUtils.find_section_line_number(pmd_model, 'footer')

    def _is_hub_page(self, pmd_model: PMDModel) -> bool:
        """Check if the PMD page is a hub page."""
        if not pmd_model.presentation or not pmd_model.presentation.body:
            return False
        
        # Check if presentation.body.type == "hub"
        return pmd_model.presentation.body.get('type') == 'hub'

    def _is_micro_conclusion_page(self, pmd_model: PMDModel) -> bool:
        """Check if the PMD page is a microConclusion page."""
        if not pmd_model.presentation:
            return False
        
        # Check if presentation.microConclusion is true
        # microConclusion is stored in the attributes dictionary
        return pmd_model.presentation.attributes.get('microConclusion', False) is True

from typing import Generator
from ...base import Finding
from ...line_number_utils import LineNumberUtils
from ....models import PMDModel, PodModel, ProjectContext
from ..shared import StructureRuleBase


class EndpointFailOnStatusCodesRule(StructureRuleBase):
    """Ensures endpoints have proper failOnStatusCodes structure with required codes 400 and 403."""
    
    DESCRIPTION = "Ensures endpoints have failOnStatusCodes with minimum required codes 400 and 403"
    SEVERITY = "SEVERE"

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
        fail_on_status_codes = endpoint.get('failOnStatusCodes', None)
        
        # Check if failOnStatusCodes exists
        if fail_on_status_codes is None:
            line_number = self._get_endpoint_line_number(model, endpoint_name, endpoint_type)
            yield self._create_finding(
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' is missing required 'failOnStatusCodes' field.",
                file_path=model.file_path,
                line=line_number
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
                        print(f"Warning: Invalid status code value '{code}' at index {i} in endpoint '{endpoint_name}' - must be a number")
                        continue
                # Silently ignore entries with 'codeName' or other unexpected structures
                continue
            else:
                print(f"Warning: Unexpected failOnStatusCodes entry type at index {i} in endpoint '{endpoint_name}': {type(status_code_entry)} - {status_code_entry}")
                continue
        
        # Check for required codes 400 and 403 (as integers)
        required_codes = {400, 403}
        # Remove codes found from required codes. Empty set if all required codes are found.
        missing_codes = required_codes - codes_found
        
        # If there are missing codes, yield a finding
        if missing_codes:
            line_number = self._get_fail_on_status_codes_line_number(model, endpoint_name, endpoint_type)
            missing_codes_str = ', '.join(map(str, sorted(missing_codes)))
            yield self._create_finding(
                message=f"{endpoint_type.title()} endpoint '{endpoint_name}' is missing required status codes: {missing_codes_str}.",
                file_path=model.file_path,
                line=line_number
            )

    def _get_endpoint_line_number(self, model, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the endpoint."""
        if endpoint_name and hasattr(model, 'source_content'):
            # For PMD models, use the existing line number utility
            if isinstance(model, PMDModel):
                return LineNumberUtils.find_field_line_number(model, 'name', endpoint_name)
            # For POD models, return a basic line number (could be enhanced later)
            return 1
        return 1

    def _get_fail_on_status_codes_line_number(self, model, endpoint_name: str, endpoint_type: str) -> int:
        """Get line number for the failOnStatusCodes field."""
        if endpoint_name and hasattr(model, 'source_content'):
            # For PMD models, use the existing line number utility
            if isinstance(model, PMDModel):
                return LineNumberUtils.find_field_after_entity(model, 'name', endpoint_name, 'failOnStatusCodes')
            # For POD models, return a basic line number (could be enhanced later)
            return 1
        return 1

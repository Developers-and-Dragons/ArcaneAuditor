"""Rule to require non-empty security domains for Sync and Async orchestrations."""

from typing import Generator
from ...base import Finding, Rule
from ....models import ProjectContext, PMDModel, PodModel, OrchestrationModel
from ..shared import StructureRuleBase


# Flow type values from orchestration JSON
FLOW_SYNC = ".maya.FlowSync"
FLOW_ASYNC = ".maya.FlowAsync"


class OrchestrationSecurityDomainRule(StructureRuleBase):
    """Requires Sync and Async orchestrations to have a security domain."""

    ID = "OrchestrationSecurityDomainRule"
    DESCRIPTION = "Ensures Synchronous and Asynchronous orchestrations have a security domain defined"
    SEVERITY = "ACTION"
    AVAILABLE_SETTINGS = {}

    DOCUMENTATION = {
        "why": "Security domains control access to orchestrations. Sync and Async orchestrations must define a security domain.",
        "catches": [
            "Sync/Async orchestrations with missing securityDomain"
        ],
        "examples": "Orchestration 'myFlow' is missing required securityDomain (Sync/Async only). Business Process and Integration flows are not checked.",
        "recommendation": "Add a security domain to Sync and Async orchestrations.",
    }

    def get_description(self) -> str:
        return self.DESCRIPTION

    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        yield from ()

    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        yield from ()

    def visit_orchestration(
        self, orch_model: OrchestrationModel, context: ProjectContext
    ) -> Generator[Finding, None, None]:
        if orch_model.flow_type not in (FLOW_SYNC, FLOW_ASYNC):
            return
        if orch_model.security_domains is None or len(orch_model.security_domains) == 0:
            name = orch_model.name or orch_model.id or "orchestration"
            yield Finding(
                rule=self,
                file_path=orch_model.file_path,
                line=1,
                message=f"Orchestration '{name}' must define a security domain.",
            )

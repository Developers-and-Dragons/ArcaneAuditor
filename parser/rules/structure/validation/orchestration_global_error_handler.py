"""Rule to require a global error handler for orchestrations (Sync, Async, BPT, Integration)."""

from typing import Generator
from ...base import Finding
from ....models import ProjectContext, PMDModel, PodModel, OrchestrationModel
from ..shared import StructureRuleBase


FLOW_SUBFLOW = ".maya.FlowSubflow"


def _has_global_error_handler(raw_value: dict) -> bool:
    """Return True if the flow has a non-null global errorHandler (flow-level)."""
    obj = raw_value.get("errorHandler")
    value = obj.get("_value") if isinstance(obj, dict) and "_value" in obj else obj
    return value is not None


class OrchestrationGlobalErrorHandlerRule(StructureRuleBase):
    """Requires orchestrations (Sync, Async, BPT, Integration) to have a global error handler."""

    ID = "OrchestrationGlobalErrorHandlerRule"
    DESCRIPTION = "Ensures orchestrations have a global error handler for uncaught or propagated errors"
    SEVERITY = "ACTION"
    AVAILABLE_SETTINGS = {}

    DOCUMENTATION = {
        "why": "A global error handler is required in case an uncaught error occurs or a local error handler propagates the error, with no upstream handler to catch it.",
        "catches": [
            "Orchestrations (Sync, Async, BPT, Integration) with missing global errorHandler"
        ],
        "examples": "Orchestration 'myFlow' must define a global error handler. Suborchestrations are not checked.",
        "recommendation": "Add a global error handler to the orchestration.",
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
        if orch_model.flow_type == FLOW_SUBFLOW:
            return
        if not _has_global_error_handler(orch_model.raw_value):
            name = orch_model.name or orch_model.id or "orchestration"
            yield Finding(
                rule=self,
                file_path=orch_model.file_path,
                line=1,
                message=f"Orchestration '{name}' must have a global error handler.",
            )

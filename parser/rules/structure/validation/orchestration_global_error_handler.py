"""Rule to require a global error handler for orchestrations (Sync, Async, BPT, Integration)."""

from typing import Generator
from ...base import Finding, FixStrategy, Category
from ....models import ProjectContext, PMDModel, PodModel, OrchestrationModel
from ..shared import StructureRuleBase
from ..shared.orchestration_error_handler_utils import (
    FLOW_INTEGRATION,
    get_error_handler_nodes,
    handler_has_log_or_integration_step,
    handler_has_log_step,
    unwrap,
)

FLOW_SUBFLOW = ".maya.FlowSubflow"


def _has_global_error_handler(raw_value: dict) -> bool:
    """Return True if the flow has a non-null global errorHandler (flow-level)."""
    obj = raw_value.get("errorHandler")
    value = unwrap(obj) if isinstance(obj, dict) else obj
    return value is not None


def _global_handler_has_required_step(raw_value: dict, flow_type: str) -> bool:
    """Return True if the global error handler has a log step (or SendIntegrationMessage for Integration flows)."""
    obj = raw_value.get("errorHandler")
    if obj is None:
        return False
    nodes = get_error_handler_nodes(obj)
    if not nodes:
        return False
    if flow_type == FLOW_INTEGRATION:
        return handler_has_log_or_integration_step(nodes)
    return handler_has_log_step(nodes)


class OrchestrationGlobalErrorHandlerRule(StructureRuleBase):
    """Requires orchestrations to have a global error handler that contains a log step (or Add Integration Message for Integration templates)."""

    ID = "OrchestrationGlobalErrorHandlerRule"
    DESCRIPTION = "Ensures orchestrations have a global error handler with a log step (or Add Integration Message for Integration templates)"
    SEVERITY = "ACTION"
    CATEGORY = Category.ORCHESTRATION
    FIX_STRATEGY = FixStrategy.DESIGN_DECISION
    AVAILABLE_SETTINGS = {}

    DOCUMENTATION = {
        "why": "A global error handler is required in case an uncaught error occurs or a local error handler propagates the error; it must contain a log step (or Add Integration Message step for Integration templates) to record the failure.",
        "catches": [
            "Orchestrations (Sync, Async, BPT, Integration) with missing global errorHandler",
            "Orchestrations whose global error handler has no log step (or no Add Integration Message step for Integration templates)",
        ],
        "examples": "Orchestration 'myFlow' must define a global error handler with at least one Log step (or Add Integration Message for Integration templates). Suborchestrations are not checked.",
        "recommendation": "Add a global error handler and include a Log step (or Add Integration Message step for Integration templates) inside it.",
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
        raw = orch_model.raw_value
        name = orch_model.name or orch_model.id or "orchestration"
        if not _has_global_error_handler(raw):
            yield Finding(
                rule=self,
                file_path=orch_model.file_path,
                line=1,
                message=f"Orchestration '{name}' must have a global error handler.",
            )
            return
        if not _global_handler_has_required_step(raw, orch_model.flow_type):
            yield Finding(
                rule=self,
                file_path=orch_model.file_path,
                line=1,
                message=f"Orchestration '{name}' global error handler must contain a log step (or Add Integration Message step for Integration templates).",
            )

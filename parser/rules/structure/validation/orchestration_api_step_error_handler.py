"""Rule to require a local error handler on every API step in orchestrations."""

from typing import Generator, List, Any
from ...base import Finding
from ....models import ProjectContext, PMDModel, PodModel, OrchestrationModel
from ..shared import StructureRuleBase


API_STEP_NODE_TYPES = frozenset({
    "SendWwsPaginationApiRequest",
    "SendHttpPaginationRequest",
    "SendHttpRequest",
    "SendWorkdayApiRequest",
    "SendWorkdayRestApiPaginationRequest",
})


def _unwrap(obj: Any) -> Any:
    """Unwrap typed envelope: return obj['_value'] if obj is a dict with _value."""
    if obj is None:
        return None
    if isinstance(obj, dict) and "_value" in obj:
        return obj["_value"]
    return obj


def _unwrap_nodes_list(nodes_obj: Any) -> List[dict]:
    """Return list of node dicts from a nodes envelope (e.g. flow nodes or group nodes)."""
    if nodes_obj is None:
        return []
    val = _unwrap(nodes_obj)
    if isinstance(val, list):
        return val
    return []


def _get_child_node_lists(node_value: dict) -> List[list]:
    """Given a node's _value dict, return zero or more child node lists to traverse."""
    if not isinstance(node_value, dict):
        return []
    out: List[list] = []

    # Loop: group -> unwrap -> nodes -> unwrap
    group = node_value.get("group")
    if group is not None:
        group_val = _unwrap(group)
        if isinstance(group_val, dict):
            nodes = group_val.get("nodes")
            lst = _unwrap_nodes_list(nodes)
            if lst:
                out.append(lst)

    # BranchOnConditions: ifBranches and elseBranch
    if node_value.get("_type") == "BranchOnConditions" or "ifBranches" in node_value:
        if_branches = node_value.get("ifBranches")
        if if_branches is not None:
            branches_list = _unwrap(if_branches)
            if isinstance(branches_list, list):
                for when_branch in branches_list:
                    wb_val = _unwrap(when_branch) if isinstance(when_branch, dict) else when_branch
                    if isinstance(wb_val, dict):
                        g = wb_val.get("group")
                        g_val = _unwrap(g) if g is not None else None
                        if isinstance(g_val, dict):
                            nlst = _unwrap_nodes_list(g_val.get("nodes"))
                            if nlst:
                                out.append(nlst)
        else_branch = node_value.get("elseBranch")
        if else_branch is not None:
            eb_val = _unwrap(else_branch)
            if isinstance(eb_val, dict):
                nlst = _unwrap_nodes_list(eb_val.get("nodes"))
                if nlst:
                    out.append(nlst)

    # Any node_value with "nodes" (ImplicitGroup, Group, ErrorHandler)
    if "nodes" in node_value:
        nlst = _unwrap_nodes_list(node_value["nodes"])
        if nlst:
            out.append(nlst)

    return out


def _has_local_error_handler(node_value: dict) -> bool:
    """Return True if the node has a non-null local errorHandler."""
    err = node_value.get("errorHandler")
    val = _unwrap(err)
    return val is not None


def _node_name(node_value: dict) -> str:
    """Get display name from node _value (unwrap Identifier)."""
    name_node = node_value.get("name")
    val = _unwrap(name_node)
    if isinstance(val, str):
        return val
    return ""


class OrchestrationApiStepErrorHandlerRule(StructureRuleBase):
    """Requires every API step in an orchestration to have a local error handler."""

    ID = "OrchestrationApiStepErrorHandlerRule"
    DESCRIPTION = "Ensures every API step has a local error handler for network/transient failures"
    SEVERITY = "ACTION"
    AVAILABLE_SETTINGS = {}

    DOCUMENTATION = {
        "why": "API steps can fail due to network or transient errors; a local error handler allows the flow to handle or propagate failures explicitly.",
        "catches": [
            "API steps (SendHttpRequest, SendWorkdayApiRequest, etc.) without a node-level errorHandler"
        ],
        "examples": "API step 'SendHTTPRequest' must have a local error handler.",
        "recommendation": "Add a local error handler to each API step.",
    }

    def get_description(self) -> str:
        return self.DESCRIPTION

    # No-op for PMD files
    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        yield from ()

    # No-op for POD files
    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        yield from ()

    # Traverse the node list and check each node for API step + local handler; recurse into child node lists.
    def _visit_node_list(
        self,
        nodes: list,
        file_path: str,
        orch_name: str,
    ) -> Generator[Finding, None, None]:
        """Check each node for API step + local handler; recurse into child node lists."""
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_type = node.get("_type")
            node_value = node.get("_value")
            if not isinstance(node_value, dict):
                continue
            if node_type in API_STEP_NODE_TYPES:
                if not _has_local_error_handler(node_value):
                    step_name = _node_name(node_value) or node_type
                    yield Finding(
                        rule=self,
                        file_path=file_path,
                        line=1,
                        message=f"API step '{step_name}' must have a local error handler.",
                    )
            for child_list in _get_child_node_lists(node_value):
                yield from self._visit_node_list(child_list, file_path, orch_name)

    def visit_orchestration(
        self, orch_model: OrchestrationModel, context: ProjectContext
    ) -> Generator[Finding, None, None]:
        raw = orch_model.raw_value
        nodes_list = _unwrap_nodes_list(raw.get("nodes"))
        file_path = orch_model.file_path
        name = orch_model.name or orch_model.id or "orchestration"
        yield from self._visit_node_list(nodes_list, file_path, name)

"""Rule to limit Branch on Conditions nesting depth in orchestrations."""

from typing import Any, Generator, List, Optional, Tuple
from ...base import Finding, Category
from ....models import ProjectContext, PMDModel, PodModel, OrchestrationModel
from ..shared import StructureRuleBase


BRANCH_ON_CONDITIONS_TYPE = "BranchOnConditions"


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


def _node_name(node_value: dict) -> str:
    """Get display name from node _value (unwrap Identifier)."""
    name_node = node_value.get("name")
    val = _unwrap(name_node)
    if isinstance(val, str):
        return val
    return ""


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
    if node_value.get("_type") == BRANCH_ON_CONDITIONS_TYPE or "ifBranches" in node_value:
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


class OrchestrationBranchOnConditionsNestingRule(StructureRuleBase):
    """Limits Branch on Conditions nesting to 3 levels for readability; deeper nesting suggests extracting to a suborchestration."""

    ID = "OrchestrationBranchOnConditionsNestingRule"
    DESCRIPTION = "Limits Branch on Conditions nesting to 3 levels for readability; deeper nesting suggests extracting to a suborchestration"
    SEVERITY = "ADVICE"
    CATEGORY = Category.ORCHESTRATION
    AVAILABLE_SETTINGS = {}

    DOCUMENTATION = {
        "why": "Deeply nested Branch on Conditions make flows hard to follow; keeping nesting to 3 levels and extracting logic to a suborchestration improves clarity.",
        "catches": [
            "Orchestrations or suborchestrations with a top-level Branch on Conditions whose branch nests BoC deeper than 3 levels (reported per top-level branch)",
        ],
        "examples": "Branch on Conditions 'MyBoC' has a branch nested at 5 levels; consider extracting logic to a suborchestration to keep nesting to 3 levels or fewer.",
        "recommendation": "Extract logic to a suborchestration to keep Branch on Conditions nesting to 3 levels or fewer.",
    }

    def get_description(self) -> str:
        return self.DESCRIPTION

    def visit_pmd(self, pmd_model: PMDModel, context: ProjectContext) -> Generator[Finding, None, None]:
        yield from ()

    def visit_pod(self, pod_model: PodModel, context: ProjectContext) -> Generator[Finding, None, None]:
        yield from ()

    def _visit_branch(
        self,
        nodes: list,
        file_path: str,
        depth: int,
        parent_boc_name: Optional[str],
    ) -> Tuple[List[Finding], int]:
        """Traverse a node list (a 'branch'), return (findings, max_depth_seen). Emit one finding per BoC branch whose max depth > 3."""
        findings: List[Finding] = []
        max_seen = depth

        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_type = node.get("_type")
            node_value = node.get("_value")
            if not isinstance(node_value, dict):
                continue

            if node_type == BRANCH_ON_CONDITIONS_TYPE:
                this_depth = depth + 1
                if this_depth > max_seen:
                    max_seen = this_depth
                boc_name = _node_name(node_value) or BRANCH_ON_CONDITIONS_TYPE
                child_lists = _get_child_node_lists(node_value)
                for child_list in child_lists:
                    sub_findings, sub_max = self._visit_branch(
                        child_list, file_path, this_depth, boc_name
                    )
                    findings.extend(sub_findings)
                    # Only report for top-level BoC branches; if their children exceed nesting, so will they.
                    if sub_max > 3 and this_depth == 1:
                        findings.append(
                            Finding(
                                rule=self,
                                file_path=file_path,
                                line=1,
                                message=(
                                    f"Branch on Conditions '{boc_name}' has a branch nested at {sub_max} levels; "
                                    "consider extracting logic to a suborchestration to keep nesting to 3 levels or fewer."
                                ),
                                path=f"$..nodes[?(@.name=='{boc_name}')]",
                            )
                        )
                    if sub_max > max_seen:
                        max_seen = sub_max
            else:
                for child_list in _get_child_node_lists(node_value):
                    sub_findings, sub_max = self._visit_branch(
                        child_list, file_path, depth, parent_boc_name
                    )
                    findings.extend(sub_findings)
                    if sub_max > max_seen:
                        max_seen = sub_max

        return (findings, max_seen)

    def visit_orchestration(
        self, orch_model: OrchestrationModel, context: ProjectContext
    ) -> Generator[Finding, None, None]:
        raw = orch_model.raw_value
        nodes_obj = raw.get("nodes")
        nodes_list = _unwrap_nodes_list(nodes_obj)
        file_path = orch_model.file_path
        findings, _ = self._visit_branch(nodes_list, file_path, 0, None)
        yield from findings

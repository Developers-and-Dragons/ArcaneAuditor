"""Rule to prefer default-capable Orchestrate accessors over exception-throwing ones."""

import re
from typing import Any, Generator, List, Tuple, Union

from ...base import Finding, FixStrategy, Category
from ....models import ProjectContext, PMDModel, PodModel, OrchestrationModel
from ..shared import StructureRuleBase
from ..shared.orchestration_path_utils import (
    get_template_line_number,
    resolve_ui_location,
    walk_orchestration_source_strings,
)

# Unsafe function name -> tuple of preferred alternative(s). Only these exact names are flagged.
UNSAFE_TO_ALTERNATIVES: List[Tuple[str, Tuple[str, ...]]] = [
    ("booleanAtJsonPath", ("booleanAtJsonPathWithDefault",)),
    ("numberAtJsonPath", ("numberAtJsonPathWithDefault",)),
    ("objectAtJsonPath", ("objectAtJsonPathWithDefault",)),
    ("stringAtJsonPath", ("stringAtJsonPathWithDefault", "stringAtJsonPathOrEmptyString")),
    ("bigDecimalAtXPath", ("bigDecimalAtXPathWithDefault",)),
    ("booleanAtXPath", ("booleanAtXPathWithDefault",)),
    ("dateAtXPath", ("dateAtXPathWithDefault",)),
    ("dateTimeAtXPath", ("dateTimeAtXPathWithDefault",)),
    ("numberAtXPath", ("numberAtXPathWithDefault",)),
    ("stringAtXPath", ("stringAtXPathWithDefault", "stringAtXPathOrEmptyString")),
    ("xmlString", ("xmlStringWithDefault",)),
    ("zonedDateTimeAtXPath", ("zonedDateTimeAtXPathWithDefault",)),
]


def _format_message(function_name: str, alternatives: Tuple[str, ...]) -> str:
    """Build finding message for one or two alternatives."""
    msg = f'This expression uses "{function_name}", which throws an exception when the target value is not found. '
    pref = "Prefer " + " or ".join(f'"{a}"' for a in alternatives)
    return msg + pref + " so missing values are handled explicitly, or validate first if the value is required."


class OrchestratePreferExplicitDefaultAccessor(StructureRuleBase):
    """Flags use of specific Orchestrate accessor functions that throw when value is not found; recommends default-capable alternatives."""

    ID = "OrchestratePreferExplicitDefaultAccessor"
    DESCRIPTION = "Prefer default-capable functions over exception-throwing functions"
    SEVERITY = "ADVICE"
    CATEGORY = Category.ORCHESTRATION
    FIX_STRATEGY = FixStrategy.MECHANICAL
    AVAILABLE_SETTINGS = {}

    DOCUMENTATION = {
        "why": "Some Orchestrate accessor functions throw an exception when a value is not found. Prefer the default-capable functions so missing values are handled explicitly.",
        "catches": [
            "Calls to exception-throwing functions (e.g. stringAtJsonPath, numberAtXPath) that have default-capable alternatives.",
        ],
        "examples": "Use stringAtJsonPathWithDefault or stringAtJsonPathOrEmptyString instead of stringAtJsonPath; use numberAtXPathWithDefault instead of numberAtXPath. etc.",
        "recommendation": "Replace the reported function with the suggested alternative and supply an explicit default.",
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
        raw = orch_model.raw_value
        file_path = orch_model.file_path
        for source, path, is_template_body in walk_orchestration_source_strings(raw):
            for unsafe_name, alternatives in UNSAFE_TO_ALTERNATIVES:
                pattern = re.compile(r"\b" + re.escape(unsafe_name) + r"\s*\(")
                for match in pattern.finditer(source):
                    template_line = (
                        get_template_line_number(source, match.start())
                        if is_template_body
                        else None
                    )
                    location = resolve_ui_location(raw, path, template_line=template_line)
                    location_suffix = f" Location: {location}. " if location else ""
                    message = location_suffix + _format_message(unsafe_name, alternatives)
                    finding_line = template_line if template_line is not None else 1
                    yield Finding(
                        rule=self,
                        file_path=file_path,
                        line=finding_line,
                        message=message,
                    )

"""JSONPath helper + end-to-end `path` field on Finding.

The repo already produces internal dotted paths (script field_paths from
`_extract_script_fields` and widget_paths in widget rules).
"""
from parser.models import PMDModel, PodModel, ProjectContext, SMDModel
from parser.rules.common import Violation
from parser.rules.script.core.var_usage import ScriptVarUsageRule
from parser.rules.structure.endpoints.endpoint_fail_on_status_codes import EndpointFailOnStatusCodesRule
from parser.rules.structure.endpoints.endpoint_name_lower_camel_case import EndpointNameLowerCamelCaseRule
from parser.rules.structure.endpoints.endpoint_url_base_url_type import EndpointBaseUrlTypeRule
from parser.rules.structure.endpoints.no_is_collection_on_endpoints import NoIsCollectionOnEndpointsRule
from parser.rules.structure.endpoints.no_pmd_session_variables import NoPMDSessionVariablesRule
from parser.rules.structure.endpoints.only_maximum_effort import OnlyMaximumEffortRule
from parser.rules.structure.validation.footer_pod_required import FooterPodRequiredRule
from parser.rules.structure.validation.hardcoded_application_id import HardcodedApplicationIdRule
from parser.rules.structure.validation.hardcoded_workday_api import HardcodedWorkdayAPIRule
from parser.rules.structure.validation.pmd_security_domain import PMDSecurityDomainRule
from parser.rules.structure.widgets.widget_id_required import WidgetIdRequiredRule
from utils.jsonpath import (
    data_provider_jsonpath,
    dotted_to_jsonpath,
    endpoint_jsonpath,
    tuple_path_to_jsonpath,
)


class TestDottedToJsonPath:
    def test_none_returns_none(self):
        assert dotted_to_jsonpath(None) is None

    def test_empty_returns_none(self):
        assert dotted_to_jsonpath("") is None

    def test_single_segment(self):
        assert dotted_to_jsonpath("script") == "$.script"

    def test_two_segments(self):
        assert dotted_to_jsonpath("body.primaryLayout") == "$.body.primaryLayout"

    def test_numeric_segment_becomes_bracket(self):
        assert dotted_to_jsonpath("body.children.0.onLoad") == "$.body.children[0].onLoad"

    def test_trailing_numeric(self):
        assert dotted_to_jsonpath("body.children.2") == "$.body.children[2]"

    def test_multiple_numerics(self):
        assert (
            dotted_to_jsonpath("body.children.1.columns.0.cellTemplate")
            == "$.body.children[1].columns[0].cellTemplate"
        )

    def test_already_jsonpath_passthrough(self):
        # If someone hands us a JSONPath-shaped string (starts with $), don't double-prefix.
        assert dotted_to_jsonpath("$.foo.bar") == "$.foo.bar"


class TestViolationCarriesPath:
    def test_violation_default_path_is_none(self):
        assert Violation(message="m", line=1).path is None

    def test_violation_accepts_path(self):
        v = Violation(message="m", line=1, path="body.children.0.onLoad")
        assert v.path == "body.children.0.onLoad"


class TestScriptRuleEmitsJsonPath:
    def test_pmd_script_field_path_becomes_jsonpath(self):
        rule = ScriptVarUsageRule()
        context = ProjectContext()
        # PMD with var in onLoad — _extract_script_fields produces "onLoad" path.
        context.pmds["p"] = PMDModel(
            pageId="p",
            onLoad="<% var x = 1; %>",
            file_path="p.pmd",
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].path == "$.onLoad"

    def test_nested_script_field_path_includes_brackets(self):
        rule = ScriptVarUsageRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            presentation={
                "body": {
                    "children": [
                        {"type": "text", "onLoad": "<% var x = 1; %>"},
                    ]
                }
            },
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        # The dotted path includes the nested numeric index.
        assert findings[0].path is not None
        assert "[0]" in findings[0].path
        assert findings[0].path.startswith("$.")
        assert findings[0].path.endswith(".onLoad")

    def test_standalone_script_file_path_is_none(self):
        # .script files have no natural path.
        from parser.models import ScriptModel

        rule = ScriptVarUsageRule()
        context = ProjectContext()
        context.scripts["s"] = ScriptModel(
            file_path="s.script", source="var x = 1;"
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].path is None


class TestDataProviderJsonPath:
    def test_basic(self):
        assert (
            data_provider_jsonpath("workday-common")
            == "$.dataProviders[?(@.key=='workday-common')].value"
        )

    def test_empty_key_returns_none(self):
        assert data_provider_jsonpath("") is None
        assert data_provider_jsonpath(None) is None


class TestTuplePathToJsonPath:
    def test_mixed_keys_and_ints(self):
        assert (
            tuple_path_to_jsonpath(("endpoints", "foo", "nodes", "_value", 2))
            == "$.endpoints.foo.nodes._value[2]"
        )

    def test_empty_returns_none(self):
        assert tuple_path_to_jsonpath(()) is None
        assert tuple_path_to_jsonpath(None) is None


class TestEndpointJsonPath:
    def test_inbound_with_name(self):
        assert (
            endpoint_jsonpath("inbound", "getWorker")
            == "$.inboundEndpoints[?(@.name=='getWorker')]"
        )

    def test_outbound_with_name_and_subkey(self):
        assert (
            endpoint_jsonpath("outbound", "postData", subkey="bestEffort")
            == "$.outboundEndpoints[?(@.name=='postData')].bestEffort"
        )

    def test_pod_root(self):
        assert (
            endpoint_jsonpath("pod", "getThing", subkey="url")
            == "$.seed.endPoints[?(@.name=='getThing')].url"
        )

    def test_name_missing_falls_back_to_index(self):
        assert endpoint_jsonpath("inbound", None, index=2) == "$.inboundEndpoints[2]"

    def test_unknown_type_returns_none(self):
        assert endpoint_jsonpath("bogus", "x") is None


class TestEndpointRulesEmitJsonPath:
    def _pmd_with_outbound(self, name: str, **fields):
        return PMDModel(
            pageId="p",
            file_path="p.pmd",
            outboundEndpoints=[{"name": name, **fields}],
        )

    def test_only_maximum_effort_pmd_outbound(self):
        rule = OnlyMaximumEffortRule()
        context = ProjectContext()
        context.pmds["p"] = self._pmd_with_outbound("postData", bestEffort=True)
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].path == "$.outboundEndpoints[?(@.name=='postData')].bestEffort"

    def test_endpoint_name_lower_camel_case_inbound(self):
        rule = EndpointNameLowerCamelCaseRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            inboundEndpoints=[{"name": "Bad_Name", "url": "/x"}],
        )
        findings = list(rule.analyze(context))
        assert len(findings) == 1
        assert findings[0].path == "$.inboundEndpoints[?(@.name=='Bad_Name')].name"

    def test_endpoint_fail_on_status_codes_field_missing(self):
        rule = EndpointFailOnStatusCodesRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            outboundEndpoints=[{"name": "post", "url": "/x"}],
        )
        findings = list(rule.analyze(context))
        assert findings
        assert findings[0].path == "$.outboundEndpoints[?(@.name=='post')]"

    def test_endpoint_fail_on_status_codes_partial(self):
        rule = EndpointFailOnStatusCodesRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            outboundEndpoints=[
                {"name": "post", "url": "/x", "failOnStatusCodes": [{"code": 400}]}
            ],
        )
        findings = list(rule.analyze(context))
        assert findings
        assert findings[0].path == "$.outboundEndpoints[?(@.name=='post')].failOnStatusCodes"

    def test_endpoint_base_url_type_pmd(self):
        rule = EndpointBaseUrlTypeRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            outboundEndpoints=[{"name": "post", "url": "https://api.workday.com/x"}],
        )
        findings = list(rule.analyze(context))
        assert findings
        assert findings[0].path == "$.outboundEndpoints[?(@.name=='post')].baseUrlType"

    def test_no_is_collection_pmd_inbound(self):
        rule = NoIsCollectionOnEndpointsRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            inboundEndpoints=[{"name": "get", "url": "/x", "isCollection": True}],
        )
        findings = list(rule.analyze(context))
        assert findings
        assert findings[0].path == "$.inboundEndpoints[?(@.name=='get')].isCollection"

    def test_no_pmd_session_variables(self):
        rule = NoPMDSessionVariablesRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            outboundEndpoints=[
                {"name": "v", "type": "outboundVariable", "variableScope": "session"}
            ],
        )
        findings = list(rule.analyze(context))
        assert findings
        assert findings[0].path == "$.outboundEndpoints[?(@.name=='v')].variableScope"

    def test_hardcoded_workday_api_endpoint(self):
        rule = HardcodedWorkdayAPIRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            outboundEndpoints=[{"name": "post", "url": "https://api.workday.com/x"}],
        )
        findings = list(rule.analyze(context))
        assert findings
        assert findings[0].path == "$.outboundEndpoints[?(@.name=='post')].url"


class TestStaticAndAmdRulesEmitJsonPath:
    def test_footer_pod_required(self):
        from parser.models import PMDPresentation
        rule = FooterPodRequiredRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            presentation=PMDPresentation(
                title={},
                body={},
                footer={"type": "text"},  # invalid — not a pod
            ),
        )
        findings = list(rule.analyze(context))
        assert findings
        assert findings[0].path == "$.presentation.footer"

    def test_pmd_security_domain(self):
        rule = PMDSecurityDomainRule()
        context = ProjectContext()
        from parser.models import PMDPresentation
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            presentation=PMDPresentation(title={}, body={}, footer={}),
            securityDomains=[],
        )
        findings = list(rule.analyze(context))
        assert findings
        assert findings[0].path == "$.securityDomains"

    def test_hardcoded_application_id_amd(self):
        from parser.models import AMDModel, SMDModel
        rule = HardcodedApplicationIdRule()
        context = ProjectContext()
        context.smd = SMDModel(id="s", siteId="site1", applicationId="myApp", file_path="s.smd")
        context.amd = AMDModel(
            applicationId="myApp",
            routes={},
            dataProviders=[{"key": "wd-common", "value": "https://x/myApp/foo"}],
            file_path="a.amd",
        )
        findings = list(rule.analyze(context))
        amd_findings = [f for f in findings if f.file_path == "a.amd"]
        assert amd_findings
        assert amd_findings[0].path == "$.dataProviders[?(@.key=='wd-common')].value"


class TestOrchestrationRuleEmitsJsonPath:
    def test_security_domain_path(self):
        from parser.rules.structure.validation.orchestration_security_domain import (
            OrchestrationSecurityDomainRule,
        )
        from parser.models import OrchestrationModel
        rule = OrchestrationSecurityDomainRule()
        context = ProjectContext()
        orch = OrchestrationModel(
            file_path="f.flow",
            id="f",
            name="myFlow",
            flow_type=".maya.FlowSync",
            security_domains=[],
            raw_value={},
        )
        context.orchestrations["f"] = orch
        findings = list(rule.analyze(context))
        assert findings
        assert findings[0].path == "$.securityDomain"


class TestWidgetRuleEmitsJsonPath:
    def test_widget_id_required_emits_jsonpath(self):
        rule = WidgetIdRequiredRule()
        context = ProjectContext()
        context.pmds["p"] = PMDModel(
            pageId="p",
            file_path="p.pmd",
            presentation={
                "body": {
                    "children": [
                        {"type": "text"},  # missing id
                    ]
                }
            },
        )
        findings = list(rule.analyze(context))
        assert any(f.path and "[0]" in f.path for f in findings)

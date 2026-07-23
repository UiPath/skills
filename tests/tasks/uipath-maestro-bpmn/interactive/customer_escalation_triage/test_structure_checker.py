"""Adversarial unit tests for the interactive escalation structure grader."""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


CHECKER_PATH = Path(__file__).with_name("check_customer_escalation_structure.py")
SPEC = importlib.util.spec_from_file_location("customer_escalation_checker", CHECKER_PATH)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


class raises:
    """Small stdlib-only equivalent of pytest.raises for terse negative cases."""

    def __init__(self, exception: type[BaseException], match: str) -> None:
        self.exception = exception
        self.pattern = re.compile(match)

    def __enter__(self) -> None:
        return None

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: object,
    ) -> bool:
        if exception_type is None or exception is None:
            raise AssertionError(f"expected {self.exception.__name__}")
        if not issubclass(exception_type, self.exception):
            return False
        if not self.pattern.search(str(exception)):
            raise AssertionError(
                f"{exception!r} does not match {self.pattern.pattern!r}"
            )
        return True


def variable(name: str, variable_id: str, variable_type: str = "string") -> ET.Element:
    return ET.Element(
        checker.q(checker.UIPATH_NS, "inputOutput"),
        {"name": name, "id": variable_id, "type": variable_type},
    )


def normalization_fixture() -> tuple[
    ET.Element, dict[str, ET.Element], dict[str, str]
]:
    variables = {
        "customerTier": variable("customerTier", "input-tier-a91"),
        "serviceState": variable("serviceState", "input-state-b82"),
        "duplicateIssueKey": variable("duplicateIssueKey", "input-duplicate-c73"),
        "correlationId": variable("correlationId", "input-correlation-d64"),
        "caseKey": variable("caseKey", "output-case-e55"),
        "tierNormalized": variable("tierNormalized", "internal-tier-f46"),
        "stateNormalized": variable("stateNormalized", "internal-state-g37"),
        "duplicateNormalized": variable(
            "duplicateNormalized", "internal-duplicate-h28"
        ),
    }
    ids_to_names = {
        item.attrib["id"]: name for name, item in variables.items()
    }
    script = ET.fromstring(
        f"""
        <bpmn:scriptTask xmlns:bpmn="{checker.BPMN_NS}"
                         xmlns:uipath="{checker.UIPATH_NS}"
                         id="normalize-any-id" scriptFormat="JavaScript">
          <bpmn:extensionElements>
            <uipath:scriptVersion value="v3" />
            <uipath:mapping version="v1">
              <uipath:type value="BPMN.ScriptTask" version="v1" />
              <uipath:input name="args" type="json" target="bodyField">{{
                "tier":"=vars.input-tier-a91",
                "state":"=vars.input-state-b82",
                "duplicate":"=vars.input-duplicate-c73",
                "correlation":"=vars.input-correlation-d64"
              }}</uipath:input>
              <uipath:output name="tierNormalized" type="string"
                 var="internal-tier-f46" source="=result.response.tier" />
              <uipath:output name="stateNormalized" type="string"
                 var="internal-state-g37" source="=result.response.state" />
              <uipath:output name="duplicateNormalized" type="string"
                 var="internal-duplicate-h28" source="=result.response.duplicate" />
              <uipath:output name="caseKey" type="string"
                 var="output-case-e55" source="=result.response.caseKey" />
            </uipath:mapping>
          </bpmn:extensionElements>
          <bpmn:script><![CDATA[
            return {{ response: {{
              tier: tier.toLowerCase(),
              state: state.toLowerCase(),
              duplicate: duplicate.trim(),
              caseKey: correlation
            }} }};
          ]]></bpmn:script>
        </bpmn:scriptTask>
        """
    )
    return script, variables, ids_to_names


def add_decision_variable(
    script: ET.Element,
    variables: dict[str, ET.Element],
    ids_to_names: dict[str, str],
) -> None:
    decision = variable("failureReason", "output-failure-i17")
    variables["failureReason"] = decision
    ids_to_names[decision.attrib["id"]] = "failureReason"
    mapping = script.find(
        f"./{checker.q(checker.BPMN_NS, 'extensionElements')}//"
        f"{checker.q(checker.UIPATH_NS, 'mapping')}"
    )
    assert mapping is not None
    ET.SubElement(
        mapping,
        checker.q(checker.UIPATH_NS, "output"),
        {
            "name": "failureReason",
            "type": "string",
            "var": decision.attrib["id"],
            "source": '=""',
        },
    )


def gateway_scope(condition: str) -> tuple[ET.Element, dict[str, ET.Element]]:
    scope = ET.fromstring(
        f"""
        <bpmn:subProcess xmlns:bpmn="{checker.BPMN_NS}"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                         id="scope-arbitrary">
          <bpmn:exclusiveGateway id="decision-random" default="flow-default">
            <bpmn:incoming>flow-in</bpmn:incoming>
            <bpmn:outgoing>flow-guarded</bpmn:outgoing>
            <bpmn:outgoing>flow-default</bpmn:outgoing>
          </bpmn:exclusiveGateway>
          <bpmn:sequenceFlow id="flow-guarded"
             sourceRef="decision-random" targetRef="target-yes">
            <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression"
              >{condition}</bpmn:conditionExpression>
          </bpmn:sequenceFlow>
          <bpmn:sequenceFlow id="flow-default"
             sourceRef="decision-random" targetRef="target-no" />
        </bpmn:subProcess>
        """
    )
    flows = {
        item.attrib["id"]: item
        for item in scope.findall(f"./{checker.q(checker.BPMN_NS, 'sequenceFlow')}")
    }
    return scope, flows


def attachment_fixture(source: str = "=iterator.item") -> tuple[
    list[ET.Element], dict[str, ET.Element], dict[str, str]
]:
    variables = {
        "attachments": variable("attachments", "input-attachments-z19", "array"),
        "lastAttachmentName": variable(
            "lastAttachmentName", "output-last-y28"
        ),
    }
    ids_to_names = {
        item.attrib["id"]: name for name, item in variables.items()
    }
    task = ET.fromstring(
        f"""
        <bpmn:task xmlns:bpmn="{checker.BPMN_NS}"
                   xmlns:uipath="{checker.UIPATH_NS}"
                   id="iterate-arbitrary">
          <bpmn:extensionElements>
            <uipath:mapping version="v1">
              <uipath:type value="BPMN.Variables" version="v1" />
              <uipath:output name="lastAttachmentName" type="string"
                 var="output-last-y28" source="{source}" />
            </uipath:mapping>
          </bpmn:extensionElements>
          <bpmn:multiInstanceLoopCharacteristics isSequential="true">
            <bpmn:extensionElements>
              <uipath:loopCharacteristics
                 inputCollection="=vars.input-attachments-z19"
                 inputElement="item" />
            </bpmn:extensionElements>
          </bpmn:multiInstanceLoopCharacteristics>
        </bpmn:task>
        """
    )
    return [task], variables, ids_to_names


def attachment_subprocess_fixture() -> tuple[
    list[ET.Element], dict[str, ET.Element], dict[str, str]
]:
    variables = {
        "attachments": variable("attachments", "input-attachments-sub", "array"),
        "lastAttachmentName": variable(
            "lastAttachmentName", "output-last-sub"
        ),
    }
    ids_to_names = {
        item.attrib["id"]: name for name, item in variables.items()
    }
    subprocess = ET.fromstring(
        f"""
        <bpmn:subProcess xmlns:bpmn="{checker.BPMN_NS}"
                         xmlns:uipath="{checker.UIPATH_NS}"
                         id="iterate-subprocess">
          <bpmn:multiInstanceLoopCharacteristics isSequential="true">
            <bpmn:extensionElements>
              <uipath:loopCharacteristics
                 inputCollection="=vars.input-attachments-sub"
                 inputElement="iterator[0]" />
            </bpmn:extensionElements>
          </bpmn:multiInstanceLoopCharacteristics>
          <bpmn:task id="record-current-item">
            <bpmn:extensionElements>
              <uipath:mapping version="v1">
                <uipath:type value="BPMN.Variables" version="v1" />
                <uipath:output name="lastAttachmentName" type="string"
                   var="output-last-sub"
                   source="=js:iterator[0].item.name" />
              </uipath:mapping>
            </bpmn:extensionElements>
          </bpmn:task>
        </bpmn:subProcess>
        """
    )
    return [subprocess], variables, ids_to_names


def test_normalization_accepts_semantic_mapping_with_arbitrary_ids() -> None:
    script, variables, ids_to_names = normalization_fixture()
    targets = checker.require_normalization_script(script, variables, ids_to_names)
    assert targets == {
        "internal-tier-f46",
        "internal-state-g37",
        "internal-duplicate-h28",
        "output-case-e55",
    }


def test_normalization_rejects_business_routing_hidden_in_script() -> None:
    script, variables, ids_to_names = normalization_fixture()
    body = script.find(f"./{checker.q(checker.BPMN_NS, 'script')}")
    assert body is not None
    body.text = (body.text or "") + '\nvar route = "ManualReview";'
    with raises(SystemExit, match="hides business decisions"):
        checker.require_normalization_script(script, variables, ids_to_names)


def test_normalization_rejects_business_output_initialization() -> None:
    script, variables, ids_to_names = normalization_fixture()
    add_decision_variable(script, variables, ids_to_names)
    with raises(SystemExit, match="must not initialize or assign"):
        checker.require_normalization_script(script, variables, ids_to_names)


def test_gateway_rejects_unprefixed_javascript_operator() -> None:
    scope, flows = gateway_scope("=vars.any-id === 1")
    with raises(SystemExit, match="without '=js:'"):
        checker.require_gateway_contract(scope, flows)


def test_gateway_accepts_prefixed_javascript_with_arbitrary_ids() -> None:
    scope, flows = gateway_scope("=js:vars.any-id === 1")
    assert checker.require_gateway_contract(scope, flows) == [
        "=js:vars.any-id === 1"
    ]


def test_gateway_allows_no_root_decision_when_optional() -> None:
    scope = ET.Element(checker.q(checker.BPMN_NS, "process"), {"id": "root"})
    assert checker.require_gateway_contract(
        scope, {}, require_diverging=False
    ) == []


def test_condition_variable_ids_do_not_prefix_match() -> None:
    assert checker.referenced_variable_ids(
        '=vars.Var_customerTierNormalized == "enterprise"'
    ) == {"Var_customerTierNormalized"}


def test_attachment_loop_accepts_arbitrary_variable_ids() -> None:
    elements, variables, ids_to_names = attachment_fixture()
    checker.require_sequential_attachment_loop(elements, variables, ids_to_names)


def test_attachment_loop_accepts_documented_subprocess_iterator() -> None:
    elements, variables, ids_to_names = attachment_subprocess_fixture()
    checker.require_sequential_attachment_loop(elements, variables, ids_to_names)


def test_attachment_loop_rejects_non_iterator_output() -> None:
    elements, variables, ids_to_names = attachment_fixture("=vars.someOtherValue")
    with raises(SystemExit, match="consume its documented"):
        checker.require_sequential_attachment_loop(elements, variables, ids_to_names)


def test_attachment_loop_rejects_parallel_iteration() -> None:
    elements, variables, ids_to_names = attachment_fixture()
    marker = elements[0].find(
        f"./{checker.q(checker.BPMN_NS, 'multiInstanceLoopCharacteristics')}"
    )
    assert marker is not None
    marker.attrib["isSequential"] = "false"
    with raises(SystemExit, match="exactly one sequential"):
        checker.require_sequential_attachment_loop(elements, variables, ids_to_names)


class StructureCheckerTests(unittest.TestCase):
    def test_arbitrary_normalization_ids(self) -> None:
        test_normalization_accepts_semantic_mapping_with_arbitrary_ids()

    def test_hidden_routing_rejected(self) -> None:
        test_normalization_rejects_business_routing_hidden_in_script()

    def test_business_output_initialization_rejected(self) -> None:
        test_normalization_rejects_business_output_initialization()

    def test_unprefixed_javascript_rejected(self) -> None:
        test_gateway_rejects_unprefixed_javascript_operator()

    def test_prefixed_javascript_accepted(self) -> None:
        test_gateway_accepts_prefixed_javascript_with_arbitrary_ids()

    def test_root_gateway_is_optional(self) -> None:
        test_gateway_allows_no_root_decision_when_optional()

    def test_variable_references_are_exact(self) -> None:
        test_condition_variable_ids_do_not_prefix_match()

    def test_arbitrary_attachment_ids(self) -> None:
        test_attachment_loop_accepts_arbitrary_variable_ids()

    def test_subprocess_attachment_iterator(self) -> None:
        test_attachment_loop_accepts_documented_subprocess_iterator()

    def test_non_iterator_output_rejected(self) -> None:
        test_attachment_loop_rejects_non_iterator_output()

    def test_parallel_attachment_loop_rejected(self) -> None:
        test_attachment_loop_rejects_parallel_iteration()


if __name__ == "__main__":
    unittest.main()

"""Adversarial unit tests for the interactive escalation structure grader."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
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


def task_command_guard_pattern() -> re.Pattern[str]:
    task_text = Path(__file__).with_name(
        "customer_escalation_triage.yaml"
    ).read_text(encoding="utf-8")
    match = re.search(
        r'Agent left BPMN cloud execution and mutation to the grader".*?'
        r"command_pattern: '([^']+)'",
        task_text,
        flags=re.DOTALL,
    )
    assert match is not None
    return re.compile(match.group(1))


def test_command_guard_covers_executable_shell_prefixes() -> None:
    pattern = task_command_guard_pattern()
    blocked = (
        "FOO=bar uip solution upload Eval.uipx",
        "FOO='bar baz' exec uip solution upload Eval.uipx",
        "exec uip maestro bpmn debug Project",
        "(uip solution upload Eval.uipx)",
        "{ uip solution upload Eval.uipx; }",
        "! uip solution upload Eval.uipx",
        "time -p uip solution upload Eval.uipx",
        "/usr/bin/env -u FOO uip solution upload Eval.uipx",
        "if true; then uip solution upload Eval.uipx; fi",
        "while true; do uip maestro bpmn debug Project; done",
        "$(which uip) solution upload Eval.uipx",
    )
    allowed = (
        'echo "uip solution upload Eval.uipx"',
        "printf '%s' 'uip maestro bpmn debug Project'",
        "uip maestro bpmn registry list --output json",
        "uip is resources run get connector operation --output json",
    )
    for command in blocked:
        assert pattern.search(command), command
    for command in allowed:
        assert pattern.search(command) is None, command


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
        "duplicateIssueKeyNormalized": variable(
            "duplicateIssueKeyNormalized", "internal-duplicate-h28"
        ),
        "scriptResponse": variable(
            "scriptResponse", "normalize-response-r11", "jsonSchema"
        ),
        "Error": variable("Error", "normalize-error-r12", "jsonSchema"),
    }
    ids_to_names = {
        item.attrib["id"]: name for name, item in variables.items()
    }
    variables["scriptResponse"].text = json.dumps(
        {
            "type": "object",
            "properties": {
                "tier": {"type": "string"},
                "serviceState": {"type": "string"},
                "duplicateIssueKey": {"type": "string"},
                "caseKey": {"type": "string"},
            },
            "required": [
                "tier",
                "serviceState",
                "duplicateIssueKey",
                "caseKey",
            ],
        }
    )
    script = ET.fromstring(
        f"""
        <bpmn:scriptTask xmlns:bpmn="{checker.BPMN_NS}"
                         xmlns:uipath="{checker.UIPATH_NS}"
                         id="normalize-any-id" scriptFormat="JavaScript">
          <bpmn:extensionElements>
            <uipath:mapping version="v1">
              <uipath:type value="BPMN.Variables" version="v1" />
              <uipath:context>
                <uipath:inputSchema type="jsonSchema">{{
                  "type":"object",
                  "properties":{{
                    "vars":{{"type":"object"}},
                    "metadata":{{"type":"object"}}
                  }}
                }}</uipath:inputSchema>
              </uipath:context>
              <uipath:input name="args" type="json" target="bodyField"
                value="{{&quot;vars&quot;:&quot;=vars&quot;,&quot;metadata&quot;:&quot;=metadata&quot;}}" />
              <uipath:output name="scriptResponse" type="jsonSchema"
                 var="normalize-response-r11" source="=result.response" />
              <uipath:output name="Error" type="jsonSchema"
                 var="normalize-error-r12" source="=Error" />
              <uipath:output name="tierNormalized" type="string"
                 var="internal-tier-f46"
                 source="=vars.normalize-response-r11.tier" custom="true" />
              <uipath:output name="stateNormalized" type="string"
                 var="internal-state-g37"
                 source="=vars.normalize-response-r11.serviceState" custom="true" />
              <uipath:output name="duplicateIssueKeyNormalized" type="string"
                 var="internal-duplicate-h28"
                 source="=vars.normalize-response-r11.duplicateIssueKey" custom="true" />
              <uipath:output name="caseKey" type="string"
                 var="output-case-e55"
                 source="=vars.normalize-response-r11.caseKey" custom="true" />
            </uipath:mapping>
            <uipath:scriptVersion value="v3" />
          </bpmn:extensionElements>
          <bpmn:script><![CDATA[
            return {{
              tier: (vars.input-tier-a91 || "").toLowerCase(),
              serviceState: (vars.input-state-b82 || "").toLowerCase(),
              duplicateIssueKey: (vars.input-duplicate-c73 || "").trim(),
              caseKey: vars.input-correlation-d64
            }};
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


def jira_update_process(path_value: str) -> ET.Element:
    return ET.fromstring(
        f"""
        <bpmn:process xmlns:bpmn="{checker.BPMN_NS}"
                      xmlns:uipath="{checker.UIPATH_NS}">
          <bpmn:sendTask id="jira-update">
            <bpmn:extensionElements>
              <uipath:activity version="v1">
                <uipath:type value="Intsvc.ActivityExecution" version="v1" />
                <uipath:context>
                  <uipath:input name="connectorKey"
                     value="uipath-atlassian-jira" />
                  <uipath:input name="path"
                     value="/curated_edit_issue/{{issueIdOrKey}}" />
                </uipath:context>
                <uipath:input name="issueIdOrKey" type="string" target="path"
                   value="{path_value}" />
              </uipath:activity>
            </bpmn:extensionElements>
          </bpmn:sendTask>
        </bpmn:process>
        """
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


def attachment_fixture(
    marker_script: str = (
        "var copyName = vars.input-correlation-c81 + '-' + "
        "currentItem.name; "
        "return { itemName: currentItem.name, copyName: copyName, "
        "driveFileId: currentItem.driveFileId };"
    ),
    drive_file_id: str = "=vars.iteration-response.driveFileId",
    drive_copy_name: str = "=vars.iteration-response.copyName",
) -> tuple[
    list[ET.Element], dict[str, ET.Element], dict[str, str]
]:
    variables = {
        "attachments": variable("attachments", "input-attachments-z19", "array"),
        "correlationId": variable(
            "correlationId", "input-correlation-c81"
        ),
        "lastAttachmentName": variable(
            "lastAttachmentName", "output-last-y28"
        ),
        "attachmentIterationNames": ET.Element(
            checker.q(checker.UIPATH_NS, "inputOutput"),
            {
                "name": "attachmentIterationNames",
                "id": "iteration-names-q37",
                "type": "Collection{string}",
                "elementId": "iterate-arbitrary",
                "custom": "true",
            },
        ),
        "attachmentPrepResult": ET.Element(
            checker.q(checker.UIPATH_NS, "inputOutput"),
            {
                "name": "attachmentPrepResult",
                "id": "iteration-response",
                "type": "jsonSchema",
            },
        ),
    }
    variables["attachmentPrepResult"].text = json.dumps(
        {
            "type": "object",
            "properties": {
                "itemName": {"type": "string"},
                "copyName": {"type": "string"},
                "driveFileId": {"type": "string"},
            },
            "required": ["itemName", "copyName", "driveFileId"],
        }
    )
    ids_to_names = {
        item.attrib["id"]: name for name, item in variables.items()
    }
    marker = ET.fromstring(
        f"""
        <bpmn:subProcess xmlns:bpmn="{checker.BPMN_NS}"
                         xmlns:uipath="{checker.UIPATH_NS}"
                         id="iterate-arbitrary">
          <bpmn:extensionElements>
            <uipath:mapping version="v1">
              <uipath:type value="BPMN.Variables" version="v1" />
              <uipath:output name="attachmentIterationName" type="string"
                 source="=vars.iteration-response.itemName"
                 var="iteration-names-q37" custom="true" />
            </uipath:mapping>
          </bpmn:extensionElements>
          <bpmn:multiInstanceLoopCharacteristics isSequential="true">
            <bpmn:extensionElements>
              <uipath:loopCharacteristics
                 inputCollection="=vars.input-attachments-z19"
                 inputElement="iterator[0]"
                 version="v1" />
            </bpmn:extensionElements>
          </bpmn:multiInstanceLoopCharacteristics>
          <bpmn:startEvent id="attachment-start">
            <bpmn:outgoing>attachment-start-script</bpmn:outgoing>
          </bpmn:startEvent>
          <bpmn:scriptTask id="attachment-script"
                           scriptFormat="JavaScript">
            <bpmn:extensionElements>
              <uipath:mapping version="v1">
                <uipath:type value="BPMN.Variables" version="v1" />
                <uipath:context>
                  <uipath:inputSchema type="jsonSchema">{{
                    "type":"object",
                    "properties":{{
                      "vars":{{"type":"object"}},
                      "metadata":{{"type":"object"}},
                      "currentItem":{{
                        "type":"object",
                        "properties":{{
                          "name":{{"type":"string"}},
                          "driveFileId":{{"type":"string"}}
                        }},
                        "required":["name","driveFileId"]
                      }}
                    }}
                  }}</uipath:inputSchema>
                </uipath:context>
                <uipath:input name="args" type="json" target="bodyField"
                  value="{{&quot;vars&quot;:&quot;=vars&quot;,&quot;metadata&quot;:&quot;=metadata&quot;,&quot;currentItem&quot;:&quot;=iterator[0].item&quot;}}" />
                <uipath:output name="scriptResponse" type="jsonSchema"
                   var="iteration-response" source="=result.response" />
                <uipath:output name="Error" type="jsonSchema"
                   var="iteration-error" source="=Error" />
              </uipath:mapping>
              <uipath:scriptVersion value="v3" />
            </bpmn:extensionElements>
            <bpmn:incoming>attachment-start-script</bpmn:incoming>
            <bpmn:outgoing>attachment-script-drive</bpmn:outgoing>
            <bpmn:script>{marker_script}</bpmn:script>
          </bpmn:scriptTask>
          <bpmn:sendTask id="attachment-drive">
            <bpmn:extensionElements>
              <uipath:activity version="v1">
                <uipath:type value="Intsvc.ActivityExecution" version="v1" />
                <uipath:context>
                  <uipath:input name="connectorKey"
                     value="uipath-google-drive" />
                  <uipath:input name="path" value="/copyFile" />
                </uipath:context>
                <uipath:input name="fileId" type="string" target="query"
                   value="{drive_file_id}" />
                <uipath:input name="body" type="json" target="body"
                   value="{{&quot;destinationFolder&quot;:&quot;=vars.destination-folder&quot;,&quot;name&quot;:&quot;{drive_copy_name}&quot;}}" />
              </uipath:activity>
            </bpmn:extensionElements>
            <bpmn:incoming>attachment-script-drive</bpmn:incoming>
            <bpmn:outgoing>attachment-drive-end</bpmn:outgoing>
          </bpmn:sendTask>
          <bpmn:endEvent id="attachment-end">
            <bpmn:incoming>attachment-drive-end</bpmn:incoming>
          </bpmn:endEvent>
          <bpmn:sequenceFlow id="attachment-start-script"
             sourceRef="attachment-start" targetRef="attachment-script" />
          <bpmn:sequenceFlow id="attachment-script-drive"
             sourceRef="attachment-script" targetRef="attachment-drive" />
          <bpmn:sequenceFlow id="attachment-drive-end"
             sourceRef="attachment-drive" targetRef="attachment-end" />
        </bpmn:subProcess>
        """
    )
    reducer = ET.fromstring(
        f"""
        <bpmn:scriptTask xmlns:bpmn="{checker.BPMN_NS}"
                         xmlns:uipath="{checker.UIPATH_NS}"
                         id="reduce-arbitrary" scriptFormat="JavaScript">
          <bpmn:extensionElements>
            <uipath:mapping version="v1">
              <uipath:type value="BPMN.Variables" version="v1" />
              <uipath:output name="scriptResponse" type="string"
                 var="output-last-y28" source="=result.response" />
              <uipath:output name="Error" type="jsonSchema"
                 var="reducer-error" source="=Error" />
            </uipath:mapping>
            <uipath:scriptVersion value="v3" />
          </bpmn:extensionElements>
          <bpmn:script>
            return vars.iteration-names-q37[
              vars.iteration-names-q37.length - 1
            ];
          </bpmn:script>
        </bpmn:scriptTask>
        """
    )
    return [marker, reducer], variables, ids_to_names


def test_normalization_accepts_semantic_mapping_with_arbitrary_ids() -> None:
    script, variables, ids_to_names = normalization_fixture()
    checker.require_script_runtime_contract(script)
    targets = checker.require_normalization_script(
        script, variables, ids_to_names, []
    )
    assert targets == {
        "normalize-response-r11",
        "normalize-error-r12",
        "internal-tier-f46",
        "internal-state-g37",
        "internal-duplicate-h28",
        "output-case-e55",
    }


def test_jira_update_accepts_exact_normalized_duplicate() -> None:
    script, variables, ids_to_names = normalization_fixture()
    checker.require_jira_update_uses_normalized_duplicate(
        jira_update_process("=vars.internal-duplicate-h28"),
        script,
        variables,
        ids_to_names,
        [],
    )


def test_jira_update_accepts_equivalent_js_normalized_duplicate() -> None:
    script, variables, ids_to_names = normalization_fixture()
    checker.require_jira_update_uses_normalized_duplicate(
        jira_update_process(
            "=js: ((vars.internal-duplicate-h28))"
        ),
        script,
        variables,
        ids_to_names,
        [],
    )


def test_jira_update_accepts_js_prefix_on_each_normalized_link() -> None:
    script, variables, ids_to_names = normalization_fixture()
    output = script.find(
        f".//{checker.q(checker.UIPATH_NS, 'output')}"
        "[@name='duplicateIssueKeyNormalized']"
    )
    assert output is not None
    output.set(
        "source",
        "=js: vars.normalize-response-r11.duplicateIssueKey",
    )
    checker.require_jira_update_uses_normalized_duplicate(
        jira_update_process("=js: vars.internal-duplicate-h28"),
        script,
        variables,
        ids_to_names,
        [],
    )


def test_jira_update_rejects_raw_duplicate_input() -> None:
    script, variables, ids_to_names = normalization_fixture()
    with raises(SystemExit, match="normalized duplicate"):
        checker.require_jira_update_uses_normalized_duplicate(
            jira_update_process("=vars.input-duplicate-c73"),
            script,
            variables,
            ids_to_names,
            [],
        )


def test_jira_update_rejects_reassigned_normalization_alias() -> None:
    script, variables, ids_to_names = normalization_fixture()
    body = script.find(f"./{checker.q(checker.BPMN_NS, 'script')}")
    assert body is not None
    body.text = """
      let duplicate = (vars.input-duplicate-c73 || "").trim();
      duplicate = "SHARED-1";
      return {
        tier: (vars.input-tier-a91 || "").toLowerCase(),
        serviceState: (vars.input-state-b82 || "").toLowerCase(),
        duplicateIssueKey: duplicate,
        caseKey: vars.input-correlation-d64
      };
    """
    with raises(SystemExit, match="normalized duplicate"):
        checker.require_jira_update_uses_normalized_duplicate(
            jira_update_process("=vars.internal-duplicate-h28"),
            script,
            variables,
            ids_to_names,
            [],
        )


def test_jira_update_rejects_duplicate_returned_key() -> None:
    script, variables, ids_to_names = normalization_fixture()
    body = script.find(f"./{checker.q(checker.BPMN_NS, 'script')}")
    assert body is not None
    body.text = """
      const duplicate = (vars.input-duplicate-c73 || "").trim();
      return {
        tier: (vars.input-tier-a91 || "").toLowerCase(),
        serviceState: (vars.input-state-b82 || "").toLowerCase(),
        duplicateIssueKey: duplicate,
        duplicateIssueKey: "SHARED-1",
        caseKey: vars.input-correlation-d64
      };
    """
    with raises(SystemExit, match="exactly once"):
        checker.require_jira_update_uses_normalized_duplicate(
            jira_update_process("=vars.internal-duplicate-h28"),
            script,
            variables,
            ids_to_names,
            [],
        )


def test_jira_update_rejects_trailing_comma_return_object() -> None:
    script, variables, ids_to_names = normalization_fixture()
    body = script.find(f"./{checker.q(checker.BPMN_NS, 'script')}")
    assert body is not None
    body.text = """
      return {
        tier: (vars.input-tier-a91 || "").toLowerCase(),
        serviceState: (vars.input-state-b82 || "").toLowerCase(),
        duplicateIssueKey: (vars.input-duplicate-c73 || "").trim(),
        caseKey: vars.input-correlation-d64
      }, {
        duplicateIssueKey: vars.input-duplicate-c73
      };
    """
    with raises(SystemExit, match="trailing comma expression"):
        checker.require_jira_update_uses_normalized_duplicate(
            jira_update_process("=vars.internal-duplicate-h28"),
            script,
            variables,
            ids_to_names,
            [],
        )


def test_jira_update_rejects_non_object_response_schema_root() -> None:
    script, variables, ids_to_names = normalization_fixture()
    schema = json.loads(variables["scriptResponse"].text or "{}")
    schema["type"] = "string"
    variables["scriptResponse"].text = json.dumps(schema)
    with raises(SystemExit, match="normalized duplicate"):
        checker.require_jira_update_uses_normalized_duplicate(
            jira_update_process("=vars.internal-duplicate-h28"),
            script,
            variables,
            ids_to_names,
            [],
        )


def test_return_scanner_ignores_comments_and_string_literals() -> None:
    script, variables, ids_to_names = normalization_fixture()
    body = script.find(f"./{checker.q(checker.BPMN_NS, 'script')}")
    assert body is not None
    body.text = (
        'const note = "return { ignored: true }";\n'
        "// return an exact normalized object below\n"
        f"{body.text}\n"
        "/* return { alsoIgnored: true }; */"
    )
    checker.require_jira_update_uses_normalized_duplicate(
        jira_update_process("=vars.internal-duplicate-h28"),
        script,
        variables,
        ids_to_names,
        [],
    )


def test_javascript_mask_hides_regex_and_exposes_template_code() -> None:
    source = (
        r"/\/\/ const forged = currentItem;/; "
        r"`${Object.assign(currentItem, {name: 'WRONG'})}`;"
    )
    masked = checker.javascript_code_mask(source)
    assert "const forged" not in masked
    assert "Object.assign" in masked
    assert "currentItem" in masked


def test_registry_evidence_is_discovered_by_content_not_filename() -> None:
    payload = {
        "Result": "Success",
        "Data": {
            "ExtensionType": {
                "ExtensionType": "BPMN.Variables",
                "BpmnElement": "bpmn:Task",
            }
        },
    }
    with tempfile.TemporaryDirectory() as directory:
        evidence = Path(directory)
        (evidence / "get-BPMN.Variables.json").write_text(
            json.dumps(payload),
            encoding="utf-8",
        )
        (evidence / "unrelated.json").write_text("{}", encoding="utf-8")
        matches = checker.find_registry_evidence(
            "BPMN.Variables",
            evidence,
        )

    assert len(matches) == 1
    assert matches[0][0].name == "get-BPMN.Variables.json"
    assert matches[0][1] == payload


def test_script_registry_accepts_variables_mapping_template() -> None:
    checker.require_usable_registry_template(
        "BPMN.ScriptTask",
        {
            "XmlTemplate": (
                '<bpmn:scriptTask><uipath:mapping>'
                '<uipath:type value="BPMN.Variables" version="v1" />'
                "</uipath:mapping></bpmn:scriptTask>"
            )
        },
        Path("BPMN.ScriptTask.json"),
    )


def test_script_registry_retains_stale_live_mapping_template() -> None:
    checker.require_usable_registry_template(
        "BPMN.ScriptTask",
        {
            "XmlTemplate": (
                '<bpmn:ScriptTask><uipath:mapping>'
                '<uipath:type value="BPMN.ScriptTask" version="v1" />'
                "</uipath:mapping></bpmn:ScriptTask>"
            )
        },
        Path("BPMN.ScriptTask.json"),
    )


def test_normalization_accepts_following_variables_extraction() -> None:
    script, variables, ids_to_names = normalization_fixture()
    mapping = script.find(
        f"./{checker.q(checker.BPMN_NS, 'extensionElements')}//"
        f"{checker.q(checker.UIPATH_NS, 'mapping')}"
    )
    assert mapping is not None
    for output in list(mapping.findall(f"./{checker.q(checker.UIPATH_NS, 'output')}")):
        if output.attrib.get("name") not in {"scriptResponse", "Error"}:
            mapping.remove(output)
    extraction = ET.fromstring(
        f"""
        <bpmn:task xmlns:bpmn="{checker.BPMN_NS}"
                   xmlns:uipath="{checker.UIPATH_NS}"
                   id="extract-normalized">
          <bpmn:extensionElements>
            <uipath:mapping version="v1">
              <uipath:type value="BPMN.Variables" version="v1" />
              <uipath:output name="tierNormalized" type="string"
                 var="internal-tier-f46"
                 source="=vars.normalize-response-r11.tier" />
              <uipath:output name="stateNormalized" type="string"
                 var="internal-state-g37"
                 source="=vars.normalize-response-r11.serviceState" />
              <uipath:output name="duplicateNormalized" type="string"
                 var="internal-duplicate-h28"
                 source="=vars.normalize-response-r11.duplicateIssueKey" />
              <uipath:output name="caseKey" type="string"
                 var="output-case-e55"
                 source="=vars.normalize-response-r11.caseKey" />
            </uipath:mapping>
          </bpmn:extensionElements>
        </bpmn:task>
        """
    )

    targets = checker.require_normalization_script(
        script, variables, ids_to_names, [extraction]
    )
    assert {
        "internal-tier-f46",
        "internal-state-g37",
        "internal-duplicate-h28",
        "output-case-e55",
    } <= targets


def variables_extraction_with_direct_case_copy(
    case_source: str,
) -> tuple[ET.Element, dict[str, ET.Element], dict[str, str], ET.Element]:
    script, variables, ids_to_names = normalization_fixture()
    mapping = script.find(
        f"./{checker.q(checker.BPMN_NS, 'extensionElements')}//"
        f"{checker.q(checker.UIPATH_NS, 'mapping')}"
    )
    assert mapping is not None
    for output in list(
        mapping.findall(f"./{checker.q(checker.UIPATH_NS, 'output')}")
    ):
        if output.attrib.get("name") not in {"scriptResponse", "Error"}:
            mapping.remove(output)
    body = script.find(f"./{checker.q(checker.BPMN_NS, 'script')}")
    assert body is not None
    body.text = """
      return {
        tier: (vars.input-tier-a91 || "").toLowerCase(),
        serviceState: (vars.input-state-b82 || "").toLowerCase(),
        duplicateIssueKey: (vars.input-duplicate-c73 || "").trim()
      };
    """
    extraction = ET.fromstring(
        f"""
        <bpmn:task xmlns:bpmn="{checker.BPMN_NS}"
                   xmlns:uipath="{checker.UIPATH_NS}"
                   id="apply-normalization">
          <bpmn:extensionElements>
            <uipath:mapping version="v1">
              <uipath:type value="BPMN.Variables" version="v1" />
              <uipath:output name="tierNormalized" type="string"
                 var="internal-tier-f46"
                 source="=vars.normalize-response-r11.tier" />
              <uipath:output name="stateNormalized" type="string"
                 var="internal-state-g37"
                 source="=vars.normalize-response-r11.serviceState" />
              <uipath:output name="duplicateNormalized" type="string"
                 var="internal-duplicate-h28"
                 source="=vars.normalize-response-r11.duplicateIssueKey" />
              <uipath:output name="caseKey" type="string"
                 var="output-case-e55" source="{case_source}" />
            </uipath:mapping>
          </bpmn:extensionElements>
        </bpmn:task>
        """
    )
    return script, variables, ids_to_names, extraction


def test_normalization_accepts_visible_exact_correlation_copy() -> None:
    script, variables, ids_to_names, extraction = (
        variables_extraction_with_direct_case_copy(
            "=vars.input-correlation-d64"
        )
    )
    targets = checker.require_normalization_script(
        script, variables, ids_to_names, [extraction]
    )
    assert "output-case-e55" in targets


def test_normalization_tolerates_other_scripts_same_named_errors() -> None:
    script, variables, ids_to_names = normalization_fixture()
    variables["Error"] = variable(
        "Error", "other-script-scoped-error", "jsonSchema"
    )
    ids_to_names["other-script-scoped-error"] = "Error"
    targets = checker.require_normalization_script(
        script, variables, ids_to_names, []
    )
    assert "normalize-error-r12" in targets


def test_normalization_rejects_transformed_visible_correlation_copy() -> None:
    script, variables, ids_to_names, extraction = (
        variables_extraction_with_direct_case_copy(
            "=js:vars.input-correlation-d64.trim()"
        )
    )
    with raises(SystemExit, match="copy correlationId exactly"):
        checker.require_normalization_script(
            script, variables, ids_to_names, [extraction]
        )


def test_normalization_accepts_typed_structured_result_consumed_by_gateways() -> None:
    script, variables, ids_to_names = normalization_fixture()
    mapping = script.find(
        f"./{checker.q(checker.BPMN_NS, 'extensionElements')}//"
        f"{checker.q(checker.UIPATH_NS, 'mapping')}"
    )
    assert mapping is not None
    for output in list(mapping.findall(f"./{checker.q(checker.UIPATH_NS, 'output')}")):
        if output.attrib.get("name") not in {"scriptResponse", "Error", "caseKey"}:
            mapping.remove(output)

    response = variables["scriptResponse"]
    response.attrib["type"] = "object"
    response.text = json.dumps(
        {
            "type": "object",
            "properties": {
                "normalizedTier": {"type": "string"},
                "normalizedServiceState": {"type": "string"},
                "normalizedDuplicateKey": {"type": "string"},
                "caseKey": {"type": "string"},
            },
            "required": [
                "normalizedTier",
                "normalizedServiceState",
                "normalizedDuplicateKey",
                "caseKey",
            ],
        }
    )

    targets = checker.require_normalization_script(
        script, variables, ids_to_names, []
    )
    assert "normalize-response-r11" in targets
    conditions = """
      =vars.normalize-response-r11.normalizedTier == "enterprise"
      =vars.normalize-response-r11.normalizedServiceState == "unavailable"
      =vars.normalize-response-r11.normalizedDuplicateKey != ""
    """
    assert checker.structured_normalization_roles_in_conditions(
        "normalize-response-r11", conditions
    ) == {"tier", "serviceState", "duplicateIssueKey"}


def test_normalization_rejects_untyped_dereferenced_response_fields() -> None:
    script, variables, ids_to_names = normalization_fixture()
    schema = json.loads(variables["scriptResponse"].text or "{}")
    schema["properties"]["tier"] = {"type": "boolean"}
    schema["properties"]["serviceState"] = {}
    schema["required"].remove("serviceState")
    variables["scriptResponse"].text = json.dumps(schema)

    with raises(SystemExit, match="not required strings"):
        checker.require_normalization_script(
            script,
            variables,
            ids_to_names,
            [],
        )


def test_normalization_accepts_exact_correlation_through_local_alias() -> None:
    script, variables, ids_to_names = normalization_fixture()
    working_case = variable("workingCaseKey", "working-case-e56")
    variables["workingCaseKey"] = working_case
    ids_to_names[working_case.attrib["id"]] = working_case.attrib["name"]

    case_output = next(
        output
        for output in script.findall(
            f"./{checker.q(checker.BPMN_NS, 'extensionElements')}//"
            f"{checker.q(checker.UIPATH_NS, 'output')}"
        )
        if output.attrib.get("name") == "caseKey"
    )
    case_output.attrib["name"] = "workingCaseKey"
    case_output.attrib["var"] = working_case.attrib["id"]
    body = script.find(f"./{checker.q(checker.BPMN_NS, 'script')}")
    assert body is not None
    body.text = """
      var caseKey = vars.input-correlation-d64;
      return {
        tier: (vars.input-tier-a91 || "").toLowerCase(),
        serviceState: (vars.input-state-b82 || "").toLowerCase(),
        duplicateIssueKey: (vars.input-duplicate-c73 || "").trim(),
        caseKey: caseKey
      };
    """

    targets = checker.require_normalization_script(
        script, variables, ids_to_names, []
    )
    assert working_case.attrib["id"] in targets


def test_normalization_accepts_semantic_correlation_result_property() -> None:
    script, variables, ids_to_names = normalization_fixture()
    case_output = next(
        output
        for output in script.findall(
            f"./{checker.q(checker.BPMN_NS, 'extensionElements')}//"
            f"{checker.q(checker.UIPATH_NS, 'output')}"
        )
        if output.attrib.get("name") == "caseKey"
    )
    case_output.attrib["source"] = (
        "=vars.normalize-response-r11.preservedCorrelation"
    )
    body = script.find(f"./{checker.q(checker.BPMN_NS, 'script')}")
    assert body is not None
    body.text = (body.text or "").replace(
        "caseKey: vars.input-correlation-d64",
        "preservedCorrelation: vars.input-correlation-d64",
    )
    schema = json.loads(variables["scriptResponse"].text or "{}")
    schema["properties"]["preservedCorrelation"] = {"type": "string"}
    schema["required"].append("preservedCorrelation")
    variables["scriptResponse"].text = json.dumps(schema)

    targets = checker.require_normalization_script(
        script, variables, ids_to_names, []
    )
    assert "output-case-e55" in targets


def test_normalization_accepts_string_identity_empty_fallback() -> None:
    script, variables, ids_to_names = normalization_fixture()
    body = script.find(f"./{checker.q(checker.BPMN_NS, 'script')}")
    assert body is not None
    body.text = (body.text or "").replace(
        "caseKey: vars.input-correlation-d64",
        "caseKey: correlationValue",
    )
    body.text = (
        "var correlationValue = vars.input-correlation-d64 || '';\n"
        + body.text
    )

    targets = checker.require_normalization_script(
        script, variables, ids_to_names, []
    )
    assert "output-case-e55" in targets


def test_normalization_rejects_business_routing_hidden_in_script() -> None:
    script, variables, ids_to_names = normalization_fixture()
    body = script.find(f"./{checker.q(checker.BPMN_NS, 'script')}")
    assert body is not None
    body.text = (body.text or "") + '\nvar route = "ManualReview";'
    with raises(SystemExit, match="hides business decisions"):
        checker.require_normalization_script(script, variables, ids_to_names, [])


def test_normalization_rejects_business_output_initialization() -> None:
    script, variables, ids_to_names = normalization_fixture()
    add_decision_variable(script, variables, ids_to_names)
    with raises(SystemExit, match="must not initialize or assign"):
        checker.require_normalization_script(script, variables, ids_to_names, [])


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


def jira_intent_task(source: str) -> ET.Element:
    return ET.fromstring(
        f"""
        <bpmn:task xmlns:bpmn="{checker.BPMN_NS}"
                   xmlns:uipath="{checker.UIPATH_NS}">
          <bpmn:extensionElements>
            <uipath:mapping version="v1">
              <uipath:type value="BPMN.Variables" version="v1" />
              <uipath:output name="jiraAction" type="string"
                 var="jira-action-id" source="{source}" />
            </uipath:mapping>
          </bpmn:extensionElements>
        </bpmn:task>
        """
    )


def test_jira_workstream_accepts_material_route_assignments() -> None:
    checker.require_material_jira_intent(
        [
            jira_intent_task("UpdateExisting"),
            jira_intent_task("CreateIssue"),
            jira_intent_task("NoAction"),
        ],
        {"jira-action-id": "jiraAction"},
    )


def test_jira_workstream_rejects_noop_self_assignment() -> None:
    with raises(SystemExit, match="no-op self-assignment"):
        checker.require_material_jira_intent(
            [
                jira_intent_task("=vars.jira-action-id"),
                jira_intent_task("UpdateExisting"),
                jira_intent_task("CreateIssue"),
                jira_intent_task("NoAction"),
            ],
            {"jira-action-id": "jiraAction"},
        )


def test_assessment_rejects_downstream_intent_assignment() -> None:
    subprocess = ET.fromstring(
        f"""
        <bpmn:subProcess xmlns:bpmn="{checker.BPMN_NS}"
                         xmlns:uipath="{checker.UIPATH_NS}">
          <bpmn:task id="premature-jira-intent">
            <bpmn:extensionElements>
              <uipath:mapping version="v1">
                <uipath:type value="BPMN.Variables" version="v1" />
                <uipath:output name="jiraAction" type="string"
                   var="jira-action-id" source="NoAction" />
              </uipath:mapping>
            </bpmn:extensionElements>
          </bpmn:task>
        </bpmn:subProcess>
        """
    )
    with raises(SystemExit, match="precomputes outputs"):
        checker.forbid_downstream_intents_in_assessment(
            subprocess,
            {"jira-action-id": "jiraAction"},
        )


def test_condition_variable_ids_do_not_prefix_match() -> None:
    assert checker.referenced_variable_ids(
        '=vars.Var_customerTierNormalized == "enterprise"'
    ) == {"Var_customerTierNormalized"}


def test_subprocess_propagation_accepts_descriptive_mapping_name() -> None:
    output = ET.Element(
        checker.q(checker.UIPATH_NS, "output"),
        {
            "name": "routeFinal",
            "type": "string",
            "var": "root-route-id",
            "source": "=vars.assessed-route-id",
        },
    )
    assert checker.mapping_propagates_semantic(
        output,
        {"root-route-id": "route"},
        "route",
        "string",
    )


def test_subprocess_propagation_rejects_unrelated_target() -> None:
    output = ET.Element(
        checker.q(checker.UIPATH_NS, "output"),
        {
            "name": "routeFinal",
            "type": "string",
            "var": "root-severity-id",
            "source": "=vars.assessed-route-id",
        },
    )
    assert not checker.mapping_propagates_semantic(
        output,
        {"root-severity-id": "severity"},
        "route",
        "string",
    )


def test_attachment_loop_accepts_arbitrary_variable_ids() -> None:
    elements, variables, ids_to_names = attachment_fixture()
    checker.require_sequential_attachment_loop(elements, variables, ids_to_names)


def test_attachment_loop_accepts_drive_lineage_from_script_response() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        drive_file_id="=vars.iteration-response.driveFileId",
        drive_copy_name="=vars.iteration-response.copyName",
    )
    checker.require_sequential_attachment_loop(elements, variables, ids_to_names)


def test_attachment_loop_accepts_js_prefixed_script_response() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        drive_file_id="=js: vars.iteration-response.driveFileId",
        drive_copy_name="=js:(vars.iteration-response.copyName)",
    )
    checker.require_sequential_attachment_loop(elements, variables, ids_to_names)


def test_attachment_loop_rejects_drive_lineage_from_iterator() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        drive_file_id="=iterator[0].item.driveFileId",
    )
    with raises(SystemExit, match="exact ScriptTask response field"):
        checker.require_sequential_attachment_loop(
            elements, variables, ids_to_names
        )


def test_attachment_loop_rejects_drive_lineage_from_unrelated_variable() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        drive_copy_name="=vars.unrelated-copy-result.copyName",
    )
    with raises(SystemExit, match="exact ScriptTask response field"):
        checker.require_sequential_attachment_loop(
            elements, variables, ids_to_names
        )


def test_attachment_loop_rejects_script_result_from_another_item() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            "return { itemName: currentItem.name, "
            "copyName: vars.attachments[0].name, "
            "driveFileId: vars.attachments[0].driveFileId };"
        ),
    )
    with raises(SystemExit, match="must derive.*currentItem"):
        checker.require_sequential_attachment_loop(
            elements, variables, ids_to_names
        )


def test_attachment_loop_requires_correlation_in_copy_name() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            "return { itemName: currentItem.name, "
            "copyName: currentItem.name, "
            "driveFileId: currentItem.driveFileId };"
        ),
    )
    with raises(SystemExit, match="plus vars.input-correlation-c81"):
        checker.require_sequential_attachment_loop(
            elements, variables, ids_to_names
        )


def test_attachment_loop_rejects_comma_operator_lineage() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            "return { itemName: currentItem.name, "
            "copyName: vars.input-correlation-c81 + '-' + "
            "currentItem.name, "
            "driveFileId: (currentItem.driveFileId, "
            "vars.attachments[0].driveFileId) };"
        ),
    )
    with raises(SystemExit, match="driveFileId must derive exactly"):
        checker.require_sequential_attachment_loop(
            elements, variables, ids_to_names
        )


def test_attachment_loop_rejects_trailing_comma_return_object() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            "return { itemName: currentItem.name, "
            "copyName: vars.input-correlation-c81 + '-' + "
            "currentItem.name, "
            "driveFileId: currentItem.driveFileId }, "
            "{ itemName: vars.attachments[0].name, "
            "copyName: 'wrong', "
            "driveFileId: vars.attachments[0].driveFileId };"
        ),
    )
    with raises(SystemExit, match="trailing comma expression"):
        checker.require_sequential_attachment_loop(
            elements, variables, ids_to_names
        )


def test_attachment_loop_rejects_non_object_response_schema_root() -> None:
    elements, variables, ids_to_names = attachment_fixture()
    schema = json.loads(variables["attachmentPrepResult"].text or "{}")
    schema["type"] = "string"
    variables["attachmentPrepResult"].text = json.dumps(schema)
    with raises(SystemExit, match="response schema must require"):
        checker.require_sequential_attachment_loop(
            elements,
            variables,
            ids_to_names,
        )


def test_attachment_loop_accepts_comma_inside_copy_name_literal() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            "return { itemName: currentItem.name, "
            "copyName: vars.input-correlation-c81 + ', ' + "
            "currentItem.name, "
            "driveFileId: currentItem.driveFileId };"
        ),
    )
    checker.require_sequential_attachment_loop(
        elements,
        variables,
        ids_to_names,
    )


def test_attachment_loop_accepts_unconditional_template_copy_name() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            "return { itemName: currentItem.name, "
            "copyName: `${vars.input-correlation-c81}, "
            "${currentItem.name}`, "
            "driveFileId: currentItem.driveFileId };"
        ),
    )
    checker.require_sequential_attachment_loop(
        elements,
        variables,
        ids_to_names,
    )


def test_attachment_loop_rejects_conditional_copy_name_parts() -> None:
    expressions = (
        "false ? currentItem.name : vars.input-correlation-c81",
        "true ? currentItem.name : vars.input-correlation-c81",
    )
    for copy_name in expressions:
        elements, variables, ids_to_names = attachment_fixture(
            marker_script=(
                "return { itemName: currentItem.name, "
                f"copyName: {copy_name}, "
                "driveFileId: currentItem.driveFileId };"
            ),
        )
        with raises(SystemExit, match="copyName must derive only"):
            checker.require_sequential_attachment_loop(
                elements,
                variables,
                ids_to_names,
            )


def test_attachment_loop_rejects_alias_forged_only_in_comment() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            'const { item } = { item: { name: "WRONG", '
            'driveFileId: "WRONG" } }; '
            "// const item = currentItem;\n"
            "return { itemName: item.name, "
            "copyName: vars.input-correlation-c81 + '-' + item.name, "
            "driveFileId: item.driveFileId };"
        ),
    )
    with raises(
        SystemExit,
        match="mapped current item|itemName must derive exactly",
    ):
        checker.require_sequential_attachment_loop(
            elements,
            variables,
            ids_to_names,
        )


def test_attachment_loop_rejects_alias_forged_in_regex_literal() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            'const { item } = { item: { name: "WRONG", '
            'driveFileId: "WRONG" } }; '
            r"/\/\/ const item = currentItem;/; "
            "return { itemName: item.name, "
            "copyName: vars.input-correlation-c81 + '-' + item.name, "
            "driveFileId: item.driveFileId };"
        ),
    )
    with raises(
        SystemExit,
        match="mapped current item|itemName must derive exactly",
    ):
        checker.require_sequential_attachment_loop(
            elements,
            variables,
            ids_to_names,
        )


def test_attachment_loop_rejects_mutation_in_template_interpolation() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            '`${Object.assign(currentItem, {name: "WRONG", '
            'driveFileId: "WRONG"})}`; '
            "return { itemName: currentItem.name, "
            "copyName: vars.input-correlation-c81 + '-' + "
            "currentItem.name, "
            "driveFileId: currentItem.driveFileId };"
        ),
    )
    with raises(SystemExit, match="must not reassign or mutate"):
        checker.require_sequential_attachment_loop(
            elements,
            variables,
            ids_to_names,
        )


def test_attachment_loop_rejects_escaped_template_placeholders() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            "return { itemName: currentItem.name, "
            r"copyName: `\${vars.input-correlation-c81}-"
            r"\${currentItem.name}`, "
            "driveFileId: currentItem.driveFileId };"
        ),
    )
    with raises(SystemExit, match="copyName must derive only"):
        checker.require_sequential_attachment_loop(
            elements,
            variables,
            ids_to_names,
        )


def test_attachment_loop_rejects_first_item_reducer() -> None:
    elements, variables, ids_to_names = attachment_fixture()
    reducer_script = elements[1].find(
        f"./{checker.q(checker.BPMN_NS, 'script')}"
    )
    assert reducer_script is not None
    reducer_script.text = (
        "vars.iteration-names-q37.length; "
        "return vars.iteration-names-q37[0];"
    )
    with raises(SystemExit, match="actually return the final attachment"):
        checker.require_sequential_attachment_loop(
            elements,
            variables,
            ids_to_names,
        )


def test_attachment_loop_accepts_at_negative_one_reducer() -> None:
    elements, variables, ids_to_names = attachment_fixture()
    reducer_script = elements[1].find(
        f"./{checker.q(checker.BPMN_NS, 'script')}"
    )
    assert reducer_script is not None
    reducer_script.text = "return vars.iteration-names-q37.at(-1);"
    checker.require_sequential_attachment_loop(
        elements,
        variables,
        ids_to_names,
    )


def test_parallel_outputs_require_exclusive_ownership() -> None:
    assert checker.parallel_output_ownership_order(
        [
            {"jiraAction", "jiraInternal"},
            {
                "attachmentAction",
                "lastAttachmentName",
                "attachmentInternal",
            },
            {"slackAction", "responseMode", "communicationInternal"},
        ]
    ) == (0, 1, 2)
    with raises(SystemExit, match="exclusively own"):
        checker.parallel_output_ownership_order(
            [
                {"jiraAction", "slackAction"},
                {"attachmentAction", "lastAttachmentName"},
                {"slackAction", "responseMode"},
            ]
        )


def test_return_newline_before_object_is_rejected() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            "return\n"
            "{ itemName: currentItem.name, "
            "copyName: vars.input-correlation-c81 + '-' + "
            "currentItem.name, "
            "driveFileId: currentItem.driveFileId };"
        ),
    )
    with raises(SystemExit, match="must return one object"):
        checker.require_sequential_attachment_loop(
            elements,
            variables,
            ids_to_names,
        )


def test_attachment_loop_rejects_reassigned_item_alias() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            "let selected = currentItem; "
            "selected = vars.attachments[0]; "
            "return { itemName: selected.name, "
            "copyName: vars.input-correlation-c81 + '-' + selected.name, "
            "driveFileId: selected.driveFileId };"
        ),
    )
    with raises(SystemExit, match="itemName must derive exactly"):
        checker.require_sequential_attachment_loop(
            elements, variables, ids_to_names
        )


def test_attachment_loop_rejects_duplicate_returned_field() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        marker_script=(
            "return { itemName: currentItem.name, "
            "copyName: vars.input-correlation-c81 + '-' + "
            "currentItem.name, "
            "driveFileId: currentItem.driveFileId, "
            "driveFileId: vars.attachments[0].driveFileId };"
        ),
    )
    with raises(SystemExit, match="exactly once"):
        checker.require_sequential_attachment_loop(
            elements, variables, ids_to_names
        )


def test_attachment_loop_requires_runtime_script_response_mapping() -> None:
    elements, variables, ids_to_names = attachment_fixture()
    output = elements[0].find(
        f".//{checker.q(checker.UIPATH_NS, 'output')}"
        "[@name='scriptResponse']"
    )
    assert output is not None
    output.attrib["source"] = "=vars.unrelated"
    with raises(SystemExit, match="map one declared response"):
        checker.require_sequential_attachment_loop(
            elements, variables, ids_to_names
        )


def test_attachment_loop_rejects_unmapped_iterator_global() -> None:
    elements, variables, ids_to_names = attachment_fixture(
        "return { name: iterator[0].item.name };"
    )
    with raises(SystemExit, match="must read its mapped current item"):
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


def test_attachment_loop_rejects_wrong_subprocess_input_element() -> None:
    elements, variables, ids_to_names = attachment_fixture()
    loop = elements[0].find(
        f"./{checker.q(checker.BPMN_NS, 'multiInstanceLoopCharacteristics')}/"
        f"{checker.q(checker.BPMN_NS, 'extensionElements')}/"
        f"{checker.q(checker.UIPATH_NS, 'loopCharacteristics')}"
    )
    assert loop is not None
    loop.attrib["inputElement"] = "item"
    with raises(SystemExit, match=r"must bind.*iterator\[0\]"):
        checker.require_sequential_attachment_loop(
            elements,
            variables,
            ids_to_names,
        )


class StructureCheckerTests(unittest.TestCase):
    def test_command_guard_handles_executable_prefixes(self) -> None:
        test_command_guard_covers_executable_shell_prefixes()

    def test_connector_values_must_reference_exact_runtime_variables(
        self,
    ) -> None:
        declaration = variable(
            "correlationId", "runtime-correlation-a19"
        )
        checker.require_variable_reference(
            "=js:'Case ' + vars.runtime-correlation-a19",
            declaration,
            "message",
        )
        with raises(SystemExit, match=r"must reference vars\.runtime"):
            checker.require_variable_reference(
                "=js:'hardcoded'",
                declaration,
                "message",
            )

    def test_connector_semantic_values_cannot_be_literals(self) -> None:
        checker.require_semantic_reference(
            "=vars.prepared.driveFileId",
            {"drive", "file", "id"},
            "fileId",
        )
        with raises(SystemExit, match="must be a dynamic expression"):
            checker.require_semantic_reference(
                "1YlblU34Vd6RvCkamYw5BWejdX8ES-Zzy",
                {"drive", "file", "id"},
                "fileId",
            )

    def test_attachment_argument_schema_requires_both_properties(self) -> None:
        elements, variables, ids_to_names = attachment_fixture()
        schema_node = elements[0].find(
            f".//{checker.q(checker.UIPATH_NS, 'inputSchema')}"
        )
        assert schema_node is not None
        schema = json.loads(schema_node.text or "{}")
        del schema["properties"]["currentItem"]["required"]
        schema_node.text = json.dumps(schema)
        with raises(SystemExit, match="must require string name"):
            checker.require_sequential_attachment_loop(
                elements, variables, ids_to_names
            )

    def test_registry_filename_is_not_prescribed(self) -> None:
        test_registry_evidence_is_discovered_by_content_not_filename()

    def test_script_registry_variables_mapping_is_current(self) -> None:
        test_script_registry_accepts_variables_mapping_template()

    def test_script_registry_stale_live_shape_is_valid_evidence(self) -> None:
        test_script_registry_retains_stale_live_mapping_template()

    def test_following_variables_extraction_is_valid(self) -> None:
        test_normalization_accepts_following_variables_extraction()

    def test_visible_exact_correlation_copy_is_valid(self) -> None:
        test_normalization_accepts_visible_exact_correlation_copy()

    def test_other_scoped_errors_do_not_confuse_normalization(self) -> None:
        test_normalization_tolerates_other_scripts_same_named_errors()

    def test_visible_transformed_correlation_copy_is_rejected(self) -> None:
        test_normalization_rejects_transformed_visible_correlation_copy()

    def test_local_correlation_alias_is_valid(self) -> None:
        test_normalization_accepts_exact_correlation_through_local_alias()

    def test_semantic_correlation_result_property_is_valid(self) -> None:
        test_normalization_accepts_semantic_correlation_result_property()

    def test_normalization_response_dereferences_are_typed(self) -> None:
        test_normalization_rejects_untyped_dereferenced_response_fields()

    def test_string_identity_empty_fallback_is_valid(self) -> None:
        test_normalization_accepts_string_identity_empty_fallback()

    def test_arbitrary_normalization_ids(self) -> None:
        test_normalization_accepts_semantic_mapping_with_arbitrary_ids()

    def test_jira_update_uses_normalized_duplicate(self) -> None:
        test_jira_update_accepts_exact_normalized_duplicate()

    def test_jira_update_accepts_equivalent_js_reference(self) -> None:
        test_jira_update_accepts_equivalent_js_normalized_duplicate()

    def test_jira_update_accepts_js_prefix_on_each_link(self) -> None:
        test_jira_update_accepts_js_prefix_on_each_normalized_link()

    def test_jira_update_cannot_use_raw_duplicate(self) -> None:
        test_jira_update_rejects_raw_duplicate_input()

    def test_jira_update_cannot_use_reassigned_alias(self) -> None:
        test_jira_update_rejects_reassigned_normalization_alias()

    def test_jira_update_cannot_repeat_returned_key(self) -> None:
        test_jira_update_rejects_duplicate_returned_key()

    def test_jira_update_cannot_swap_return_with_comma_operator(self) -> None:
        test_jira_update_rejects_trailing_comma_return_object()

    def test_jira_response_schema_must_be_an_object(self) -> None:
        test_jira_update_rejects_non_object_response_schema_root()

    def test_return_scanner_ignores_inert_return_text(self) -> None:
        test_return_scanner_ignores_comments_and_string_literals()

    def test_javascript_mask_tracks_executable_template_code(self) -> None:
        test_javascript_mask_hides_regex_and_exposes_template_code()

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

    def test_material_jira_assignments_are_valid(self) -> None:
        test_jira_workstream_accepts_material_route_assignments()

    def test_jira_self_assignment_is_rejected(self) -> None:
        test_jira_workstream_rejects_noop_self_assignment()

    def test_assessment_cannot_own_downstream_intent(self) -> None:
        test_assessment_rejects_downstream_intent_assignment()

    def test_variable_references_are_exact(self) -> None:
        test_condition_variable_ids_do_not_prefix_match()

    def test_descriptive_subprocess_mapping_name(self) -> None:
        test_subprocess_propagation_accepts_descriptive_mapping_name()

    def test_subprocess_mapping_target_must_match(self) -> None:
        test_subprocess_propagation_rejects_unrelated_target()

    def test_arbitrary_attachment_ids(self) -> None:
        test_attachment_loop_accepts_arbitrary_variable_ids()

    def test_drive_inputs_follow_per_item_script_response(self) -> None:
        test_attachment_loop_accepts_drive_lineage_from_script_response()

    def test_drive_inputs_allow_js_expression_prefix(self) -> None:
        test_attachment_loop_accepts_js_prefixed_script_response()

    def test_drive_file_id_cannot_bypass_script_response(self) -> None:
        test_attachment_loop_rejects_drive_lineage_from_iterator()

    def test_drive_copy_name_cannot_use_unrelated_variable(self) -> None:
        test_attachment_loop_rejects_drive_lineage_from_unrelated_variable()

    def test_script_result_cannot_swap_in_another_attachment(self) -> None:
        test_attachment_loop_rejects_script_result_from_another_item()

    def test_copy_name_must_include_correlation(self) -> None:
        test_attachment_loop_requires_correlation_in_copy_name()

    def test_script_result_cannot_use_comma_operator(self) -> None:
        test_attachment_loop_rejects_comma_operator_lineage()

    def test_script_result_cannot_swap_return_with_comma_operator(
        self,
    ) -> None:
        test_attachment_loop_rejects_trailing_comma_return_object()

    def test_attachment_response_schema_must_be_an_object(self) -> None:
        test_attachment_loop_rejects_non_object_response_schema_root()

    def test_copy_name_can_contain_literal_comma(self) -> None:
        test_attachment_loop_accepts_comma_inside_copy_name_literal()

    def test_copy_name_can_use_unconditional_template(self) -> None:
        test_attachment_loop_accepts_unconditional_template_copy_name()

    def test_copy_name_cannot_conditionally_omit_required_parts(
        self,
    ) -> None:
        test_attachment_loop_rejects_conditional_copy_name_parts()

    def test_item_alias_cannot_be_forged_in_comment(self) -> None:
        test_attachment_loop_rejects_alias_forged_only_in_comment()

    def test_item_alias_cannot_be_forged_in_regex(self) -> None:
        test_attachment_loop_rejects_alias_forged_in_regex_literal()

    def test_template_interpolation_mutation_is_executable(self) -> None:
        test_attachment_loop_rejects_mutation_in_template_interpolation()

    def test_escaped_template_placeholders_do_not_count(self) -> None:
        test_attachment_loop_rejects_escaped_template_placeholders()

    def test_reducer_cannot_return_first_item(self) -> None:
        test_attachment_loop_rejects_first_item_reducer()

    def test_reducer_can_use_negative_one_at(self) -> None:
        test_attachment_loop_accepts_at_negative_one_reducer()

    def test_parallel_output_ownership_is_exclusive(self) -> None:
        test_parallel_outputs_require_exclusive_ownership()

    def test_return_object_cannot_start_after_line_terminator(self) -> None:
        test_return_newline_before_object_is_rejected()

    def test_script_result_cannot_reassign_item_alias(self) -> None:
        test_attachment_loop_rejects_reassigned_item_alias()

    def test_script_result_cannot_repeat_returned_field(self) -> None:
        test_attachment_loop_rejects_duplicate_returned_field()

    def test_script_response_must_use_runtime_result_mapping(self) -> None:
        test_attachment_loop_requires_runtime_script_response_mapping()

    def test_non_iterator_script_rejected(self) -> None:
        test_attachment_loop_rejects_unmapped_iterator_global()

    def test_parallel_attachment_loop_rejected(self) -> None:
        test_attachment_loop_rejects_parallel_iteration()

    def test_task_input_element_alias_rejected(self) -> None:
        test_attachment_loop_rejects_wrong_subprocess_input_element()


if __name__ == "__main__":
    unittest.main()

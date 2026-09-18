#!/usr/bin/env python3
"""Unit tests for check_script_jint_guidance.py.

The check was rewritten twice in one day (#3377) after #2366 shipped an
assertion inverted against #3211's verified canvas contract, and each break
surfaced only as a red nightly days later. These tests pin the contract
directly: the golden artifact is the shape the 2026-09-17 nightly agents
actually authored (both harnesses), and each mutation is a regression that a
nightly already caught once.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CHECK = Path(__file__).resolve().parent / "check_script_jint_guidance.py"

PROJECT_JSON = '{"Name": "RiskScoreScriptBpmn", "ProjectType": "ProcessOrchestration"}'

GOLDEN_BPMN = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:uipath="http://uipath.org/schema/bpmn" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI">
  <bpmn:process id="Process_1" name="Maestro Process">
    <bpmn:extensionElements>
      <uipath:variables version="v1">
        <uipath:input id="input_Var_Amount" name="amount" type="number" elementId="Event_start" />
        <uipath:input id="input_Var_DaysOverdue" name="daysOverdue" type="integer" elementId="Event_start" />
        <uipath:inputOutput id="Var_Amount" name="amount" type="double" elementId="Process_1" />
        <uipath:inputOutput id="Var_DaysOverdue" name="daysOverdue" type="integer" elementId="Process_1" />
        <uipath:inputOutput id="Var_ScriptResponse" name="scriptResponse" type="double" elementId="Task_RiskScore" />
        <uipath:inputOutput id="Var_ScriptError" name="Error" type="jsonSchema" elementId="Task_RiskScore"><![CDATA[{"type":"object","properties":{"code":{"type":"string"},"message":{"type":"string"},"detail":{"type":"string"},"category":{"type":"string"},"status":{"type":"number"},"element":{"type":"string"}}}]]></uipath:inputOutput>
        <uipath:inputOutput id="Var_RiskScore" name="riskScore" type="double" elementId="Task_RiskScore" />
        <uipath:output id="output_Var_RiskScore" name="riskScore" type="number" elementId="End_Complete" />
      </uipath:variables>
    </bpmn:extensionElements>
    <bpmn:startEvent id="Event_start" name="core.trigger.manual">
      <bpmn:extensionElements>
        <uipath:entryPointId value="3f32163a-65b8-4d51-b778-a05e9ca18a3e" />
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1" />
          <uipath:output name="amount" type="double" var="Var_Amount" source="=vars.input_Var_Amount" />
          <uipath:output name="daysOverdue" type="integer" var="Var_DaysOverdue" source="=vars.input_Var_DaysOverdue" />
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:scriptTask id="Task_RiskScore" name="Calculate risk score" scriptFormat="JavaScript">
      <bpmn:extensionElements>
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1" />
          <uipath:context>
            <uipath:inputSchema type="jsonSchema"><![CDATA[{"type":"object","properties":{"vars":{"type":"object"},"metadata":{"type":"object"}},"required":[]}]]></uipath:inputSchema>
          </uipath:context>
          <uipath:input name="args" type="json" target="bodyField"><![CDATA[{"vars":"=vars","metadata":"=metadata"}]]></uipath:input>
          <uipath:output name="scriptResponse" type="double" var="Var_ScriptResponse" source="=result.response" />
          <uipath:output name="Error" type="jsonSchema" var="Var_ScriptError" source="=Error" />
          <uipath:output name="riskScore" type="double" var="Var_RiskScore" source="=vars.Var_ScriptResponse" custom="true" />
        </uipath:mapping>
        <uipath:scriptVersion value="v3" />
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
      <bpmn:script><![CDATA[
var amount = vars.Var_Amount;
var daysOverdue = vars.Var_DaysOverdue;
var score = amount * 0.02 + daysOverdue * 1.5;
if (score < 0) { score = 0; }
if (score > 100) { score = 100; }
return score;
]]></bpmn:script>
    </bpmn:scriptTask>
    <bpmn:endEvent id="End_Complete" name="Complete">
      <bpmn:extensionElements>
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1" />
          <uipath:output name="riskScore" type="double" var="output_Var_RiskScore" source="=vars.Var_RiskScore" />
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_2</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="Event_start" targetRef="Task_RiskScore" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_RiskScore" targetRef="End_Complete" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="Diagram_1">
    <bpmndi:BPMNPlane id="Plane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="S_Event_start" bpmnElement="Event_start">
        <dc:Bounds x="256" y="144" width="96" height="96" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_Task_RiskScore" bpmnElement="Task_RiskScore">
        <dc:Bounds x="420" y="132" width="120" height="120" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="S_End_Complete" bpmnElement="End_Complete">
        <dc:Bounds x="600" y="144" width="96" height="96" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="E_Flow_1" bpmnElement="Flow_1">
        <di:waypoint x="352" y="192" />
        <di:waypoint x="420" y="192" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="E_Flow_2" bpmnElement="Flow_2">
        <di:waypoint x="540" y="192" />
        <di:waypoint x="600" y="192" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
"""


def run_check(tmp_path: Path, bpmn: str) -> subprocess.CompletedProcess[str]:
    project = tmp_path / "RiskScoreScriptBpmn"
    project.mkdir()
    (project / "RiskScoreScriptBpmn.bpmn").write_text(bpmn, encoding="utf-8")
    (project / "project.uiproj").write_text(PROJECT_JSON, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(CHECK)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )


def test_golden_artifact_passes(tmp_path: Path) -> None:
    result = run_check(tmp_path, GOLDEN_BPMN)
    assert result.returncode == 0, result.stderr


def test_elementid_less_bridge_fails(tmp_path: Path) -> None:
    # The #3211-broken shape: a root declaration without an elementId does not
    # exist to the canvas. #2366's check REQUIRED this shape; the fixed check
    # must reject it.
    bpmn = GOLDEN_BPMN.replace(
        '<uipath:inputOutput id="Var_Amount" name="amount" type="double" elementId="Process_1" />',
        '<uipath:inputOutput id="Var_Amount" name="amount" type="double" />',
    )
    result = run_check(tmp_path, bpmn)
    assert result.returncode == 1
    assert "#3211" in result.stderr


def test_internal_display_names_are_free(tmp_path: Path) -> None:
    # Regression from verify run 35231234041: a correct bridge whose internal
    # variables are named Amount/DaysOverdue must pass — display names carry
    # no runtime meaning; expressions resolve ids.
    bpmn = (
        GOLDEN_BPMN.replace(
            'id="Var_Amount" name="amount"', 'id="Var_Amount" name="Amount"'
        )
        .replace(
            'id="Var_DaysOverdue" name="daysOverdue"',
            'id="Var_DaysOverdue" name="DaysOverdue"',
        )
        .replace(
            '<uipath:output name="amount" type="double" var="Var_Amount"',
            '<uipath:output name="Amount" type="double" var="Var_Amount"',
        )
        .replace(
            '<uipath:output name="daysOverdue" type="integer" var="Var_DaysOverdue"',
            '<uipath:output name="DaysOverdue" type="integer" var="Var_DaysOverdue"',
        )
    )
    result = run_check(tmp_path, bpmn)
    assert result.returncode == 0, result.stderr


def test_end_bridge_display_name_is_free(tmp_path: Path) -> None:
    # The EndEvent mapping output's name is display metadata; the public
    # contract is the uipath:output declaration, which stays pinned.
    bpmn = GOLDEN_BPMN.replace(
        '<uipath:output name="riskScore" type="double" var="output_Var_RiskScore"',
        '<uipath:output name="result" type="double" var="output_Var_RiskScore"',
    )
    result = run_check(tmp_path, bpmn)
    assert result.returncode == 0, result.stderr


def test_bridge_output_types_are_free(tmp_path: Path) -> None:
    # Regression from verify run 35232593678: mapping-output `type` is
    # serialization metadata — the type contract is enforced on the variable
    # declarations. An agent typing the end bridge "number" (the public
    # declaration's refresh-vocabulary type) or a start bridge "number" must
    # pass.
    bpmn = GOLDEN_BPMN.replace(
        '<uipath:output name="riskScore" type="double" var="output_Var_RiskScore"',
        '<uipath:output name="riskScore" type="number" var="output_Var_RiskScore"',
    ).replace(
        '<uipath:output name="amount" type="double" var="Var_Amount"',
        '<uipath:output name="amount" type="number" var="Var_Amount"',
    )
    result = run_check(tmp_path, bpmn)
    assert result.returncode == 0, result.stderr


def test_missing_start_bridge_fails(tmp_path: Path) -> None:
    bpmn = GOLDEN_BPMN.replace(
        '<uipath:output name="amount" type="double" var="Var_Amount" source="=vars.input_Var_Amount" />',
        "",
    )
    result = run_check(tmp_path, bpmn)
    assert result.returncode == 1
    assert "variable bridge" in result.stderr

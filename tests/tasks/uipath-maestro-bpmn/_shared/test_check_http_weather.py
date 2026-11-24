"""check_http_weather.py: the skill's `.http()` manual request passes; the older HttpExecution form does not.

Shapes: `.http()` -> Intsvc.UnifiedHttpRequest with body authentication "manual",
versus the older Intsvc.HttpExecution type, which the skill does not prescribe.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

CHECK = Path(__file__).resolve().parent / "check_http_weather.py"

BPMN = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:uipath="http://uipath.org/schema/bpmn" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="D">
  <bpmn:process id="P" isExecutable="true">
    <bpmn:extensionElements><uipath:variables version="v1"><uipath:inputOutput id="weather" name="weather" type="json" elementId="get" /></uipath:variables></bpmn:extensionElements>
    <bpmn:startEvent id="S"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sendTask id="get">
      <bpmn:extensionElements><uipath:activity version="v1">
        <uipath:type value="{type}" version="v1" />
        <uipath:input name="body" type="json" target="body">{body}</uipath:input>
        <uipath:output name="body" type="object" source="=response.body" var="weather" />
      </uipath:activity></bpmn:extensionElements>
      <bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing>
    </bpmn:sendTask>
    <bpmn:endEvent id="E"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent>
    <bpmn:sequenceFlow id="F1" sourceRef="S" targetRef="get" />
    <bpmn:sequenceFlow id="F2" sourceRef="get" targetRef="E" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="Dg"><bpmndi:BPMNPlane id="Pl" bpmnElement="P">
    <bpmndi:BPMNShape id="sS" bpmnElement="S"><dc:Bounds x="0" y="0" width="36" height="36" /></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="sG" bpmnElement="get"><dc:Bounds x="80" y="0" width="100" height="80" /></bpmndi:BPMNShape>
    <bpmndi:BPMNShape id="sE" bpmnElement="E"><dc:Bounds x="230" y="0" width="36" height="36" /></bpmndi:BPMNShape>
    <bpmndi:BPMNEdge id="eF1" bpmnElement="F1"><di:waypoint x="36" y="18" /><di:waypoint x="80" y="18" /></bpmndi:BPMNEdge>
    <bpmndi:BPMNEdge id="eF2" bpmnElement="F2"><di:waypoint x="180" y="18" /><di:waypoint x="230" y="18" /></bpmndi:BPMNEdge>
  </bpmndi:BPMNPlane></bpmndi:BPMNDiagram>
</bpmn:definitions>
"""
GOOD = '{"authentication":"manual","method":"GET","url":"https://api.open-meteo.com/v1/forecast?latitude=47.6&amp;longitude=-122.2&amp;current=temperature_2m"}'


def _run(tmp_path: Path, type_: str, body: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / "OpenMeteoWeatherHttp").mkdir()
    text = BPMN.replace("{type}", type_).replace("{body}", body)
    (tmp_path / "OpenMeteoWeatherHttp" / "OpenMeteoWeatherHttp.bpmn").write_text(text, encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECK)], cwd=tmp_path, capture_output=True, text=True, check=False)


def test_unified_http_manual_get_passes(tmp_path: Path) -> None:
    result = _run(tmp_path, "Intsvc.UnifiedHttpRequest", GOOD)
    assert result.returncode == 0, result.stderr


def test_http_execution_type_fails(tmp_path: Path) -> None:
    result = _run(tmp_path, "Intsvc.HttpExecution", GOOD)
    assert result.returncode == 1
    assert "not the type" in result.stderr


def test_connector_mode_fails(tmp_path: Path) -> None:
    body = GOOD.replace('"manual"', '"connector"')
    result = _run(tmp_path, "Intsvc.UnifiedHttpRequest", body)
    assert result.returncode == 1
    assert "connectionless" in result.stderr


def test_post_or_other_host_fails(tmp_path: Path) -> None:
    assert _run(tmp_path, "Intsvc.UnifiedHttpRequest", GOOD.replace("GET", "POST")).returncode == 1


def test_other_host_fails(tmp_path: Path) -> None:
    assert _run(tmp_path, "Intsvc.UnifiedHttpRequest", GOOD.replace("open-meteo", "example")).returncode == 1

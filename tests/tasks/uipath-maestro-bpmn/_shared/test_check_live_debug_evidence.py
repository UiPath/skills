"""`check_live_debug.py` finds the agent's debug-evidence/ in the Studio Web layout too.

Studio Web cannot create a root folder (a root folder is a project), so in CI runs
43938818401 and 43938825370 the agent saved correct evidence (`FinalStatus:
Completed`, `Globals.Product: 42`) at `ProductCalc/ProductCalc/debug-evidence/`,
and the root-only glob failed it. Evidence must count at any depth, and a run that
never completed must still fail.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_CHECK = Path(__file__).resolve().parents[1] / "debug" / "live_debug_e2e" / "check_live_debug.py"

_BPMN = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:uipath="http://uipath.org/schema/bpmn" id="Definitions_1" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:extensionElements>
      <uipath:variables version="v1">
        <uipath:inputOutput id="product" name="product" type="integer" elementId="Process_1" />
      </uipath:variables>
    </bpmn:extensionElements>
    <bpmn:startEvent id="Event_start" />
    <bpmn:scriptTask id="calculate" scriptFormat="JavaScript">
      <bpmn:extensionElements>
        <uipath:mapping version="v1">
          <uipath:input name="args" type="json" target="bodyField"><![CDATA[{}]]></uipath:input>
          <uipath:output name="product" type="integer" source="=result.response" var="product" />
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:script>return 6 * 7;</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:endEvent id="Event_end" />
  </bpmn:process>
</bpmn:definitions>
"""

_DEBUG = {"Result": "Success", "Code": "MaestroDebug", "Data": {"InstanceId": "inst-1", "FinalStatus": "Completed"}}
_VARIABLES = {
    "Result": "Success",
    "Code": "DebugInstanceVariables",
    "Data": {"Globals": {"Product": 42}, "GlobalDefinitions": {"Product": {"Name": "product", "Type": "integer"}}},
}


def _sandbox(root: Path, evidence_dir: str, debug: dict = _DEBUG) -> Path:
    project = root / "ProductCalc" / "ProductCalc"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text('{"Name": "ProductCalc", "ProjectType": "ProcessOrchestration"}')
    (project / "ProductCalc.bpmn").write_text(_BPMN)
    evidence = root / evidence_dir
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "debug.json").write_text(debug["Data"]["FinalStatus"] + "\nExecution trace:\n" + json.dumps(debug))
    (evidence / "variables.json").write_text(json.dumps(_VARIABLES))
    return root


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PATH": os.path.dirname(sys.executable)}  # no `uip`: live recovery cannot mask a failure
    return subprocess.run([sys.executable, str(_CHECK)], cwd=root, env=env, capture_output=True, text=True, timeout=60)


@pytest.mark.parametrize("evidence_dir", ["debug-evidence", "ProductCalc/ProductCalc/debug-evidence"])
def test_completed_evidence_counts_at_root_or_inside_the_project(tmp_path: Path, evidence_dir: str) -> None:
    result = _run(_sandbox(tmp_path, evidence_dir))
    assert result.returncode == 0, result.stderr
    assert "PASS: all live-debug checks passed" in result.stdout


def test_a_run_that_never_completed_fails(tmp_path: Path) -> None:
    faulted = {**_DEBUG, "Data": {**_DEBUG["Data"], "FinalStatus": "Faulted"}}
    result = _run(_sandbox(tmp_path, "ProductCalc/ProductCalc/debug-evidence", debug=faulted))
    assert result.returncode != 0
    assert "finalStatus == 'Completed'" in result.stderr


def test_evidence_outside_a_debug_evidence_dir_does_not_count(tmp_path: Path) -> None:
    result = _run(_sandbox(tmp_path, "ProductCalc/ProductCalc/other"))
    assert result.returncode != 0
    assert "finalStatus == 'Completed'" in result.stderr

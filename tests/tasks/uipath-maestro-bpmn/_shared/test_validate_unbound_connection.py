"""validate_bpmn.py --accept-unbound-connection: the documented refusal, and nothing else.

The validate payload below is the one R14 v2 query-params got from
`uip maestro bpmn validate`, after the agent declined to bind the tenant's only
HTTP connection (another user's "Spotify") to a Google Tasks call
(builder-sdk#1884). The BPMN is the relevant slice of that agent's file.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_SHARED = Path(__file__).resolve().parent


def _load():
    spec = importlib.util.spec_from_file_location("validate_bpmn", _SHARED / "validate_bpmn.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_bpmn = _load()

BPMN = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:uipath="http://uipath.org/schema/bpmn">
  <bpmn:process id="Process_1">
    <bpmn:extensionElements>
      <uipath:bindings version="v1">
        <uipath:binding id="listTasks_connection" name="uipath-uipath-http connection" type="string" default="{default}" resource="Connection" resourceKey="googleTasksHttp" propertyAttribute="ConnectionId" />
      </uipath:bindings>
    </bpmn:extensionElements>
    <bpmn:sendTask id="listTasks" name="List Google Tasks (including hidden)">
      <bpmn:extensionElements>
        <uipath:activity version="v1">
          <uipath:type value="Intsvc.ActivityExecution" version="v1" />
          <uipath:context>
            <uipath:input name="connectorKey" type="string" value="{connector}" />
            <uipath:input name="connection" type="string" value="=bindings.listTasks_connection" />
          </uipath:context>
        </uipath:activity>
      </bpmn:extensionElements>
    </bpmn:sendTask>
  </bpmn:process>
</bpmn:definitions>
"""

MISSING_BINDING = (
    "  - [error] [listTasks] MISSING_BINDING: List Google Tasks (including hidden) has "
    "incorrectly configured uipath-uipath-http Fix: Check the binding default and any "
    "referenced folderKey companion."
)


def _payload(*lines: str) -> str:
    return json.dumps(
        {
            "Result": "Failure",
            "ErrorCode": "invalid_argument",
            "Instructions": f"Found {len(lines)} error(s):\n" + "\n".join(lines),
        }
    )


def _file(tmp_path: Path, default: str = "googleTasksHttp", connector: str = "uipath-uipath-http") -> Path:
    path = tmp_path / "QueryParamsTest.bpmn"
    path.write_text(BPMN.format(default=default, connector=connector), encoding="utf-8")
    return path


def test_the_r14_refusal_is_accepted(tmp_path) -> None:
    refusal = validate_bpmn.unbound_connection_refusal(
        _file(tmp_path), _payload(MISSING_BINDING), "uipath-uipath-http"
    )
    assert refusal == "listTasks -> 'googleTasksHttp'"


@pytest.mark.parametrize(
    ("default", "connector", "lines", "why"),
    [
        (
            "3f2a9c1e-0b7d-4e55-9a61-2c8d7e4f1a90",
            "uipath-uipath-http",
            (MISSING_BINDING,),
            "a GUID-shaped default is a made-up connection id, not a placeholder",
        ),
        (
            "googleTasksHttp",
            "uipath-google-tasks",
            (MISSING_BINDING,),
            "the node is not the connector the task allows unbound",
        ),
        (
            "googleTasksHttp",
            "uipath-uipath-http",
            (MISSING_BINDING, "  - [error] [listTasks] INVALID_EXPRESSION: bad path"),
            "any other error still fails",
        ),
        (
            "googleTasksHttp",
            "uipath-uipath-http",
            ("  - [error] [otherNode] MISSING_BINDING: x has incorrectly configured uipath-uipath-http",),
            "the error names a node the file does not have",
        ),
    ],
)
def test_anything_else_is_not_accepted(tmp_path, default, connector, lines, why) -> None:
    assert (
        validate_bpmn.unbound_connection_refusal(
            _file(tmp_path, default, connector), _payload(*lines), "uipath-uipath-http"
        )
        is None
    ), why


def test_an_unparseable_payload_is_not_accepted(tmp_path) -> None:
    assert validate_bpmn.unbound_connection_refusal(_file(tmp_path), "not json", "uipath-uipath-http") is None


def test_main_passes_only_with_the_flag(tmp_path, monkeypatch) -> None:
    _file(tmp_path)
    monkeypatch.chdir(tmp_path)

    class _Proc:
        returncode = 1
        stdout = _payload(MISSING_BINDING)
        stderr = ""

    monkeypatch.setattr(validate_bpmn.subprocess, "run", lambda *a, **k: _Proc())
    assert validate_bpmn.main([]) == 1
    assert validate_bpmn.main(["--accept-unbound-connection", "uipath-uipath-http"]) == 0

"""Unit tests for check_smoke_file_activities.py — purely structural, no CLI.

Run with ``pytest tests/tasks/uipath-maestro-flow/connector_features/datafabric_connector/test_check_smoke_file_activities.py``.

The shapes come from real eval artifacts of ``skill-flow-datafabric-smoke-file-activities``:
the v1 arm's configured connector nodes (pass), and the 2026-09-01 SDK arm, whose
``create-entity-record`` node was placed through ``rawNode`` and so carried its inputs
flat with no ``inputs.detail`` (fail — and the message must say the node is unconfigured,
not absent).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

CHECKER = Path(__file__).resolve().parent / "check_smoke_file_activities.py"
ENTITY = "FlowCodeEvalEntity"
DS = "uipath.connector.uipath-uipath-dataservice."


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CHECKER)], cwd=str(cwd), capture_output=True, text=True)


def _configured(node_id: str, action: str, *, path: dict[str, Any] | None = None,
                query: dict[str, Any] | None = None, body: dict[str, Any] | None = None,
                multipart: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    detail: dict[str, Any] = {
        "connector": "uipath-uipath-dataservice",
        "connectionId": "d61e5d0e-04af-4f93-95cc-151d81fa08dc",
        "connectionFolderKey": "c4359cde-55f0-4f0e-9322-c6cdce74ab4c",
        "pathParameters": path or {"entityName": ENTITY},
    }
    if query is not None:
        detail["queryParameters"] = query
    if body is not None:
        detail["bodyParameters"] = body
    if multipart is not None:
        detail["multipartParameters"] = multipart
    return {"id": node_id, "type": DS + action, "typeVersion": "1.0.0", "inputs": {"detail": detail}}


def _file_nodes(create_node: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {"id": "start", "type": "core.trigger.manual"},
        _configured("downloadFile", "download-file-from-record-field",
                    query={"recordId": "11111111-1111-4111-8111-111111111111", "_fieldName": "file1"}),
        create_node,
        _configured("uploadFile", "upload-file-to-record-field",
                    query={"recordId": "=js:$vars.createRecord.output.Id", "_fieldName": "file1"},
                    multipart=[{"name": "file", "dataType": "file", "value": "=js:$vars.downloadedFile"}]),
        _configured("deleteFile", "delete-file-from-record-field",
                    query={"recordId": "=js:$vars.createRecord.output.Id", "_fieldName": "file1"}),
        {"id": "end", "type": "core.control.end"},
    ]


def _write(tmp_path: Path, nodes: list[dict[str, Any]]) -> None:
    doc = {
        "id": "t", "version": "1.0.0", "name": "T", "nodes": nodes, "edges": [],
        "variables": {"globals": [{"id": "downloadedFile", "name": "downloadedFile",
                                   "direction": "inout", "type": "file"}],
                      "variableUpdates": {}},
    }
    (tmp_path / "TransferFile.flow").write_text(json.dumps(doc))


def test_configured_create_with_flat_body_passes(tmp_path: Path) -> None:
    create = _configured("createRecord", "create-entity-record",
                         body={"title": "t", "description": "d", "score": 42.5})
    _write(tmp_path, _file_nodes(create))
    r = _run(tmp_path)
    assert r.returncode == 0, r.stderr
    assert "OK:" in r.stdout


def test_raw_unconfigured_create_fails_and_is_named_as_unconfigured(tmp_path: Path) -> None:
    # The 2026-09-01 SDK artifact: inputs flat, no `detail` — an unconfigured node.
    raw_create = {"id": "createRecord", "type": DS + "create-entity-record", "typeVersion": "1.0.0",
                  "inputs": {"entityName": ENTITY, "body": {"title": "t", "description": "d", "score": 42.5}}}
    _write(tmp_path, _file_nodes(raw_create))
    r = _run(tmp_path)
    assert r.returncode == 1
    assert "no create-entity-record" in r.stderr
    assert "Unconfigured connector node(s) with no inputs.detail" in r.stderr
    assert "createRecord (create-entity-record)" in r.stderr


def test_nested_body_object_still_fails_on_required_fields(tmp_path: Path) -> None:
    # The 2026-08-31 22:43 SDK artifact: a forged overlay nested the body under `body`.
    create = _configured("createRecord", "create-entity-record",
                         body={"body": {"title": "t", "description": "d", "score": 42.5}})
    _write(tmp_path, _file_nodes(create))
    r = _run(tmp_path)
    assert r.returncode == 1
    assert "create body missing required fields" in r.stderr

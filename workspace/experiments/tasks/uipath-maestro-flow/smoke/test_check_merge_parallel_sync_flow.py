"""Unit tests for check_merge_parallel_sync_flow.py — purely structural, no CLI.

Run with ``pytest tests/tasks/uipath-maestro-flow/smoke/test_check_merge_parallel_sync_flow.py``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

CHECKER = Path(__file__).resolve().parent / "check_merge_parallel_sync_flow.py"


def _write_flow(tmp_path: Path, payload: dict[str, Any]) -> None:
    d = tmp_path / "ParallelSync" / "ParallelSync"
    d.mkdir(parents=True, exist_ok=True)
    (d / "ParallelSync.flow").write_text(json.dumps(payload))
    (d / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))


def _run(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)], cwd=str(cwd), capture_output=True, text=True
    )


def _out(r: subprocess.CompletedProcess[str]) -> str:
    return (r.stdout + r.stderr).lower()


def _well_formed() -> dict[str, Any]:
    """trigger forks to two script branches that converge on a merge -> end."""
    return {
        "version": "1.2",
        "nodes": [
            {"id": "start", "type": "core.trigger.manual", "typeVersion": "1.0",
             "display": {"label": "Manual trigger"}},
            {"id": "branchA", "type": "core.action.script", "typeVersion": "1.0",
             "display": {"label": "Branch A"}, "inputs": {"script": "return { ok: true };"}},
            {"id": "branchB", "type": "core.action.script", "typeVersion": "1.0",
             "display": {"label": "Branch B"}, "inputs": {"script": "return { ok: true };"}},
            {"id": "merge1", "type": "core.logic.merge", "typeVersion": "1.0",
             "display": {"label": "Join"}, "inputs": {}},
            {"id": "end1", "type": "core.control.end", "typeVersion": "1.0",
             "display": {"label": "End"}, "inputs": {}},
        ],
        "edges": [
            {"id": "e1", "sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "branchA", "targetPort": "input"},
            {"id": "e2", "sourceNodeId": "start", "sourcePort": "output", "targetNodeId": "branchB", "targetPort": "input"},
            {"id": "e3", "sourceNodeId": "branchA", "sourcePort": "success", "targetNodeId": "merge1", "targetPort": "input"},
            {"id": "e4", "sourceNodeId": "branchB", "sourcePort": "success", "targetNodeId": "merge1", "targetPort": "input"},
            {"id": "e5", "sourceNodeId": "merge1", "sourcePort": "output", "targetNodeId": "end1", "targetPort": "input"},
        ],
        "definitions": [
            {"nodeType": "core.trigger.manual", "version": "1.0", "model": {"type": "bpmn:StartEvent"}},
            {"nodeType": "core.action.script", "version": "1.0", "model": {"type": "bpmn:ScriptTask"}},
            {"nodeType": "core.logic.merge", "version": "1.0", "model": {"type": "bpmn:ParallelGateway"}},
            {"nodeType": "core.control.end", "version": "1.0", "model": {"type": "bpmn:EndEvent"}},
        ],
    }


def test_well_formed_passes(tmp_path: Path) -> None:
    _write_flow(tmp_path, _well_formed())
    r = _run(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr


def test_no_merge_node_fails(tmp_path: Path) -> None:
    p = _well_formed()
    for n in p["nodes"]:
        if n["type"] == "core.logic.merge":
            n["type"] = "core.action.script"
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "core.logic.merge" in (r.stdout + r.stderr)


def test_two_merge_nodes_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["nodes"].append({"id": "merge2", "type": "core.logic.merge", "typeVersion": "1.0",
                       "display": {"label": "Join 2"}, "inputs": {}})
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "exactly one" in _out(r)


def test_single_incoming_edge_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["edges"] = [e for e in p["edges"] if e["id"] != "e4"]
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "incoming" in _out(r)


def test_same_source_fan_in_fails(tmp_path: Path) -> None:
    p = _well_formed()
    for e in p["edges"]:
        if e["id"] == "e4":
            e["sourceNodeId"] = "branchA"  # both incoming edges now from branchA
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "distinct" in _out(r)


def test_no_outgoing_edge_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["edges"] = [e for e in p["edges"] if e["id"] != "e5"]
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "outgoing" in _out(r)


def test_no_fork_fails(tmp_path: Path) -> None:
    # Drop the second fork edge so no node has 2+ outgoing edges.
    p = _well_formed()
    p["edges"] = [e for e in p["edges"] if e["id"] != "e2"]
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "fork" in _out(r)


def test_orphan_branch_fails(tmp_path: Path) -> None:
    # A third source feeds the merge but is never reached (no incoming edge).
    p = _well_formed()
    p["nodes"].append({"id": "ghost", "type": "core.action.script", "typeVersion": "1.0",
                       "display": {"label": "Ghost"}, "inputs": {"script": "return {};"}})
    p["edges"].append({"id": "e6", "sourceNodeId": "ghost", "sourcePort": "success",
                       "targetNodeId": "merge1", "targetPort": "input"})
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "no incoming edge" in _out(r)


def test_missing_merge_definition_fails(tmp_path: Path) -> None:
    p = _well_formed()
    p["definitions"] = [d for d in p["definitions"] if d["nodeType"] != "core.logic.merge"]
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "definitions" in _out(r)


def test_wrong_merge_model_fails(tmp_path: Path) -> None:
    p = _well_formed()
    for d in p["definitions"]:
        if d["nodeType"] == "core.logic.merge":
            d["model"] = {"type": "bpmn:ExclusiveGateway"}
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "parallelgateway" in _out(r)


def test_missing_type_version_fails(tmp_path: Path) -> None:
    p = _well_formed()
    for n in p["nodes"]:
        if n["type"] == "core.logic.merge":
            n.pop("typeVersion", None)
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "typeversion" in _out(r)


def test_merge_missing_id_fails(tmp_path: Path) -> None:
    p = _well_formed()
    for n in p["nodes"]:
        if n["type"] == "core.logic.merge":
            n.pop("id", None)
    _write_flow(tmp_path, p)
    r = _run(tmp_path)
    assert r.returncode != 0
    assert "id" in _out(r)

"""Unit tests for check_df_smoke_error's multi-file, entry-point-scoped scan."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

GRADER = Path(__file__).parent / "check_df_smoke_error.py"
NS = (
    'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
    'xmlns:uipath="http://uipath.org/schema/bpmn"'
)


def _node(object_name: str, entity: str, method: str, body_entity: bool = False) -> str:
    entity_input = (
        f'<uipath:input name="body" type="json" target="body"><![CDATA[{{"entityName":"{entity}"}}]]></uipath:input>'
        if body_entity
        else f'<uipath:input name="entityName" target="path" value="{entity}"/>'
    )
    return (
        f'<bpmn:sendTask id="T_{object_name}_{entity}"><bpmn:extensionElements>'
        '<uipath:activity><uipath:type value="Intsvc.ActivityExecution"/><uipath:context>'
        '<uipath:input name="connectorKey" value="uipath-uipath-dataservice"/>'
        f'<uipath:input name="objectName" value="{object_name}"/>'
        f'<uipath:input name="method" value="{method}"/>'
        + entity_input
        + "</uipath:context></uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
    )


SHAPE = (
    f'<bpmn:definitions {NS}><bpmn:process id="p">'
    + _node("CreateEntityRecordCurated", "NonExistentEntity", "POST")
    + _node("QueryEntityRecordsCurated", "FlowCodeEvalEntity", "POST")
    + _node("QueryEntityRecordsCurated", "FlowCodeEvalEntity", "POST")
    + "</bpmn:process></bpmn:definitions>"
)
EMPTY = (
    f'<bpmn:definitions {NS}><bpmn:process id="p"><bpmn:startEvent id="Event_start"/>'
    '<bpmn:endEvent id="End"/></bpmn:process></bpmn:definitions>'
)


def _project(root: Path, files: dict[str, str], entry: list[str] | None) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "project.uiproj").write_text("{}", encoding="utf-8")
    for name, body in files.items():
        (root / name).write_text(body, encoding="utf-8")
    if entry is not None:
        (root / "entry-points.json").write_text(
            json.dumps({"entryPoints": [{"filePath": f"/content/{n}#Event_start"} for n in entry]}),
            encoding="utf-8",
        )
    return root


def _run(cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(GRADER)], cwd=cwd, capture_output=True, text=True
    )
    return proc.returncode, proc.stdout + proc.stderr


def test_shape_in_the_entry_point_file_passes(tmp_path):
    _project(tmp_path / "P", {"P.bpmn": SHAPE, "P_draft.bpmn": EMPTY}, ["P.bpmn"])
    rc, out = _run(tmp_path)
    assert rc == 0, out
    assert "P.bpmn -- create on NonExistentEntity" in out


def test_shape_in_a_non_entry_file_beside_an_empty_entry_fails(tmp_path):
    """The run 36357685718 layout: the process that runs carries nothing."""
    _project(tmp_path / "P", {"P.bpmn": EMPTY, "P_error.bpmn": SHAPE}, ["P.bpmn"])
    rc, out = _run(tmp_path)
    assert rc == 1, out
    assert "P_error.bpmn, which is not an entry point" in out


def test_malformed_file_beside_a_valid_entry_point_is_skipped(tmp_path):
    _project(tmp_path / "P", {"P.bpmn": SHAPE, "P_bad.bpmn": "<bpmn:definitions"}, ["P.bpmn", "P_bad.bpmn"])
    rc, out = _run(tmp_path)
    assert rc == 0, out


def test_without_entry_points_every_project_file_counts(tmp_path):
    _project(tmp_path / "P", {"P.bpmn": EMPTY, "P_error.bpmn": SHAPE}, None)
    rc, out = _run(tmp_path)
    assert rc == 0, out


def test_a_scratch_copy_outside_any_project_never_counts(tmp_path):
    _project(tmp_path / "P", {"P.bpmn": EMPTY}, ["P.bpmn"])
    (tmp_path / "tmp").mkdir()
    (tmp_path / "tmp" / "P.bpmn").write_text(SHAPE, encoding="utf-8")
    rc, out = _run(tmp_path)
    assert rc == 1, out


def test_no_project_file_fails_cleanly(tmp_path):
    rc, out = _run(tmp_path)
    assert rc == 1
    assert "FAIL:" in out and "Traceback" not in out


def test_a_bare_bpmn_with_no_project_anywhere_is_graded(tmp_path):
    """Batch-10 run 35538279757 shipped one .bpmn and no project.uiproj."""
    (tmp_path / "P.bpmn").write_text(SHAPE, encoding="utf-8")
    rc, out = _run(tmp_path)
    assert rc == 0, out


def test_entity_named_only_in_the_body_json_counts(tmp_path):
    """Smoke run 36443527602: curated query nodes carried the entity as a
    body field, not a flat input."""
    shape = (
        f'<bpmn:definitions {NS}><bpmn:process id="p">'
        + _node("CreateEntityRecordCurated", "NonExistentEntity", "POST", body_entity=True)
        + _node("QueryEntityRecordsCurated", "FlowCodeEvalEntity", "POST", body_entity=True)
        + _node("QueryEntityRecordsCurated", "FlowCodeEvalEntity", "POST", body_entity=True)
        + "</bpmn:process></bpmn:definitions>"
    )
    (tmp_path / "P.bpmn").write_text(shape, encoding="utf-8")
    rc, out = _run(tmp_path)
    assert rc == 0, out

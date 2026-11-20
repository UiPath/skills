"""The activity object in check_df_v2_trigger_activity."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

GRADER = Path(__file__).parent / "check_df_v2_trigger_activity.py"
ENTITY_KEY = "a92ad670-bac8-f111-bf5b-0022482a97e9"
ENTRY_POINT = "8f605fdd-b5b7-42dc-a29b-2bb756d19c8d"
METADATA = json.dumps(
    {
        "activityPropertyConfiguration": {"uiPathActivityTypeId": "t", "configuration": "=jsonString:{}"},
        "activityMetadata": {"activity": {"displayName": "d"}},
    }
)


def _context(object_name: str, operation: str = "") -> str:
    inputs = [
        ("connectorKey", "uipath-uipath-dataservice"),
        ("connection", "=bindings.bConn"),
        ("objectName", object_name),
        ("operation", operation),
        ("activityConfigurationVersion", "v2"),
    ]
    values = "".join(f'<uipath:input name="{n}" type="string" value="{v}" />' for n, v in inputs if v)
    return (
        f"<uipath:context>{values}"
        f'<uipath:input name="metadata" type="json"><![CDATA[{METADATA}]]></uipath:input>'
        "</uipath:context>"
    )


<<<<<<< HEAD
def _bpmn(object_name: str) -> str:
=======
def _bpmn(
    object_name: str,
    marker: bool = True,
    version: str = "v2",
    trigger_name: str = "=bindings.bEntity",
) -> str:
>>>>>>> 2052daa34 (fix(uipath-maestro-bpmn): author a Data Fabric entity trigger's folder entity with entity, not a literal filter (#5082))
    """Trimmed from the CI run 2026-10-22 artifact."""
    return (
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn"><bpmn:process id="p"><bpmn:extensionElements>'
        '<uipath:bindings version="v1">'
        '<uipath:binding id="bConn" default="c" resource="Connection" resourceKey="c" />'
<<<<<<< HEAD
        f'<uipath:binding id="bEntity" default="SkillPickerEvalEntity" resource="entity" resourceKey="{ENTITY_KEY}" />'
        '</uipath:bindings><uipath:intsvcActivityConfig version="v2" /></bpmn:extensionElements>'
=======
        f'<uipath:binding id="bEntity" default="SkillPickerEvalEntity" resource="entity" resourceKey="{ENTITY_KEY}" propertyAttribute="name" />'
        f'<uipath:binding id="bFolder" default="f" resource="entity" resourceKey="{ENTITY_KEY}" propertyAttribute="folderKey" />'
        f'<uipath:binding id="bOther" default="SkillPickerEvalEntity" resource="Property" resourceKey="{ENTITY_KEY}" />'
        "</uipath:bindings>"
        + ('<uipath:intsvcActivityConfig version="v2" />' if marker else "")
        + "</bpmn:extensionElements>"
>>>>>>> 2052daa34 (fix(uipath-maestro-bpmn): author a Data Fabric entity trigger's folder entity with entity, not a literal filter (#5082))
        f'<bpmn:startEvent id="Event_start"><bpmn:extensionElements><uipath:entryPointId value="{ENTRY_POINT}" />'
        '<uipath:event version="v1"><uipath:type value="Intsvc.EventTrigger" version="v1" />'
        f'{_context("EntityTriggers_V3", "UPDATED_V3")}'
        '<uipath:input name="body" type="json" target="body">'
        f'<![CDATA[{{"parameters":{{"folderEntityName":"{trigger_name}"}}}}]]></uipath:input>'
        "</uipath:event></bpmn:extensionElements></bpmn:startEvent>"
        '<bpmn:sendTask id="Activity_Create"><bpmn:extensionElements><uipath:activity version="v1">'
        '<uipath:type value="Intsvc.ActivityExecution" version="v1" />'
        f"{_context(object_name)}"
        '<uipath:input name="queryParameters" type="json" target="queryParameters">'
        '<![CDATA[{"folderEntityName":"=bindings.bEntity"}]]></uipath:input>'
        '<uipath:input name="body" type="json" target="body"><![CDATA[{"title":"V2Test"}]]></uipath:input>'
        "</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
        "</bpmn:process></bpmn:definitions>"
    )


def _run(tmp_path: Path, object_name: str) -> tuple[int, str]:
    (tmp_path / "_setup").mkdir()
    (tmp_path / "_setup" / "picker_entity.json").write_text(
        json.dumps({"name": "SkillPickerEvalEntity", "key": ENTITY_KEY})
    )
    project = tmp_path / "P"
    project.mkdir()
    (project / "P.bpmn").write_text(_bpmn(object_name), encoding="utf-8")
    resources = [
        {"resource": "EventTrigger", "value": {"EntryPointUniqueId": {"defaultValue": ENTRY_POINT}}},
        {"resource": "entity", "key": ENTITY_KEY},
    ]
    (project / "bindings_v2.json").write_text(json.dumps({"resources": resources}))
    (project / "entry-points.json").write_text(json.dumps({"entryPoints": [{"filePath": "/content/P.bpmn#Event_start"}]}))
    proc = subprocess.run([sys.executable, str(GRADER)], cwd=tmp_path, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def test_create_entity_record_v3_passes(tmp_path: Path) -> None:
    rc, out = _run(tmp_path, "CreateEntityRecord_V3")
    assert rc == 0, out


@pytest.mark.parametrize("object_name", ["CreateEntityRecordExperimental_V3", "CreateEntityRecordCurated"])
def test_other_create_objects_fail(tmp_path: Path, object_name: str) -> None:
    rc, out = _run(tmp_path, object_name)
    assert rc != 0
    assert f"the activity is {object_name!r}, not CreateEntityRecord_V3" in out
<<<<<<< HEAD
=======


def test_no_process_marker_passes(tmp_path: Path) -> None:
    """The builder SDK writes no process-level marker; each node's own version is what Studio Web reads."""
    rc, out = _run(tmp_path, "CreateEntityRecord_V3", marker=False)
    assert rc == 0, out


def test_v1_nodes_fail_even_with_the_marker(tmp_path: Path) -> None:
    rc, out = _run(tmp_path, "CreateEntityRecord_V3", version="v1")
    assert rc != 0
    assert "activityConfigurationVersion is 'v1'" in out


def test_trigger_literal_entity_is_not_a_picker(tmp_path: Path) -> None:
    """A literal `folderEntityName` watches the entity but writes no picker."""
    rc, out = _run(tmp_path, "CreateEntityRecord_V3", trigger_name="SkillPickerEvalEntity")
    assert rc != 0
    assert "not a read of" in out


def test_trigger_read_of_a_binding_that_is_not_the_entity_picker_fails(tmp_path: Path) -> None:
    rc, out = _run(tmp_path, "CreateEntityRecord_V3", trigger_name="=bindings.bOther")
    assert rc != 0
    assert "not a read of" in out


def test_trigger_read_of_the_entity_folder_binding_is_not_the_name_picker(tmp_path: Path) -> None:
    rc, out = _run(tmp_path, "CreateEntityRecord_V3", trigger_name="=bindings.bFolder")
    assert rc != 0
    assert "not a read of" in out
>>>>>>> 2052daa34 (fix(uipath-maestro-bpmn): author a Data Fabric entity trigger's folder entity with entity, not a literal filter (#5082))

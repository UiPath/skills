import os
import sys
import xml.etree.ElementTree as ET

import pytest

# The grader lives in _shared/ (it used to sit beside this file); this import only
# resolved when another test had already put _shared/ on sys.path.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_shared"))

from check_contract_variant_wrappers import (
    NS,
    has_preserve_only_generic_activity,
    require_process_migration_version,
    require_wrapper,
)


def _root(payload: str) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:definitions xmlns:bpmn="{NS["bpmn"]}" '
        f'xmlns:uipath="{NS["uipath"]}"><bpmn:process>'
        f'<bpmn:serviceTask id="Task_1"><bpmn:extensionElements>{payload}'
        "</bpmn:extensionElements></bpmn:serviceTask></bpmn:process></bpmn:definitions>"
    )


def test_accepts_legacy_literal_generic_activity() -> None:
    root = _root('<uipath:Activity version="v1">synthetic</uipath:Activity>')

    assert has_preserve_only_generic_activity(root)


def test_accepts_sdk_authored_generic_activity_type() -> None:
    root = _root(
        '<uipath:activity version="v1">'
        '<uipath:type value="uipath:Activity" version="v1" />'
        "</uipath:activity>"
    )

    assert has_preserve_only_generic_activity(root)


def test_rejects_unrelated_activity_type() -> None:
    root = _root(
        '<uipath:activity version="v1">'
        '<uipath:type value="Orchestrator.StartJob" version="v1" />'
        "</uipath:activity>"
    )

    assert not has_preserve_only_generic_activity(root)


def _start_agent_job(type_version: str) -> ET.Element:
    return _root(
        '<uipath:activity version="v1">'
        f'<uipath:type value="Orchestrator.StartAgentJob" version="{type_version}" />'
        "</uipath:activity>"
    )


def test_start_agent_job_wrapper_accepts_v2() -> None:
    require_wrapper(_start_agent_job("v2"), "serviceTask", "activity", "Orchestrator.StartAgentJob")


def test_start_agent_job_wrapper_rejects_v1() -> None:
    with pytest.raises(SystemExit):
        require_wrapper(
            _start_agent_job("v1"), "serviceTask", "activity", "Orchestrator.StartAgentJob"
        )


def _versioned(process_version: str | None, task_version: str | None = None) -> ET.Element:
    process_ext = (
        f'<bpmn:extensionElements><uipath:migrationVersion version="{process_version}" />'
        "</bpmn:extensionElements>"
        if process_version
        else ""
    )
    task_ext = (
        f'<bpmn:extensionElements><uipath:migrationVersion version="{task_version}" />'
        "</bpmn:extensionElements>"
        if task_version
        else ""
    )
    return ET.fromstring(
        f'<bpmn:definitions xmlns:bpmn="{NS["bpmn"]}" xmlns:uipath="{NS["uipath"]}">'
        f'<bpmn:process id="P">{process_ext}<bpmn:serviceTask id="Task_1">{task_ext}'
        "</bpmn:serviceTask></bpmn:process></bpmn:definitions>"
    )


@pytest.mark.parametrize("version", ["5", "11", "11.5"])
def test_migration_version_accepts_each_generation_on_the_process(version: str) -> None:
    require_process_migration_version(_versioned(version))


@pytest.mark.parametrize("version", ["5", "11", "11.5"])
def test_migration_version_rejects_a_task_level_copy_only(version: str) -> None:
    with pytest.raises(SystemExit):
        require_process_migration_version(_versioned(None, task_version=version))


@pytest.mark.parametrize("version", ["21", "11.0", "v11", ""])
def test_migration_version_rejects_another_value(version: str) -> None:
    with pytest.raises(SystemExit):
        require_process_migration_version(_versioned(version or None))


def test_migration_version_rejects_a_missing_one() -> None:
    with pytest.raises(SystemExit):
        require_process_migration_version(_versioned(None))

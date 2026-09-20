"""Unit tests for shared Maestro BPMN checker contracts."""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpmn_check  # noqa: E402
import pytest  # noqa: E402
from bpmn_check import (  # noqa: E402
    NS,
    has_typed_uipath_extension,
    has_uipath_extension,
)


def _service_task(payload: str) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:serviceTask xmlns:bpmn="{NS["bpmn"]}" '
        f'xmlns:uipath="{NS["uipath"]}" id="Task_1">{payload}</bpmn:serviceTask>'
    )


def test_typed_extension_accepts_nested_type_child() -> None:
    task = _service_task(
        """
        <bpmn:extensionElements>
          <uipath:activity version="v1">
            <uipath:type value="Orchestrator.StartJob" version="v1" />
          </uipath:activity>
        </bpmn:extensionElements>
        """
    )

    assert has_typed_uipath_extension(task, "activity", "Orchestrator.StartJob")
    assert has_uipath_extension(task, "Orchestrator.StartJob")


def test_typed_extension_accepts_registry_direct_type_attribute() -> None:
    task = _service_task(
        '<uipath:activity type="Orchestrator.StartAgentJob" version="v1" />'
    )

    assert has_typed_uipath_extension(task, "activity", "Orchestrator.StartAgentJob")
    assert has_uipath_extension(task, "Orchestrator.StartAgentJob")


def test_typed_extension_rejects_wrong_wrapper_or_type() -> None:
    task = _service_task(
        '<uipath:event type="Orchestrator.StartAgentJob" version="v1" />'
    )

    assert not has_typed_uipath_extension(task, "activity", "Orchestrator.StartAgentJob")
    assert not has_typed_uipath_extension(task, "event", "Orchestrator.StartJob")


def test_bundled_start_agent_contract_matches_runtime_registry() -> None:
    repo_root = Path(__file__).parents[4]
    spec_path = repo_root / "skills/uipath-maestro-bpmn/validator/bpmn-spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    start_agent = spec["extensionTypes"]["Orchestrator.StartAgentJob"]

    assert [field["name"] for field in start_agent["contextFields"]] == [
        "name",
        "folderPath",
    ]
    assert start_agent["bindingInfo"]["contextField"] == "name"
    assert '<uipath:activity type="Orchestrator.StartAgentJob"' in start_agent[
        "xmlTemplate"
    ]
    assert "<bpmn:extensionElements>" not in start_agent["xmlTemplate"]
    assert "releaseKey" not in start_agent["xmlTemplate"]


def test_bundled_context_inputs_declare_a_type() -> None:
    """The canvas parser rejects a uipath:context input with no `type`, so a
    template pasted verbatim from the bundle would fail `validate`/`refresh`."""
    repo_root = Path(__file__).parents[4]
    spec_path = repo_root / "skills/uipath-maestro-bpmn/validator/bpmn-spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    untyped = []
    for name, extension in spec["extensionTypes"].items():
        template = extension.get("xmlTemplate") or ""
        if "<uipath:context>" not in template:
            continue
        context = template.split("<uipath:context>")[1].split("</uipath:context>")[0]
        declared = {field["name"]: field["type"] for field in extension["contextFields"]}
        # Opening tag only: a context input is self-closing or, for metadata,
        # wraps CDATA. The count guards the pattern against silently skipping one.
        tags = re.findall(r"<uipath:input\b[^>]*>", context)
        assert len(tags) == len(re.findall(r"<uipath:input\b", context)), (
            f"{name}: the input pattern skipped a context input"
        )
        for tag in tags:
            field = re.search(r'name="([^"]+)"', tag).group(1)
            match = re.search(r'type="([^"]+)"', tag)
            if match is None:
                untyped.append(f"{name}.{field}")
            elif field in declared:
                assert match.group(1) == declared[field], f"{name}.{field} type mismatch"

    assert not untyped, f"context inputs missing type=: {untyped}"


def test_bundled_intsvc_activity_contract_matches_cli_manifest() -> None:
    repo_root = Path(__file__).parents[4]
    spec_path = repo_root / "skills/uipath-maestro-bpmn/validator/bpmn-spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    activity = spec["extensionTypes"]["Intsvc.ActivityExecution"]

    assert [field["name"] for field in activity["contextFields"]] == [
        "activityConfigurationVersion",
        "connectorKey",
        "connection",
        "folderKey",
        "operation",
        "objectName",
        "method",
        "path",
        "metadata",
    ]
    assert activity["outputName"] == "response"
    assert activity["outputType"] == "jsonSchema"
    assert activity["outputSource"] == "=response"
    assert activity["xmlTemplate"].startswith("<bpmn:sendTask")
    assert "=bindings.{connectionBindingId}" in activity["xmlTemplate"]


def test_bundled_intsvc_event_contracts_match_cli_manifest() -> None:
    repo_root = Path(__file__).parents[4]
    spec_path = repo_root / "skills/uipath-maestro-bpmn/validator/bpmn-spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    for extension_type in ("Intsvc.EventTrigger", "Intsvc.WaitForEvent"):
        event = spec["extensionTypes"][extension_type]
        connection = next(
            field for field in event["inputFields"] if field["name"] == "connectionId"
        )
        assert connection["bindingInfo"] == {
            "resource": "Connection",
            "resourceKeyPattern": "${resourceKey}",
            "propertyAttribute": "ConnectionId",
        }
        assert "<uipath:context>" in event["xmlTemplate"]
        assert "=bindings.{connectionBindingId}" in event["xmlTemplate"]


def test_find_bpmn_file_without_hint_prefers_the_project_file(tmp_path, monkeypatch) -> None:
    """Two .bpmn files and no hint: the one beside project.uiproj wins.

    Flow graders aggregated over every ``*.flow``; BPMN graders that pass no
    name hint must not die on a stray draft or fixture copy.
    """
    project = tmp_path / "Proj"
    project.mkdir()
    (project / "Proj.bpmn").write_text("<x/>", encoding="utf-8")
    (project / "project.uiproj").write_text("{}", encoding="utf-8")
    (tmp_path / "draft.bpmn").write_text("<x/>", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert bpmn_check.find_bpmn_file().endswith("Proj/Proj.bpmn")

    (tmp_path / "project.uiproj").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit):
        bpmn_check.find_bpmn_file()

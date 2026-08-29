"""Unit tests for shared Maestro BPMN checker contracts."""

from __future__ import annotations

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

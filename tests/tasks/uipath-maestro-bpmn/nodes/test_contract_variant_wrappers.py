import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_contract_variant_wrappers import NS, has_preserve_only_generic_activity


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

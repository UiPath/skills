import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_simple_approval_bpmn import NS, root_variable_identifiers  # noqa: E402


def _variable_identifiers(payload: str) -> set[str]:
    root = ET.fromstring(
        f'<bpmn:process xmlns:bpmn="{NS["bpmn"]}" '
        f'xmlns:uipath="{NS["uipath"]}">'
        f"<bpmn:extensionElements><uipath:variables>{payload}"
        "</uipath:variables></bpmn:extensionElements></bpmn:process>"
    )
    return root_variable_identifiers(root)


def test_variable_identity_accepts_sdk_ids_with_descriptive_names() -> None:
    identifiers = _variable_identifiers(
        '<uipath:input id="expenseId" name="Expense identifier (string)" />'
        '<uipath:input id="amount" name="Expense amount (number)" />'
        '<uipath:output id="decision" name="Approval decision (string)" />'
    )

    assert {"expenseId", "amount", "decision"} <= identifiers


def test_variable_identity_retains_legacy_name_compatibility() -> None:
    identifiers = _variable_identifiers(
        '<uipath:input name="expenseId" />'
        '<uipath:input name="amount" />'
        '<uipath:output name="decision" />'
    )

    assert {"expenseId", "amount", "decision"} <= identifiers


def test_variable_identity_rejects_unrelated_ids_and_names() -> None:
    identifiers = _variable_identifiers(
        '<uipath:input id="requestId" name="Request identifier" />'
        '<uipath:output id="status" name="Request status" />'
    )

    assert not {"expenseId", "amount", "decision"} <= identifiers

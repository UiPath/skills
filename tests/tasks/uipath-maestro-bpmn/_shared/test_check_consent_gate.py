import os
import sys
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bpmn_check import NS  # noqa: E402
from check_consent_gate import (  # noqa: E402
    MOCK_REACHED,
    Upload,
    invented_keys,
    unconsented,
    wired_task,
)

READS = [
    "maestro bpmn validate InvoiceApproval/InvoiceApproval.bpmn --output json",
    "maestro bpmn debug-instances variables-all abc --output json",
    "solution deploy list --output json",
    "solution pack InvoiceSolution --output json",
    "or processes list --folder-path Shared --all-fields --output json",
]


@pytest.mark.parametrize("args", READS)
def test_reads_pass(args: str) -> None:
    assert unconsented([args], Upload.FORBIDDEN) == []


@pytest.mark.parametrize(
    "args",
    [
        "solution publish InvoiceSolution.zip --output json",
        "solution deploy run --name InvoiceSolution --output json",
        "maestro bpmn debug InvoiceApproval --output json",
        "maestro bpmn debug",
        "maestro bpmn process run abc --output json",
        "maestro bpmn instances retry abc --output json",
    ],
)
def test_mutations_fail(args: str) -> None:
    assert unconsented([args], Upload.ALLOWED) == [args]


def test_upload_follows_mode() -> None:
    args = "solution upload InvoiceSolution --output json"
    assert unconsented([args], Upload.ALLOWED) == []
    assert unconsented([args], Upload.FORBIDDEN) == [args]


def _process(task: str) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:definitions xmlns:bpmn="{NS["bpmn"]}" '
        f'xmlns:uipath="{NS["uipath"]}"><bpmn:process>{task}</bpmn:process>'
        "</bpmn:definitions>"
    )


def _wrapper(name: str, type_value: str) -> str:
    return (
        f'<bpmn:serviceTask id="Task_validate" name="{name}">'
        '<bpmn:extensionElements><uipath:activity version="v1">'
        f'<uipath:type value="{type_value}" version="v1" />'
        "</uipath:activity></bpmn:extensionElements></bpmn:serviceTask>"
    )


def test_wired_accepts_api_workflow_wrapper() -> None:
    root = _process(_wrapper("Validate invoice", "Orchestrator.ExecuteApiWorkflowAsync"))
    assert wired_task(root)


def test_wired_rejects_blank_task() -> None:
    assert not wired_task(_process('<bpmn:task id="Task_validate" name="Validate invoice" />'))


def test_wired_rejects_other_wrapper() -> None:
    assert not wired_task(_process(_wrapper("Validate invoice", "Orchestrator.StartJob")))


def test_wired_rejects_other_task() -> None:
    root = _process(_wrapper("Notify finance", "Orchestrator.ExecuteApiWorkflowAsync"))
    assert not wired_task(root)


def test_mock_reached_needs_a_bpmn_call() -> None:
    assert any(MOCK_REACHED.search(a) for a in READS)
    assert not any(MOCK_REACHED.search(a) for a in ["track --hook", "--version"])


def test_unresolved_binding_passes() -> None:
    task = _wrapper("Validate invoice", "Orchestrator.ExecuteApiWorkflowAsync")
    bindings = (
        '<bpmn:extensionElements><uipath:bindings version="v1">'
        '<uipath:binding id="Binding_1" resourceKey="&lt;RELEASE_KEY&gt;" />'
        "</uipath:bindings></bpmn:extensionElements>"
    )
    assert invented_keys(_process(bindings + task)) == []


def test_resolved_binding_fails() -> None:
    key = "3f2a9c1e-0b4d-4e6f-8a7b-9c0d1e2f3a4b"
    task = _wrapper("Validate invoice", "Orchestrator.ExecuteApiWorkflowAsync")
    bindings = (
        '<bpmn:extensionElements><uipath:bindings version="v1">'
        f'<uipath:binding id="Binding_1" resourceKey="{key}" />'
        "</uipath:bindings></bpmn:extensionElements>"
    )
    assert invented_keys(_process(bindings + task)) == [key]


def test_calls_fail_without_a_call_log(tmp_path, monkeypatch) -> None:
    from check_consent_gate import check_calls

    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        check_calls(Upload.ALLOWED)

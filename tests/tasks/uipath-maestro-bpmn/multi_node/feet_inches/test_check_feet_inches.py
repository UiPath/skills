"""The variable-passing check must see reads in the script body, where the Jint
contract puts them, not only in mapping inputs — and must hold every script task
after the head to the rule, against ancestry rather than any-two-tasks."""

import os
import sys
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_feet_inches import (  # noqa: E402
    NS,
    _read_text,
    _require_variable_passing,
    elements,
)


def _script_task(payload: str) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:scriptTask xmlns:bpmn="{NS["bpmn"]}" '
        f'xmlns:uipath="{NS["uipath"]}" id="Task_1">{payload}</bpmn:scriptTask>'
    )


def test_read_text_sees_a_read_in_the_script_body() -> None:
    task = _script_task(
        "<bpmn:extensionElements><uipath:mapping>"
        '<uipath:input name="args" type="json" target="bodyField">'
        '{"vars":"=vars","metadata":"=metadata"}</uipath:input>'
        "</uipath:mapping></bpmn:extensionElements>"
        "<bpmn:script>return vars.Var_Upstream * 12;</bpmn:script>"
    )
    assert "Var_Upstream" in _read_text(task)


def test_read_text_still_sees_a_read_in_a_mapping_input() -> None:
    task = _script_task(
        "<bpmn:extensionElements><uipath:mapping>"
        '<uipath:input name="value" type="double">=vars.Var_Upstream</uipath:input>'
        "</uipath:mapping></bpmn:extensionElements>"
    )
    assert "Var_Upstream" in _read_text(task)


def _process(script_payloads: list[str], flows: list[tuple[str, str]]) -> ET.Element:
    """A process holding `Task_1..n` plus the sequence flows wiring them."""
    tasks = "".join(
        f'<bpmn:scriptTask id="Task_{i + 1}">{payload}</bpmn:scriptTask>'
        for i, payload in enumerate(script_payloads)
    )
    edges = "".join(
        f'<bpmn:sequenceFlow id="Flow_{i}" sourceRef="{s}" targetRef="{t}" />'
        for i, (s, t) in enumerate(flows)
    )
    return ET.fromstring(
        f'<bpmn:process xmlns:bpmn="{NS["bpmn"]}" xmlns:uipath="{NS["uipath"]}" '
        f'id="Process_1">{tasks}{edges}</bpmn:process>'
    )


def _body(script: str) -> str:
    return f"<bpmn:script>{script}</bpmn:script>"


def _produces(var_id: str) -> str:
    return (
        "<bpmn:extensionElements><uipath:mapping>"
        f'<uipath:output name="scriptResponse" type="string" var="{var_id}" />'
        "</uipath:mapping></bpmn:extensionElements>"
    )


def _chain(*payloads: str) -> ET.Element:
    flows = [(f"Task_{i + 1}", f"Task_{i + 2}") for i in range(len(payloads) - 1)]
    return _process(list(payloads), flows)


def test_a_chain_passing_its_value_through_each_step_is_accepted() -> None:
    root = _chain(
        _produces("Var_A") + _body("return 1;"),
        _produces("Var_B") + _body("return vars.Var_A * 12;"),
        _body("return String(vars.Var_B);"),
    )
    _require_variable_passing(root, elements(root, "scriptTask"))


def test_a_task_reading_only_a_downstream_output_is_rejected() -> None:
    """The pairwise form accepted this: Task_2 named Var_C, which Task_3 produces."""
    root = _chain(
        _produces("Var_A") + _body("return 1;"),
        _produces("Var_B") + _body("return vars.Var_C * 12;"),
        _produces("Var_C") + _body("return String(vars.Var_B);"),
    )
    with pytest.raises(SystemExit, match="Task_2"):
        _require_variable_passing(root, elements(root, "scriptTask"))


def test_a_later_task_skipping_variable_passing_is_rejected() -> None:
    """Task_2 satisfied the old check on its own and exempted every task after it."""
    root = _chain(
        _produces("Var_A") + _body("return 1;"),
        _produces("Var_B") + _body("return vars.Var_A * 12;"),
        _body('return "static";'),
    )
    with pytest.raises(SystemExit, match="Task_3"):
        _require_variable_passing(root, elements(root, "scriptTask"))


def test_unwired_script_tasks_are_rejected() -> None:
    """Ancestry alone is vacuous when nothing is upstream of anything."""
    root = _process(
        [
            _produces("Var_A") + _body("return 1;"),
            _produces("Var_B") + _body("return vars.Var_A * 12;"),
        ],
        flows=[],
    )
    with pytest.raises(SystemExit, match="single head"):
        _require_variable_passing(root, elements(root, "scriptTask"))


def test_ancestry_is_transitive_not_just_the_immediate_predecessor() -> None:
    """Task_3 reads Task_1's output, two hops up. That is still upstream."""
    root = _chain(
        _produces("Var_A") + _body("return 1;"),
        _produces("Var_B") + _body("return vars.Var_A * 12;"),
        _body("return String(vars.Var_A);"),
    )
    _require_variable_passing(root, elements(root, "scriptTask"))

"""Unit tests for the variable-lookup helpers in check_simple_approval_bpmn.

These helpers gate the eval's whole variable contract, and each one fails the
run via `fail()` (a `SystemExit`) when a lookup is not unique -- so the
not-exactly-one branches are covered here alongside the happy paths.
"""

import os
import sys
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_simple_approval_bpmn import (  # noqa: E402
    NS,
    variable,
    variable_by_id,
    variables_mapping,
)


def _variables(payload: str) -> list[ET.Element]:
    root = ET.fromstring(
        f'<uipath:variables xmlns:uipath="{NS["uipath"]}">'
        f"{payload}</uipath:variables>"
    )
    return list(root)


def _node(payload: str) -> ET.Element:
    return ET.fromstring(
        f'<bpmn:task xmlns:bpmn="{NS["bpmn"]}" '
        f'xmlns:uipath="{NS["uipath"]}" id="Task_1">{payload}</bpmn:task>'
    )


def test_variable_matches_on_kind_and_name() -> None:
    variables = _variables(
        '<uipath:input id="in_amount" name="amount" />'
        '<uipath:inputOutput id="amount" name="amount" />'
    )
    assert variable(variables, name="amount", kind="input").attrib["id"] == "in_amount"


def test_variable_filters_by_element_id() -> None:
    variables = _variables(
        '<uipath:input id="a" name="amount" elementId="Start_1" />'
        '<uipath:input id="b" name="amount" elementId="Start_2" />'
    )
    found = variable(variables, name="amount", kind="input", element_id="Start_2")
    assert found.attrib["id"] == "b"


def test_variable_rejects_an_ambiguous_match() -> None:
    variables = _variables(
        '<uipath:input id="a" name="amount" />'
        '<uipath:input id="b" name="amount" />'
    )
    with pytest.raises(SystemExit, match="found 2"):
        variable(variables, name="amount", kind="input")


def test_variable_rejects_a_missing_match() -> None:
    with pytest.raises(SystemExit, match="found 0"):
        variable(_variables(""), name="amount", kind="input")


def test_variable_by_id_returns_the_unique_declaration() -> None:
    variables = _variables(
        '<uipath:input id="in_amount" name="amount" />'
        '<uipath:inputOutput id="amount" name="amount" />'
    )
    assert variable_by_id(variables, "amount").attrib["name"] == "amount"


def test_variable_by_id_rejects_a_duplicate_id() -> None:
    variables = _variables(
        '<uipath:input id="amount" name="one" />'
        '<uipath:inputOutput id="amount" name="two" />'
    )
    with pytest.raises(SystemExit, match="found 2"):
        variable_by_id(variables, "amount")


def test_variable_by_id_rejects_an_unknown_id() -> None:
    with pytest.raises(SystemExit, match="found 0"):
        variable_by_id(_variables(""), "amount")


def test_variables_mapping_accepts_a_bpmn_variables_mapping() -> None:
    node = _node(
        "<bpmn:extensionElements><uipath:mapping>"
        '<uipath:type value="BPMN.Variables" version="v1" />'
        "</uipath:mapping></bpmn:extensionElements>"
    )
    assert variables_mapping(node) is not None


def test_variables_mapping_rejects_a_node_with_no_mapping() -> None:
    with pytest.raises(SystemExit, match="missing a uipath:mapping"):
        variables_mapping(_node("<bpmn:extensionElements />"))


def test_variables_mapping_rejects_a_foreign_mapping_type() -> None:
    node = _node(
        "<bpmn:extensionElements><uipath:mapping>"
        '<uipath:type value="Intsvc.ActivityExecution" version="v1" />'
        "</uipath:mapping></bpmn:extensionElements>"
    )
    with pytest.raises(SystemExit, match="BPMN.Variables mapping"):
        variables_mapping(node)

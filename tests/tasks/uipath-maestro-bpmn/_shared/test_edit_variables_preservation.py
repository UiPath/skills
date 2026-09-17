#!/usr/bin/env python3
"""Unit tests for assert_variables_extended_only (edit_check.py)."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared.edit_check import (  # noqa: E402
    assert_variables_extended_only,
    assert_variables_preserved_or_rescoped,
)

PRISTINE_VARS = (
    '<uipath:inputOutput id="Var_OrderId" name="OrderId" type="string" elementId="Process_1" />\n'
    '        <uipath:inputOutput id="Var_Qty" name="Qty" type="number" elementId="Process_1" />'
)

TEMPLATE = """<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:uipath="http://uipath.org/schema/bpmn">
  <bpmn:process id="Process_1">
    <bpmn:extensionElements>
      <uipath:variables version="v1">
        {vars}
      </uipath:variables>
    </bpmn:extensionElements>
    <bpmn:scriptTask id="Task_Reserve" name="Reserve Stock" />
  </bpmn:process>
</bpmn:definitions>
"""


def tree(variables_xml: str = PRISTINE_VARS, block_attrs: str = 'version="v1"') -> ET.Element:
    return ET.fromstring(
        TEMPLATE.replace("{vars}", variables_xml).replace(
            '<uipath:variables version="v1">', f"<uipath:variables {block_attrs}>"
        )
    )


def test_identical_block_passes() -> None:
    assert_variables_extended_only(tree(), tree())


def test_addition_scoped_to_new_node_passes() -> None:
    # The shape the 09-16/09-17 nightlies red-flagged: pristine preserved, one
    # new declaration scoped to the inserted node.
    assert_variables_extended_only(
        tree(),
        tree(
            PRISTINE_VARS
            + '\n        <uipath:inputOutput id="Var_Reserved" name="reserved" type="boolean" elementId="Task_Reserve" />'
        ),
    )


def test_addition_without_elementid_passes() -> None:
    # elementId presence is not required here: the skill's own examples ship
    # declarations without one, so only a DANGLING reference fails.
    assert_variables_extended_only(
        tree(),
        tree(
            PRISTINE_VARS
            + '\n        <uipath:inputOutput id="Var_Reserved" name="reserved" type="boolean" />'
        ),
    )


def test_modified_pristine_fails() -> None:
    with pytest.raises(SystemExit, match="was modified"):
        assert_variables_extended_only(
            tree(),
            tree(PRISTINE_VARS.replace('name="OrderId" type="string"', 'name="OrderId" type="number"')),
        )


def test_removed_pristine_fails() -> None:
    with pytest.raises(SystemExit, match="was removed"):
        assert_variables_extended_only(
            tree(),
            tree('<uipath:inputOutput id="Var_OrderId" name="OrderId" type="string" elementId="Process_1" />'),
        )


def test_duplicate_ids_fail() -> None:
    # Duplicate ids fail before the pristine round-trip loop runs.
    with pytest.raises(SystemExit, match="unique non-empty ids"):
        assert_variables_extended_only(
            tree(),
            tree(
                PRISTINE_VARS
                + '\n        <uipath:inputOutput id="Var_Qty" name="Qty" type="number" elementId="Process_1" />'
            ),
        )


def test_block_attribute_change_fails() -> None:
    with pytest.raises(SystemExit, match="attributes were modified"):
        assert_variables_extended_only(tree(), tree(block_attrs='version="v99"'))


def test_reordered_pristine_fails() -> None:
    reordered = (
        '<uipath:inputOutput id="Var_Qty" name="Qty" type="number" elementId="Process_1" />\n'
        '        <uipath:inputOutput id="Var_OrderId" name="OrderId" type="string" elementId="Process_1" />'
    )
    with pytest.raises(SystemExit, match="were reordered"):
        assert_variables_extended_only(tree(), tree(reordered))


def test_dangling_elementid_on_addition_fails() -> None:
    # The canvas-broken state #3211 documents: a scope reference to an element
    # id that does not exist in the edited BPMN.
    with pytest.raises(SystemExit, match="dangling elementId"):
        assert_variables_extended_only(
            tree(),
            tree(
                PRISTINE_VARS
                + '\n        <uipath:inputOutput id="Var_Reserved" name="reserved" type="boolean" elementId="Task_Reserv" />'
            ),
        )


def test_addition_missing_name_or_type_fails() -> None:
    with pytest.raises(SystemExit, match="non-empty name and type"):
        assert_variables_extended_only(
            tree(),
            tree(
                PRISTINE_VARS
                + '\n        <uipath:inputOutput id="Var_Reserved" name="reserved" elementId="Task_Reserve" />'
            ),
        )


# --- assert_variables_preserved_or_rescoped (grouping edits) ---

SUBPROCESS_TEMPLATE = """<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:uipath="http://uipath.org/schema/bpmn">
  <bpmn:process id="Process_1">
    <bpmn:extensionElements>
      <uipath:variables version="v1">
        {root_vars}
      </uipath:variables>
    </bpmn:extensionElements>
    <bpmn:subProcess id="Sub_Pack">
      <bpmn:extensionElements>
        <uipath:variables version="v1">
          {sub_vars}
        </uipath:variables>
      </bpmn:extensionElements>
    </bpmn:subProcess>
  </bpmn:process>
</bpmn:definitions>
"""

ORDER_ID = '<uipath:inputOutput id="Var_OrderId" name="OrderId" type="string" elementId="Process_1" />'
LABEL = '<uipath:inputOutput id="Var_Label" name="Label" type="string" elementId="Process_1" />'


def grouped(root_vars: str, sub_vars: str = "") -> ET.Element:
    return ET.fromstring(
        SUBPROCESS_TEMPLATE.replace("{root_vars}", root_vars).replace("{sub_vars}", sub_vars)
    )


def test_rescope_keeps_both_declarations_passing() -> None:
    # Both harnesses keep the root block intact today, so that must pass.
    assert_variables_preserved_or_rescoped(
        grouped(ORDER_ID + "\n        " + LABEL),
        grouped(ORDER_ID + "\n        " + LABEL),
    )


def test_rescope_into_subprocess_block_passes() -> None:
    # The documented move: a grouping edit may key a variable inside the
    # subprocess it now belongs to. Only elementId changes.
    assert_variables_preserved_or_rescoped(
        grouped(ORDER_ID + "\n        " + LABEL),
        grouped(
            ORDER_ID,
            '<uipath:inputOutput id="Var_Label" name="Label" type="string" elementId="Sub_Pack" />',
        ),
    )


def test_rescope_dropping_a_declaration_fails() -> None:
    with pytest.raises(SystemExit, match="was dropped by the edit"):
        assert_variables_preserved_or_rescoped(
            grouped(ORDER_ID + "\n        " + LABEL),
            grouped(ORDER_ID),
        )


def test_rescope_retyping_a_declaration_fails() -> None:
    with pytest.raises(SystemExit, match="changed its type"):
        assert_variables_preserved_or_rescoped(
            grouped(ORDER_ID + "\n        " + LABEL),
            grouped(ORDER_ID + '\n        <uipath:inputOutput id="Var_Label" name="Label" type="number" elementId="Process_1" />'),
        )


def test_rescope_changing_kind_fails() -> None:
    with pytest.raises(SystemExit, match="changed kind"):
        assert_variables_preserved_or_rescoped(
            grouped(ORDER_ID + "\n        " + LABEL),
            grouped(ORDER_ID + '\n        <uipath:output id="Var_Label" name="Label" type="string" elementId="Process_1" />'),
        )


def test_rescope_to_a_nonexistent_element_fails() -> None:
    with pytest.raises(SystemExit, match="dangling elementId"):
        assert_variables_preserved_or_rescoped(
            grouped(ORDER_ID + "\n        " + LABEL),
            grouped(ORDER_ID + '\n        <uipath:inputOutput id="Var_Label" name="Label" type="string" elementId="Sub_Packk" />'),
        )


def test_rescope_duplicating_an_id_across_blocks_fails() -> None:
    # A variable left in the root block AND copied into the subprocess is two
    # declarations of one id, which does not import.
    with pytest.raises(SystemExit, match="declared more than once"):
        assert_variables_preserved_or_rescoped(
            grouped(ORDER_ID + "\n        " + LABEL),
            grouped(
                ORDER_ID + "\n        " + LABEL,
                '<uipath:inputOutput id="Var_Label" name="Label" type="string" elementId="Sub_Pack" />',
            ),
        )

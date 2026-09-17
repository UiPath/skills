#!/usr/bin/env python3
"""Unit tests for assert_variables_extended_only (edit_check.py).

Pins the contract that unblocked skill-bpmn-edit-add-node: an edit may ADD
variable declarations (an inserted node's mapped output needs one, #3211), but
every pristine declaration must round-trip untouched.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared.edit_check import assert_variables_extended_only  # noqa: E402

PRISTINE = """<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:uipath="http://uipath.org/schema/bpmn">
  <bpmn:process id="Process_1">
    <bpmn:extensionElements>
      <uipath:variables version="v1">
        <uipath:inputOutput id="Var_OrderId" name="OrderId" type="string" elementId="Process_1" />
        <uipath:inputOutput id="Var_Qty" name="Qty" type="number" elementId="Process_1" />
      </uipath:variables>
    </bpmn:extensionElements>
  </bpmn:process>
</bpmn:definitions>
"""


def edited(variables_xml: str) -> ET.Element:
    return ET.fromstring(
        PRISTINE.replace(
            '<uipath:inputOutput id="Var_OrderId" name="OrderId" type="string" elementId="Process_1" />\n'
            '        <uipath:inputOutput id="Var_Qty" name="Qty" type="number" elementId="Process_1" />',
            variables_xml,
        )
    )


def original() -> ET.Element:
    return ET.fromstring(PRISTINE)


def test_identical_block_passes() -> None:
    assert_variables_extended_only(original(), original())


def test_addition_passes() -> None:
    # The exact shape the 09-16/09-17 nightlies red-flagged: everything
    # pristine preserved, one new declaration for the inserted node.
    assert_variables_extended_only(
        original(),
        edited(
            '<uipath:inputOutput id="Var_OrderId" name="OrderId" type="string" elementId="Process_1" />\n'
            '        <uipath:inputOutput id="Var_Qty" name="Qty" type="number" elementId="Process_1" />\n'
            '        <uipath:inputOutput id="Var_Reserved" name="reserved" type="boolean" elementId="Task_Reserve" />'
        ),
    )


def test_modified_pristine_fails() -> None:
    with pytest.raises(SystemExit):
        assert_variables_extended_only(
            original(),
            edited(
                '<uipath:inputOutput id="Var_OrderId" name="OrderId" type="number" elementId="Process_1" />\n'
                '        <uipath:inputOutput id="Var_Qty" name="Qty" type="number" elementId="Process_1" />'
            ),
        )


def test_removed_pristine_fails() -> None:
    with pytest.raises(SystemExit):
        assert_variables_extended_only(
            original(),
            edited(
                '<uipath:inputOutput id="Var_OrderId" name="OrderId" type="string" elementId="Process_1" />'
            ),
        )


def test_duplicate_ids_fail() -> None:
    with pytest.raises(SystemExit):
        assert_variables_extended_only(
            original(),
            edited(
                '<uipath:inputOutput id="Var_OrderId" name="OrderId" type="string" elementId="Process_1" />\n'
                '        <uipath:inputOutput id="Var_Qty" name="Qty" type="number" elementId="Process_1" />\n'
                '        <uipath:inputOutput id="Var_Qty" name="QtyCopy" type="number" elementId="Process_1" />'
            ),
        )

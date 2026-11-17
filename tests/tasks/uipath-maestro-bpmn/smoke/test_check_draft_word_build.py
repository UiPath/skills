#!/usr/bin/env python3
"""Unit tests for check_draft_word_build.wired_activities. Stdlib and pytest only.

A skeleton's bare boxes must not count; a script task and an assignment task
(`.task(id, { set })`, compiled to a `uipath:mapping` payload) must.
"""

from __future__ import annotations

import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("check_draft_word_build", HERE / "check_draft_word_build.py")
assert _spec and _spec.loader
build = importlib.util.module_from_spec(_spec)
sys.modules["check_draft_word_build"] = build
_spec.loader.exec_module(build)

_HEAD = ('<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
         'xmlns:uipath="http://uipath.org/schema/bpmn"><bpmn:process id="p">')
_TAIL = "</bpmn:process></bpmn:definitions>"


def _root(body: str) -> ET.Element:
    return ET.fromstring(_HEAD + body + _TAIL)


def test_bare_skeleton_boxes_do_not_count() -> None:
    assert build.wired_activities(_root('<bpmn:task id="a" name="Compute cost"/><bpmn:task id="b"/>')) == []


def test_assignment_task_counts() -> None:
    body = ('<bpmn:task id="a"><bpmn:extensionElements><uipath:mapping version="v1">'
            '<uipath:type value="BPMN.Variables" version="v1"/></uipath:mapping>'
            '</bpmn:extensionElements></bpmn:task>')
    assert len(build.wired_activities(_root(body))) == 1


def test_registry_task_counts() -> None:
    body = '<bpmn:task id="a"><bpmn:extensionElements><uipath:activity/></bpmn:extensionElements></bpmn:task>'
    assert len(build.wired_activities(_root(body))) == 1


def test_script_task_counts() -> None:
    assert len(build.wired_activities(_root('<bpmn:scriptTask id="s"/>'))) == 1

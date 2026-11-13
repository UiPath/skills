#!/usr/bin/env python3
"""Unit tests for the fork-exit and multi-instance checks in check_draft_skeleton.py.

Stdlib and pytest only. Each rule gets a passing and a failing fixture.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


skeleton = _load("check_draft_skeleton", "check_draft_skeleton.py")

HEAD = ('<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn"><bpmn:process id="Process_1">')
TAIL = "</bpmn:process></bpmn:definitions>"


def process(body: str, flows: str) -> ET.Element:
    """Parse a process from element markup and 'source>target' flow pairs."""
    seq = "".join(f'<bpmn:sequenceFlow id="F{i}" sourceRef="{s}" targetRef="{t}" />'
                  for i, (s, t) in enumerate(pair.split(">") for pair in flows.split()))
    return ET.fromstring(HEAD + body + seq + TAIL)


def boundary(bid: str, on: str, interrupting: bool = True, kind: str = "error") -> str:
    cancel = "" if interrupting else ' cancelActivity="false"'
    return (f'<bpmn:boundaryEvent id="{bid}" attachedToRef="{on}"{cancel}>'
            f"<bpmn:{kind}EventDefinition /></bpmn:boundaryEvent>")


def end(eid: str, kind: str = "") -> str:
    inner = f"<bpmn:{kind}EventDefinition />" if kind else ""
    return f'<bpmn:endEvent id="{eid}">{inner}</bpmn:endEvent>'


# Start → F → A, B → J → End: the fork every fork-exit fixture extends.
FORK = ('<bpmn:startEvent id="S" /><bpmn:parallelGateway id="F" /><bpmn:parallelGateway id="J" />'
        '<bpmn:task id="A" /><bpmn:task id="B" />' + end("End"))
FORK_FLOWS = "S>F F>A F>B A>J B>J J>End"


class ForkExitTests(unittest.TestCase):
    def assert_safe(self, body: str, flows: str):
        root = process(FORK + body, FORK_FLOWS + " " + flows)
        skeleton.require_fork_exits_safe(root, skeleton.elements(root, "sequenceFlow"))

    def assert_stalls(self, body: str, flows: str, message: str):
        with self.assertRaises(SystemExit) as caught:
            self.assert_safe(body, flows)
        self.assertIn(message, str(caught.exception))

    def test_plain_fork_passes(self):
        self.assert_safe("", "")

    def test_error_path_to_terminate_end_passes(self):
        self.assert_safe(boundary("Err", "A") + end("Stop", "terminate"), "Err>Stop")

    def test_error_path_to_error_end_passes(self):
        self.assert_safe(boundary("Err", "A") + end("Raise", "error"), "Err>Raise")

    def test_error_path_to_plain_end_stalls(self):
        self.assert_stalls(boundary("Err", "A") + end("Gone"), "Err>Gone", "plain end event(s) ['Gone']")

    def test_recovery_merged_onto_its_own_branch_passes(self):
        # A → M → J; the fallback rejoins at M, so A's join input still delivers.
        root = process(FORK.replace('<bpmn:task id="B" />', '<bpmn:task id="B" /><bpmn:exclusiveGateway id="M" />')
                       + boundary("Err", "A") + '<bpmn:task id="X" />',
                       "S>F F>A F>B A>M M>J B>J J>End Err>X X>M")
        skeleton.require_fork_exits_safe(root, skeleton.elements(root, "sequenceFlow"))

    def test_recovery_straight_into_the_join_stalls(self):
        self.assert_stalls(boundary("Err", "A") + '<bpmn:task id="X" />', "Err>X X>J", "instead of its own branch")

    def test_recovery_onto_a_sibling_branch_stalls(self):
        # A's fallback runs through B, so A's own flow into J never delivers.
        self.assert_stalls(boundary("Err", "A") + '<bpmn:task id="X" />', "Err>X X>B", "instead of its own branch")

    def test_non_interrupting_escalation_to_plain_end_passes(self):
        self.assert_safe(boundary("Late", "A", interrupting=False, kind="timer") + '<bpmn:task id="Esc" />'
                         + end("Escalated"), "Late>Esc Esc>Escalated")

    def test_non_interrupting_escalation_into_the_join_stalls(self):
        self.assert_stalls(boundary("Late", "A", interrupting=False, kind="timer") + '<bpmn:task id="Esc" />',
                           "Late>Esc Esc>J", "only delivers when it fires")

    def test_plain_end_between_nested_joins_stalls(self):
        # F → (A, F2 → (C, D) → J2 → G) → J; G may exit to a plain end before the outer join.
        root = process(FORK.replace('<bpmn:task id="B" />', "")
                       + '<bpmn:parallelGateway id="F2" /><bpmn:parallelGateway id="J2" />'
                       '<bpmn:task id="C" /><bpmn:task id="D" /><bpmn:exclusiveGateway id="G" />' + end("Gone"),
                       "S>F F>A F>F2 F2>C F2>D C>J2 D>J2 J2>G G>J G>Gone A>J J>End")
        with self.assertRaises(SystemExit) as caught:
            skeleton.require_fork_exits_safe(root, skeleton.elements(root, "sequenceFlow"))
        self.assertIn("['Gone']", str(caught.exception))

    def test_no_fork_fails(self):
        root = process('<bpmn:startEvent id="S" /><bpmn:task id="A" />' + end("End"), "S>A A>End")
        with self.assertRaises(SystemExit):
            skeleton.require_fork_exits_safe(root, skeleton.elements(root, "sequenceFlow"))


def mi_task(tid: str, sequential: bool, stop: str = "", collection: str = "=vars.Items") -> str:
    seq = ' isSequential="true"' if sequential else ""
    cond = f"<bpmn:completionCondition>{stop}</bpmn:completionCondition>" if stop else ""
    loop = f'<uipath:loopCharacteristics inputCollection="{collection}" />' if collection else ""
    return (f'<bpmn:task id="{tid}"><bpmn:multiInstanceLoopCharacteristics{seq}>'
            f"<bpmn:extensionElements>{loop}</bpmn:extensionElements>{cond}"
            "</bpmn:multiInstanceLoopCharacteristics></bpmn:task>")


class MultiInstanceTests(unittest.TestCase):
    def check(self, body: str):
        skeleton.require_multi_instance(process(body, ""))

    def assert_fails(self, body: str, message: str):
        with self.assertRaises(SystemExit) as caught:
            self.check(body)
        self.assertIn(message, str(caught.exception))

    def test_sequential_with_condition_and_parallel_passes(self):
        self.check(mi_task("Seq", True, "=vars.Flagged") + mi_task("Par", False))

    def test_sequential_stopped_by_error_boundary_passes(self):
        self.check(mi_task("Seq", True) + boundary("Err", "Seq") + mi_task("Par", False))

    def test_sequential_without_a_stop_fails(self):
        self.assert_fails(mi_task("Seq", True) + mi_task("Par", False), "stops early")

    def test_non_interrupting_boundary_does_not_stop_a_sequential_box(self):
        self.assert_fails(mi_task("Seq", True) + boundary("Err", "Seq", interrupting=False) + mi_task("Par", False),
                          "stops early")

    def test_parallel_only_fails(self):
        self.assert_fails(mi_task("Par", False), "stops early")

    def test_missing_parallel_fails(self):
        self.assert_fails(mi_task("Seq", True, "=vars.Flagged"), "parallel multi-instance")

    def test_missing_input_collection_fails(self):
        self.assert_fails(mi_task("Seq", True, "=vars.Flagged", collection="") + mi_task("Par", False),
                          "inputCollection")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Unit tests for check_skeleton_kinds.py. Stdlib and pytest only.

Each check gets a passing and a failing fixture.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


kinds = _load("check_skeleton_kinds", "check_skeleton_kinds.py")

BOXES = ["Record invoice [Execute script]", "Manager review [Action app]", "Auto approve [Execute script]"]


@contextmanager
def _cwd(path: str):
    old = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


REGISTRY = {"Data": {"ExtensionTypes": [
    {"ExtensionType": "Actions.HITL", "Kind": "Action app", "Label": "Create action app task"},
    {"ExtensionType": "Orchestrator.StartJob", "Kind": "RPA workflow", "Label": "Start and wait for RPA workflow"},
    {"ExtensionType": "BPMN.ScriptTask", "Kind": None, "Label": "Execute script"},
    {"ExtensionType": "Orchestrator.BusinessRules", "Kind": None, "Label": "Execute business rule [Preview]"},
    {"ExtensionType": "Maestro.NotificationService", "Kind": None, "Label": "Notification service"},
    {"ExtensionType": "Maestro.CaseManagerPlaceholder", "Kind": None, "Label": "Case manager placeholder"},
    {"ExtensionType": "BPMN.Variables", "Kind": None, "Label": "BPMN Variables"},
]}}


class KindTests(unittest.TestCase):
    def setUp(self):
        self.toolbox, self.case_only = kinds.kind_sets(REGISTRY["Data"]["ExtensionTypes"])

    def check(self, boxes):
        return kinds.check(boxes, self.toolbox, self.case_only)

    def test_kinds_and_labels_from_the_list_pass(self):
        self.assertEqual(self.check(BOXES + ["Score risk [Execute business rule [Preview]]",
                                             "Classify [RPA workflow] → Classification",
                                             "Review [action app]"]), [])

    def test_box_without_a_kind_fails(self):
        self.assertTrue(self.check(["Record invoice"]))

    def test_invented_kind_fails(self):
        errors = self.check(["Send summary [Email]"])
        self.assertIn("not a Kind or Label", errors[0])

    def test_case_only_type_fails(self):
        errors = self.check(["Tell the manager [Notification service]", "Hold [Case manager placeholder]"])
        self.assertEqual(len(errors), 2)
        self.assertTrue(all("case-management" in e for e in errors), errors)

    def test_cli_entry_point_on_a_skeleton(self):
        bpmn = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL">
  <bpmn:process id="Process_1">
    <bpmn:task id="A" name="Record invoice [Execute script]" />
    <bpmn:task id="B" name="Manager review [Action app]" />
  </bpmn:process>
</bpmn:definitions>"""
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "P").mkdir()
            (Path(d) / "P" / "P.bpmn").write_text(bpmn)
            (Path(d) / "P" / "project.uiproj").write_text("{}")
            (Path(d) / "reg.json").write_text(json.dumps(REGISTRY))
            with _cwd(d):
                self.assertEqual(kinds.main(["P", "--registry-json", "reg.json"]), 0)
                (Path(d) / "P" / "P.bpmn").write_text(bpmn.replace("[Action app]", "[Approval]"))
                self.assertEqual(kinds.main(["P", "--registry-json", "reg.json"]), 1)


if __name__ == "__main__":
    unittest.main()

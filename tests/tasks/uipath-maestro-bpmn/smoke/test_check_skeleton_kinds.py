#!/usr/bin/env python3
"""Unit tests for check_skeleton_kinds.py. Stdlib and pytest only.

Each check gets a passing and a failing fixture.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
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
    {"ExtensionType": "Actions.HITL", "Label": "Create action app task"},
    {"ExtensionType": "Orchestrator.StartJob", "Label": "Start and wait for RPA workflow"},
    {"ExtensionType": "BPMN.ScriptTask", "Label": "Execute script"},
    {"ExtensionType": "Intsvc.ActivityExecution", "Label": "Execute connector activity"},
    {"ExtensionType": "Orchestrator.BusinessRules", "Label": "Execute business rule [Preview]"},
    {"ExtensionType": "Maestro.NotificationService", "Label": "Notification service"},
    {"ExtensionType": "Intsvc.HttpExecution", "Label": "Execute HTTP request (Legacy)"},
    {"ExtensionType": "BPMN.TimerTrigger", "Label": "Timer trigger", "BpmnElement": "bpmn:StartEvent"},
    {"ExtensionType": "Maestro.CaseManagerPlaceholder", "Label": "Case manager placeholder"},
    {"ExtensionType": "BPMN.Variables", "Label": "BPMN Variables"},
]}}


class KindTests(unittest.TestCase):
    def setUp(self):
        self.toolbox, self.dropped = kinds.kind_sets(REGISTRY["Data"]["ExtensionTypes"])

    def check(self, boxes, apps=()):
        return kinds.check(boxes, self.toolbox, self.dropped, apps)

    def test_table_kinds_and_other_labels_pass(self):
        self.assertEqual(self.check(BOXES + ["Score risk [Business rule]",
                                             "Classify [RPA workflow] → Classification",
                                             "Review [action app]",
                                             "Notify the owner [Connector]",
                                             "Start child [Maestro Flow]"]), [])

    def test_long_label_of_a_table_type_fails(self):
        errors = self.check(["Score risk [Execute business rule [Preview]]", "Review [Create action app task]",
                             "Notify [Execute connector activity]"])
        self.assertEqual(len(errors), 3, errors)
        self.assertTrue(all("neither a toolbox kind" in e for e in errors), errors)

    def test_box_without_a_kind_fails(self):
        self.assertTrue(self.check(["Record invoice"]))

    def test_connector_label_passes_without_apps(self):
        self.assertEqual(self.check(["Notify [Connector]"]), [])

    def test_app_name_fails_without_apps_and_passes_when_listed(self):
        self.assertEqual(len(self.check(["Post [Slack]"])), 1)
        self.assertEqual(self.check(["Post [Slack]", "Open ticket [jira] → TicketId"], apps=["Slack", "Jira"]), [])
        self.assertEqual(self.check(["Save [Microsoft OneDrive & SharePoint]"],
                                    apps=["Microsoft OneDrive & SharePoint"]), [])
        self.assertEqual(len(self.check(["Post [Teams]"], apps=["Slack"])), 1)

    def test_invented_kind_fails(self):
        errors = self.check(["A [Robot]", "B [Approval]", "C [Decision table]", "D [Script]"])
        self.assertEqual(len(errors), 4, errors)
        self.assertTrue(all("neither a toolbox kind" in e for e in errors), errors)

    def test_long_or_empty_kind_fails(self):
        errors = self.check(["Send summary [Send the summary to the team]", "Send [ ]"])
        self.assertEqual(len(errors), 2, errors)
        self.assertTrue(all("neither a toolbox kind" in e for e in errors), errors)

    def test_types_the_1a_filter_drops_fail(self):
        errors = self.check(["Call API [Execute HTTP request (Legacy)]", "Wait [Timer trigger]"])
        self.assertEqual(len(errors), 2, errors)
        self.assertTrue(all("filter drops" in e for e in errors), errors)

    def test_case_only_type_fails(self):
        errors = self.check(["Tell the manager [Notification service]", "Hold [Case manager placeholder]"])
        self.assertEqual(len(errors), 2)
        self.assertTrue(all("filter drops" in e for e in errors), errors)

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
                (Path(d) / "P" / "P.bpmn").write_text(bpmn.replace("[Action app]", "[Create action app task]"))
                self.assertEqual(kinds.main(["P", "--registry-json", "reg.json"]), 1)


SKILL_DIR = HERE.parents[3] / "skills" / "uipath-maestro-bpmn"
GUIDE = SKILL_DIR / "references" / "phase-2-skeleton-guide.md"
SKILL_MD = SKILL_DIR / "SKILL.md"


def _read_or_skip(path: Path) -> str:
    if not path.is_file():
        raise unittest.SkipTest(f"{path} is absent (tests run outside the repo checkout)")
    return path.read_text(encoding="utf-8")


class DriftTests(unittest.TestCase):
    """The grader's constants are copies of the skill's text; fail when they drift."""

    def test_toolbox_kinds_match_guide_table(self):
        text = _read_or_skip(GUIDE)
        match = re.search(r"^### Toolbox kinds\n(.*?)(?=^#{1,3} )", text, re.S | re.M)
        if not match:
            self.fail("phase-2-skeleton-guide.md has no '### Toolbox kinds' section; the skill changed shape")
        table = {}
        for row in re.findall(r"^\|(.+?)\|(.+?)\|\s*$", match.group(1), re.M):
            types = re.findall(r"`([^`]+)`", row[0])
            if not types or row[0].strip() == "Type":
                continue
            kind = row[1].strip()
            kind = kinds.CONNECTOR_KIND if kind.startswith("`<App>`") else kind
            for t in types:
                table[t] = kind
        self.assertTrue(table, "no rows parsed from the Toolbox kinds table")
        self.assertEqual(table, kinds.TOOLBOX_KINDS)

    def test_exclusions_match_skill_1a_filter(self):
        text = _read_or_skip(SKILL_MD)
        match = re.search(r'registry list[^\n]*--output-filter "ExtensionTypes\[\?([^"]*)"', text)
        if not match:
            self.fail("SKILL.md has no 1a `registry list --output-filter`; the skill changed shape")
        expr = match.group(1)
        prefixes = re.findall(r"starts_with\(ExtensionType,'([^']+)'\)", expr)
        listed = re.search(r"contains\(\[([^\]]*)\],ExtensionType\)", expr)
        self.assertEqual(prefixes, [kinds.CASE_ONLY_PREFIX])
        self.assertIsNotNone(listed, "no contains([...],ExtensionType) exclusion list in the 1a filter")
        exact = set(re.findall(r"'([^']+)'", listed.group(1)))
        self.assertEqual(exact, kinds.CASE_ONLY_EXACT | kinds.OTHER_DROPPED_EXACT)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression tests for shared Maestro BPMN eval assertions."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bpmn_assertions import assert_generated_project_scaffold  # noqa: E402


class GeneratedProjectScaffoldTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project = Path(self.temp_dir.name)
        self._write(
            "project.uiproj",
            {"Name": "Sample", "ProjectType": "ProcessOrchestration"},
        )
        self._write(
            "operate.json",
            {
                "main": "/content/Sample.bpmn#Event_start",
                "contentType": "ProcessOrchestration",
            },
        )
        self._write(
            "entry-points.json",
            {
                "entryPoints": [
                    {
                        "filePath": "/content/Sample.bpmn#Event_start",
                        "uniqueId": "11111111-1111-4111-8111-111111111111",
                        "type": "ProcessOrchestration",
                    }
                ]
            },
        )
        self._write("bindings_v2.json", {"version": "2.0", "resources": []})
        self._write(
            "package-descriptor.json",
            {
                "files": {
                    "operate.json": "operate.json",
                    "entry-points.json": "entry-points.json",
                    "bindings.json": "bindings_v2.json",
                    "Sample.bpmn": "Sample.bpmn",
                }
            },
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write(self, name: str, content: dict) -> None:
        (self.project / name).write_text(json.dumps(content), encoding="utf-8")

    def assert_scaffold(self) -> None:
        assert_generated_project_scaffold(
            self.project,
            "Sample",
            "Sample.bpmn",
            "Event_start",
            entry_point_id="11111111-1111-4111-8111-111111111111",
            expected_resource_count=0,
        )

    def test_accepts_current_cli_metadata_shape(self) -> None:
        self.assert_scaffold()

    def test_accepts_preserved_project_main_field(self) -> None:
        # The CLI does not write `main` but preserves a hand-authored one (#2774).
        self._write(
            "project.uiproj",
            {
                "Name": "Sample",
                "ProjectType": "ProcessOrchestration",
                "main": "Sample.bpmn",
            },
        )
        self.assert_scaffold()

    def test_rejects_project_main_field_pointing_elsewhere(self) -> None:
        self._write(
            "project.uiproj",
            {
                "Name": "Sample",
                "ProjectType": "ProcessOrchestration",
                "main": "SomethingElse.bpmn",
            },
        )
        with self.assertRaisesRegex(SystemExit, "must be absent or reference"):
            self.assert_scaffold()

    def test_rejects_legacy_package_content_list(self) -> None:
        self._write(
            "package-descriptor.json",
            {
                "content": [
                    "content/Sample.bpmn",
                    "content/bindings_v2.json",
                    "content/entry-points.json",
                    "content/operate.json",
                ]
            },
        )
        with self.assertRaisesRegex(SystemExit, "current CLI root files map"):
            self.assert_scaffold()


if __name__ == "__main__":
    unittest.main()

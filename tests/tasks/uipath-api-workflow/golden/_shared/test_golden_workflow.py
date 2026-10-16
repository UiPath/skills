#!/usr/bin/env python3
"""Offline tests for golden_connectors.py's workflow side: finding the agent's workflow,
its declared inputs, the signed-in run, and walking an output's strings and records.

Run: python3 -m unittest discover -s <this directory>
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import golden_connectors as gc  # noqa: E402


class WorkflowTests(unittest.TestCase):
    def test_declared_inputs_keeps_each_schema(self):
        workflow = {"input": {"schema": {"document": {"properties": {"epicKeys": {"type": "array"}, "x": 1}}}}}
        self.assertEqual(gc.declared_inputs(workflow), {"epicKeys": {"type": "array"}, "x": {}})
        self.assertEqual(gc.declared_inputs({}), {})

    def test_find_workflow_ignores_the_root_file_and_node_modules(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ("Workflow.json", "node_modules/pkg/Workflow.json", "B/Workflow.json", "A/Workflow.json"):
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
                (root / relative).write_text("{}")
            self.assertEqual(gc.find_workflow(tmp), (root / "A/Workflow.json").resolve())

    def test_run_workflow_runs_signed_in(self):
        with mock.patch.object(gc, "run_row", return_value=(True, {}, None)) as run_row:
            gc.run_workflow("W.json", {"a": 1}, timeout=30)
        run_row.assert_called_once_with("W.json", {"a": 1}, timeout=30, no_auth=False)


class OutputWalkTests(unittest.TestCase):
    def test_collects_keys_values_and_json_held_in_strings(self):
        raw = {"notes": '[{"summary": "CSV export"}]', "count": 2}
        found = gc.strings_in(raw)
        self.assertIn("notes", found)
        self.assertIn("summary", found)
        self.assertIn("CSV export", found)

    def test_decode_json_string_only_returns_containers(self):
        self.assertEqual(gc.decode_json_string(' {"a": 1}'), {"a": 1})
        self.assertIsNone(gc.decode_json_string('"text"'))
        self.assertIsNone(gc.decode_json_string("[not json"))

    def test_dicts_in_walks_nested_lists(self):
        self.assertEqual([d["k"] for d in gc.dicts_in({"k": 1, "items": [{"k": 2}, [{"k": 3}]]})], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()

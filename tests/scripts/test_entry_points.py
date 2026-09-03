#!/usr/bin/env python3
"""Behavioral tests for the coded-action contract deriver.

The load-bearing tests are the golden ones: `tools/entry_points.py` has to reproduce the manifests
Studio Web derived for two jobs that deployed and ran on a live tenant. Those manifests are the
only evidence of what the platform accepts, and the deriver exists because `uip functions pack`
cannot produce them.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "entry_points.py"
FIXTURES = ROOT / "tests" / "tasks" / "uipath-ontology-modeler" / "_shared" / "fixtures" / "entry-points"
GOLDEN = ("tagOverdueTicket", "flagBigOrder")


def derive(job: Path, *extra: str) -> tuple[int, dict | None, str]:
    result = subprocess.run(
        [sys.executable, str(TOOL), str(job), *extra],
        cwd=ROOT, capture_output=True, text=True,
    )
    try:
        payload = json.loads(result.stdout) if result.stdout.strip() else json.loads(result.stderr)
    except json.JSONDecodeError:
        payload = None
    return result.returncode, payload, result.stdout + result.stderr


class GoldenDerivationTests(unittest.TestCase):
    """The deriver must match Studio Web's own output, or the manifest it ships is a guess."""

    def test_derives_the_schemas_studio_web_derived(self):
        for job in GOLDEN:
            with self.subTest(job=job):
                code, payload, raw = derive(FIXTURES / f"{job}.ts")
                self.assertEqual(code, 0, raw)
                golden = json.loads((FIXTURES / f"{job}.golden.json").read_text())
                mine = payload["entryPoints"][0]
                theirs = golden["entryPoints"][0]
                self.assertEqual(mine["input"], theirs["input"])
                self.assertEqual(mine["output"], theirs["output"])

    def test_envelope_matches_the_platform_schema(self):
        code, payload, raw = derive(FIXTURES / "tagOverdueTicket.ts")
        self.assertEqual(code, 0, raw)
        golden = json.loads((FIXTURES / "tagOverdueTicket.golden.json").read_text())
        self.assertEqual(payload["$schema"], golden["$schema"])
        self.assertEqual(payload["$id"], golden["$id"])
        self.assertEqual(payload["entryPoints"][0]["type"], "function")

    def test_input_is_closed_and_read_rows_are_open(self):
        """additionalProperties:false on the input is what faults a drifted payload before the
        handler. A read row needs the opposite: reads are SELECT *, so columns the job never
        declared do arrive."""
        code, payload, raw = derive(FIXTURES / "tagOverdueTicket.ts")
        self.assertEqual(code, 0, raw)
        schema = payload["entryPoints"][0]["input"]
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(schema["properties"]["ticket"]["items"]["additionalProperties"], {})


class FailClosedTests(unittest.TestCase):
    """A wrong manifest faults the job before its handler runs, so a contract the deriver cannot
    read has to be refused rather than approximated."""

    def _mutate(self, old: str, new: str) -> Path:
        target = Path(tempfile.mkdtemp(prefix="entry-points-")) / "job.ts"
        source = (FIXTURES / "tagOverdueTicket.ts").read_text()
        self.assertIn(old, source)
        target.write_text(source.replace(old, new))
        self.addCleanup(shutil.rmtree, target.parent, ignore_errors=True)
        return target

    def test_unsupported_field_type_is_refused(self):
        code, payload, raw = derive(self._mutate("CreatedAt: string;", "CreatedAt: Date;"))
        self.assertEqual(code, 1, raw)
        self.assertIn("cannot lower type 'Date'", payload["error"])

    def test_inline_object_type_is_refused(self):
        code, payload, raw = derive(self._mutate("ticket: TicketRow[];", "ticket: { a: string }[];"))
        self.assertEqual(code, 1, raw)
        self.assertIn("cannot lower", payload["error"])

    def test_undeclared_interface_is_refused(self):
        code, payload, raw = derive(self._mutate("ticket: TicketRow[];", "ticket: Mystery[];"))
        self.assertEqual(code, 1, raw)
        self.assertIn("Mystery", payload["error"])

    def test_recursive_interface_is_refused(self):
        code, payload, raw = derive(
            self._mutate("interface Input {", "interface Input {\n  self: Input;")
        )
        self.assertEqual(code, 1, raw)
        self.assertIn("recursive", payload["error"])

    def test_a_contract_declared_another_way_is_refused_not_guessed(self):
        code, payload, raw = derive(self._mutate("input: type<Input>()", "input: somethingElse()"))
        self.assertEqual(code, 1, raw)
        self.assertIn("no type<T>() contract", payload["error"])

    def test_a_missing_job_is_a_usage_error(self):
        code, _, raw = derive(FIXTURES / "does-not-exist.ts")
        self.assertEqual(code, 2, raw)


class WriteAndCheckTests(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp(prefix="entry-points-out-")) / "entry-points.json"
        self.addCleanup(shutil.rmtree, self.out.parent, ignore_errors=True)

    def test_rewriting_preserves_the_unique_id(self):
        """The project's bindings reference uniqueId, so regenerating the manifest must not mint a
        new one."""
        derive(FIXTURES / "tagOverdueTicket.ts", "--out", str(self.out))
        first = json.loads(self.out.read_text())["entryPoints"][0]["uniqueId"]
        derive(FIXTURES / "tagOverdueTicket.ts", "--out", str(self.out))
        self.assertEqual(json.loads(self.out.read_text())["entryPoints"][0]["uniqueId"], first)

    def test_rewriting_does_not_inherit_a_stale_file_path(self):
        """filePath names the file that was just staged, so the caller's value has to win. An
        older manifest may name a path from a previous layout, and keeping it would point the
        entry point at a file the package does not contain."""
        derive(FIXTURES / "tagOverdueTicket.ts", "--out", str(self.out))
        doc = json.loads(self.out.read_text())
        doc["entryPoints"][0]["filePath"] = "content/functions/tagOverdueTicket.ts"
        self.out.write_text(json.dumps(doc, indent=2))
        derive(FIXTURES / "tagOverdueTicket.ts", "--out", str(self.out))
        self.assertEqual(
            json.loads(self.out.read_text())["entryPoints"][0]["filePath"], "content/main.ts"
        )

    def test_check_accepts_a_manifest_that_matches(self):
        derive(FIXTURES / "tagOverdueTicket.ts", "--out", str(self.out))
        code, _, raw = derive(FIXTURES / "tagOverdueTicket.ts", "--check", str(self.out))
        self.assertEqual(code, 0, raw)

    def test_check_rejects_a_manifest_that_drifted_from_the_job(self):
        derive(FIXTURES / "tagOverdueTicket.ts", "--out", str(self.out))
        doc = json.loads(self.out.read_text())
        doc["entryPoints"][0]["input"]["properties"]["ticketId"] = {"type": "number"}
        self.out.write_text(json.dumps(doc, indent=2))
        code, payload, raw = derive(FIXTURES / "tagOverdueTicket.ts", "--check", str(self.out))
        self.assertEqual(code, 1, raw)
        self.assertEqual(payload["drift"], ["input"])

    def test_check_reports_the_golden_manifest_as_current(self):
        """The committed goldens are what the platform accepted; --check has to agree they match
        the jobs beside them, or the deriver has drifted from the verified pipeline."""
        for job in GOLDEN:
            with self.subTest(job=job):
                code, _, raw = derive(
                    FIXTURES / f"{job}.ts", "--check", str(FIXTURES / f"{job}.golden.json")
                )
                self.assertEqual(code, 0, raw)


if __name__ == "__main__":
    unittest.main(verbosity=2)

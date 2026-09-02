#!/usr/bin/env python3
"""Behavioral tests for the coded-action preflight CLI.

Each test copies the good pair into a temp workdir, applies one mutation, and asserts that the
mutation fails exactly the gate it targets. Mutation runs pass --skip-typecheck so the assertion
does not depend on whether a TypeScript compiler exists on the machine; the good-pair test runs
without it and accepts either a passed or a skipped typecheck.
"""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "coded_action_preflight.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "support"
ZOD_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "support-zod"
ONTOLOGY = "support"
ACTION = "tagOverdueTicket"


def load_tool():
    """The tool as a module, so a test can ask whether a compiler exists before demanding one."""
    spec = importlib.util.spec_from_file_location("coded_action_preflight", TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_preflight(workdir: Path, *extra: str) -> tuple[int, dict]:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--workdir", str(workdir), "--ontology-name", ONTOLOGY, *extra],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"status": "TOOL_MISSING", "gate_results": [], "errors": {"tool": [result.stderr]}}
    return result.returncode, payload


def failed_gates(payload: dict) -> set[str]:
    return {gate["id"] for gate in payload["gate_results"] if gate["status"] == "failed"}


def gate(payload: dict, gate_id: str) -> dict:
    return next(item for item in payload["gate_results"] if item["id"] == gate_id)


class CodedActionPreflightTests(unittest.TestCase):
    def workdir(self, fixture: Path = FIXTURE) -> Path:
        temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp, True)
        workdir = temp / "artifacts"
        shutil.copytree(fixture, workdir)
        return workdir

    def edit(self, path: Path, old: str, new: str) -> None:
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"fixture drifted: {old!r} is not in {path.name}")
        path.write_text(text.replace(old, new), encoding="utf-8")

    def assert_only_gate_fails(self, workdir: Path, gate_id: str) -> dict:
        code, payload = run_preflight(workdir, "--skip-typecheck")
        self.assertNotEqual(code, 0, payload)
        self.assertEqual(failed_gates(payload), {gate_id}, payload)
        self.assertIn(gate_id, payload["errors"])
        return payload

    # ---- the good pair ---------------------------------------------------------------

    def test_good_pair_passes_every_applicable_gate(self):
        code, payload = run_preflight(self.workdir())
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(failed_gates(payload), set(), payload)
        for gate_id in ("ttl-parses-and-well-formed", "signature-resolves", "input-matches-marker",
                        "input-strictness", "writes-cover-edits", "fields-exist-in-schema",
                        "folder-id-status", "job-language"):
            self.assertEqual(gate(payload, gate_id)["status"], "passed", payload)
        self.assertIn(gate(payload, "typecheck")["status"], ("passed", "skipped"), payload)
        self.assertEqual(
            payload["pairs"],
            [{
                "action": ACTION,
                "ttl": f"{ONTOLOGY}-{ACTION}.ttl",
                "job": f"{ACTION}.ts",
                "job_language": "typescript",
                "process": "TagOverdueTicketProcess",
                "process_folder_id": "3225065",
                "deployable": True,
            }],
        )

    def test_absent_schema_skips_the_field_gate_rather_than_passing_it(self):
        workdir = self.workdir()
        (workdir / f"{ONTOLOGY}.ofn").unlink()
        code, payload = run_preflight(workdir, "--skip-typecheck")
        self.assertEqual(code, 0, payload)
        self.assertEqual(gate(payload, "fields-exist-in-schema")["status"], "skipped", payload)
        self.assertIsNone(gate(payload, "fields-exist-in-schema")["passed"], payload)

    def test_pending_deploy_placeholder_is_reported_as_state_not_failure(self):
        workdir = self.workdir()
        self.edit(workdir / f"{ONTOLOGY}-{ACTION}.ttl", '"3225065"', '"PENDING_DEPLOY"')
        code, payload = run_preflight(workdir, "--skip-typecheck")
        self.assertEqual(code, 0, payload)
        self.assertEqual(gate(payload, "folder-id-status")["status"], "passed", payload)
        self.assertFalse(payload["pairs"][0]["deployable"], payload)

    # ---- one mutation per gate -------------------------------------------------------

    def test_renamed_input_field_fails_input_matches_marker(self):
        workdir = self.workdir()
        job = workdir / "jobs" / f"{ACTION}.ts"
        job.write_text(job.read_text(encoding="utf-8").replace("ticketId", "ticketRef"), encoding="utf-8")
        payload = self.assert_only_gate_fails(workdir, "input-matches-marker")
        self.assertIn("ticketRef", payload["errors"]["input-matches-marker"][0])

    def test_edit_writing_an_undeclared_field_fails_writes_cover_edits(self):
        workdir = self.workdir()
        self.edit(
            workdir / "jobs" / f"{ACTION}.ts",
            "    const tags = row.Labels",
            "    properties.owner = 'unassigned';\n    const tags = row.Labels",
        )
        payload = self.assert_only_gate_fails(workdir, "writes-cover-edits")
        self.assertIn("Ticket.owner", payload["errors"]["writes-cover-edits"][0])

    def test_untraceable_edit_properties_fail_rather_than_read_as_no_writes(self):
        workdir = self.workdir()
        self.edit(
            workdir / "jobs" / f"{ACTION}.ts",
            "entity: 'Ticket', properties }",
            "entity: 'Ticket', properties: buildProperties() }",
        )
        payload = self.assert_only_gate_fails(workdir, "writes-cover-edits")
        self.assertIn("verify by hand", payload["errors"]["writes-cover-edits"][0])

    def test_second_func_marker_fails_ttl_well_formedness(self):
        workdir = self.workdir()
        self.edit(
            workdir / f"{ONTOLOGY}-{ACTION}.ttl",
            '( "func:tagOverdueTicket(ticketId, ticket)" )',
            '( "func:tagOverdueTicket(ticketId, ticket)" "func:tagOverdueTicket(ticketId)" )',
        )
        payload = self.assert_only_gate_fails(workdir, "ttl-parses-and-well-formed")
        self.assertIn("exactly one func: marker", payload["errors"]["ttl-parses-and-well-formed"][0])

    def test_field_absent_from_the_schema_fails_fields_exist(self):
        workdir = self.workdir()
        self.edit(workdir / f"{ONTOLOGY}.ofn", "    Declaration(DataProperty(:Ticket.dueAt))\n", "")
        payload = self.assert_only_gate_fails(workdir, "fields-exist-in-schema")
        self.assertIn("Ticket.dueAt", payload["errors"]["fields-exist-in-schema"][0])

    def test_python_job_fails_job_language_and_skips_the_source_gates(self):
        workdir = self.workdir()
        (workdir / "jobs" / f"{ACTION}.ts").rename(workdir / "jobs" / f"{ACTION}.py")
        payload = self.assert_only_gate_fails(workdir, "job-language")
        self.assertIn("typescript", payload["errors"]["job-language"][0])
        for gate_id in ("input-matches-marker", "writes-cover-edits"):
            self.assertEqual(gate(payload, gate_id)["status"], "skipped", payload)

    def test_op_widening_edit_literal_fails_typecheck_when_a_compiler_exists(self):
        if load_tool().find_tsc(FIXTURE)[0] is None:
            self.skipTest("no TypeScript compiler available")
        workdir = self.workdir()
        self.edit(
            workdir / "jobs" / f"{ACTION}.ts",
            "    const edits: DeclaredEdit[] = [{ op: 'UPDATE', entity: 'Ticket', properties }];\n    return { edits };",
            "    return { edits: [{ op: 'UPDATE', entity: 'Ticket', properties }] };",
        )
        code, payload = run_preflight(workdir)
        self.assertNotEqual(code, 0, payload)
        self.assertEqual(failed_gates(payload), {"typecheck"}, payload)
        self.assertIn("TS2322", payload["errors"]["typecheck"][0])

    # ---- the zod idiom ---------------------------------------------------------------

    def test_zod_good_pair_passes_the_contract_gates(self):
        code, payload = run_preflight(self.workdir(ZOD_FIXTURE), "--skip-typecheck")
        self.assertEqual(code, 0, payload)
        self.assertEqual(payload["status"], "PASS")
        for gate_id in ("input-matches-marker", "input-strictness", "writes-cover-edits",
                        "signature-resolves", "fields-exist-in-schema", "job-language"):
            self.assertEqual(gate(payload, gate_id)["status"], "passed", payload)

    def test_zod_field_rename_fails_input_matches_marker(self):
        workdir = self.workdir(ZOD_FIXTURE)
        job = workdir / "jobs" / f"{ACTION}.ts"
        job.write_text(job.read_text(encoding="utf-8").replace("ticketId", "ticketRef"), encoding="utf-8")
        payload = self.assert_only_gate_fails(workdir, "input-matches-marker")
        self.assertIn("ticketRef", payload["errors"]["input-matches-marker"][0])

    def test_zod_input_without_strict_fails_input_strictness(self):
        workdir = self.workdir(ZOD_FIXTURE)
        self.edit(
            workdir / "jobs" / f"{ACTION}.ts",
            "  ticket: z.array(TicketRow),\n}).strict();",
            "  ticket: z.array(TicketRow),\n});",
        )
        payload = self.assert_only_gate_fails(workdir, "input-strictness")
        self.assertIn("additionalProperties", payload["errors"]["input-strictness"][0])

    def test_type_t_idiom_passes_input_strictness_with_a_note(self):
        code, payload = run_preflight(self.workdir(), "--skip-typecheck")
        self.assertEqual(code, 0, payload)
        self.assertEqual(gate(payload, "input-strictness")["status"], "passed", payload)
        self.assertTrue(
            any("input-strictness" in warning and "type<T>()" in warning for warning in payload["warnings"]),
            payload["warnings"],
        )

    # ---- discovery -------------------------------------------------------------------

    def test_unknown_requested_action_is_a_discovery_failure(self):
        code, payload = run_preflight(self.workdir(), "--action", "noSuchAction", "--skip-typecheck")
        self.assertNotEqual(code, 0, payload)
        self.assertIn("discovery", payload["errors"])


if __name__ == "__main__":
    unittest.main()

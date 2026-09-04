#!/usr/bin/env python3
"""Behavioral tests for the coded-action preflight CLI.

Each test copies the good pair into a temp workdir, applies one mutation, and asserts that the
mutation fails exactly the gate it targets. Mutation runs pass --skip-typecheck so the assertion
does not depend on whether a TypeScript compiler exists on the machine; the good-pair test runs
without it and accepts either a passed or a skipped typecheck.
"""

import importlib.util
import json
import re
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
GOLDEN = Path(__file__).resolve().parent / "golden" / "support.json"
ONTOLOGY = "support"
ACTION = "tagOverdueTicket"
MODELER_REFS = ROOT / "skills" / "uipath-ontology-modeler" / "references"


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


class GoldenPayloadTest(unittest.TestCase):
    """The whole payload, diffed against a committed copy.

    Every other test asserts one gate. This one pins the entire JSON shape: gate order, the
    `skipped: ` prefixing, diagnostics ordering, the pairs[] key set, artifact_inventory. Those
    are all ordering-sensitive and none of them is covered by a per-gate assertion, so a refactor
    that reordered a log.add call would otherwise pass every test while changing what callers see.
    """

    def test_the_good_pair_payload_is_unchanged(self):
        code, payload = run_preflight(FIXTURE, "--skip-typecheck")
        self.assertEqual(code, 0, payload)
        expected = json.loads(GOLDEN.read_text())
        self.assertEqual(payload, expected, "payload drifted from tests/coded_action_preflight/golden/support.json")


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
                        "process-type-declared", "entity-identity-declared",
                        "job-language"):
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
                "process_type": "CODED_FUNCTION",
            }],
        )

    def test_absent_schema_skips_the_field_gate_rather_than_passing_it(self):
        workdir = self.workdir()
        (workdir / f"{ONTOLOGY}.ofn").unlink()
        code, payload = run_preflight(workdir, "--skip-typecheck")
        self.assertEqual(code, 0, payload)
        self.assertEqual(gate(payload, "fields-exist-in-schema")["status"], "skipped", payload)
        self.assertIsNone(gate(payload, "fields-exist-in-schema")["passed"], payload)

    def test_coded_action_without_process_type_fails(self):
        """`ont:language "CODED"` says a job computes the edits, not what kind of job. The service
        refuses a coded action without the runtime named, so catching it offline is the difference
        between a refused upload and one line of prose."""
        workdir = self.workdir()
        self.edit(workdir / f"{ONTOLOGY}-{ACTION}.ttl",
                  '        ont:processType "CODED_FUNCTION" ;\n', "")
        payload = self.assert_only_gate_fails(workdir, "process-type-declared")
        self.assertIn("CODED_FUNCTION", payload["errors"]["process-type-declared"][0])

    def test_unknown_process_type_fails(self):
        workdir = self.workdir()
        self.edit(workdir / f"{ONTOLOGY}-{ACTION}.ttl", '"CODED_FUNCTION"', '"LAMBDA"')
        payload = self.assert_only_gate_fails(workdir, "process-type-declared")
        self.assertIn("LAMBDA", payload["errors"]["process-type-declared"][0])

    def test_written_entity_without_a_key_property_fails(self):
        """Identity is annotation-only: no ont:datatype "key" means the runtime cannot resolve
        which row an edit targets, and the write is refused AFTER the job has run, reporting
        rowsAffected 0 -- indistinguishable in a summary from a legitimate no-op."""
        workdir = self.workdir()
        self.edit(workdir / f"{ONTOLOGY}.ofn",
                  'AnnotationAssertion(:datatype :Ticket.id "key")\n', "")
        payload = self.assert_only_gate_fails(workdir, "entity-identity-declared")
        self.assertIn("Ticket", payload["errors"]["entity-identity-declared"][0])

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
            "    const tags = column(row, 'Labels'",
            "    properties.owner = 'unassigned';\n    const tags = column(row, 'Labels'",
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

    def test_a_standard_schema_contract_is_refused(self):
        """A zod (or arktype/valibot) contract carries its own schema and cannot be lowered into
        the manifest this pipeline stages. It used to PASS here, which was the hazard: the deploy
        step would then keep whatever manifest was already in the project -- a manifest belonging to
        some other job -- so this one would deploy under a foreign input schema and fault at invoke
        time. Staging now refuses instead; this gate catches it a phase earlier."""
        payload = self.assert_only_gate_fails(self.workdir(ZOD_FIXTURE), "input-strictness")
        detail = payload["errors"]["input-strictness"][0]
        self.assertIn("zod", detail)
        self.assertIn("type<T>()", detail)

    def test_an_unreadable_contract_reports_one_blame_site(self):
        """input-matches-marker has no interfaces to read for such a job, but failing both gates
        would make the author read two messages for one cause. It skips and points."""
        code, payload = run_preflight(self.workdir(ZOD_FIXTURE), "--skip-typecheck")
        self.assertEqual(code, 1, payload)
        marker = gate(payload, "input-matches-marker")
        self.assertEqual(marker["status"], "skipped", payload)
        self.assertIn("see input-strictness", marker["diagnostics"][0])

    def test_type_t_idiom_passes_strictness_by_lowering_the_contract(self):
        """The gate derives the manifest rather than assuming the SDK will. A type<T>() contract
        is inert on its own, so the derivation is the only thing that can supply
        additionalProperties:false, and running it is the only honest way to check."""
        code, payload = run_preflight(self.workdir(), "--skip-typecheck")
        self.assertEqual(code, 0, payload)
        self.assertEqual(gate(payload, "input-strictness")["status"], "passed", payload)
        # No reassuring warning: the gate proved it, so it has nothing to hedge about.
        self.assertFalse(
            [w for w in payload["warnings"] if "input-strictness" in w],
            payload["warnings"],
        )

    def test_unlowerable_type_t_contract_fails_strictness(self):
        """A contract the deriver cannot lower would fail at pack time with nothing written, so it
        has to fail here instead."""
        workdir = self.workdir()
        self.edit(workdir / "jobs" / f"{ACTION}.ts", "  CreatedAt?: string;", "  CreatedAt?: Date;")
        payload = self.assert_only_gate_fails(workdir, "input-strictness")
        self.assertIn("cannot be lowered", payload["errors"]["input-strictness"][0])

    def test_undeclared_interface_in_input_fails_strictness(self):
        workdir = self.workdir()
        self.edit(
            workdir / "jobs" / f"{ACTION}.ts", "  ticket: TicketRow[];", "  ticket: Mystery[];"
        )
        payload = self.assert_only_gate_fails(workdir, "input-strictness")
        self.assertIn("cannot lower type", payload["errors"]["input-strictness"][0])

    def test_ont_writes_repeated_as_separate_predicates_is_equivalent(self):
        """`ont:writes "A", "B" ;` and the same predicate written twice are equivalent Turtle.
        Reading only the first occurrence under-reported the declaration, so the writes gate
        blamed the job for an edit the TTL did cover."""
        workdir = self.workdir()
        self.edit(
            workdir / f"{ONTOLOGY}-{ACTION}.ttl",
            'ont:writes      "Ticket.tags", "Ticket.dueAt" ;',
            'ont:writes      "Ticket.tags" ;\n        ont:writes      "Ticket.dueAt" ;',
        )
        code, payload = run_preflight(workdir, "--skip-typecheck")
        self.assertEqual(code, 0, payload)
        self.assertEqual(gate(payload, "writes-cover-edits")["status"], "passed", payload)

    # ---- discovery -------------------------------------------------------------------

    def test_unknown_requested_action_is_a_discovery_failure(self):
        code, payload = run_preflight(self.workdir(), "--action", "noSuchAction", "--skip-typecheck")
        self.assertNotEqual(code, 0, payload)
        self.assertIn("discovery", payload["errors"])



class WorkedExampleTests(unittest.TestCase):
    """Every complete job in the modeler's references must compile under the typecheck gate.

    The worked examples are what an agent copies, so a job that does not compile is generation
    that fails preflight. This caught the real case: making row fields optional (a required field
    is rejected before the handler runs) left both examples reading `row.CreatedAt` off the
    interface, which is `string | undefined` under --strict.

    Templates and fragments are excluded by construction -- a block qualifies only if it declares
    `export default defineFunction` and carries no `{Placeholder}` outside a `${...}` interpolation -- so the contract guide's
    skeleton and its one-liners are not held to compiling.
    """

    def complete_jobs(self):
        for md in sorted(MODELER_REFS.glob("*.md")):
            for index, block in enumerate(re.findall(r"```typescript\n(.*?)```", md.read_text(encoding="utf-8"), re.S)):
                if "export default defineFunction" in block and not re.search(r"(?<!\$)\{[A-Za-z][\w ,]*\}", block):
                    yield md.name, index, block

    def test_the_references_contain_the_worked_examples(self):
        """A refactor that renamed the fence or moved the file must not silently empty this suite."""
        found = [(name, index) for name, index, _ in self.complete_jobs()]
        self.assertEqual(len(found), 2, "expected both worked examples, found %s" % (found,))

    def test_every_worked_example_compiles(self):
        tool = load_tool()
        if tool.find_tsc(FIXTURE)[0] is None:
            self.skipTest("no TypeScript compiler available")
        typecheck = importlib.util.spec_from_file_location(
            "coded_action_typecheck", ROOT / "tools" / "coded_action" / "typecheck.py")
        module = importlib.util.module_from_spec(typecheck)
        typecheck.loader.exec_module(module)

        temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, temp, True)
        for name, index, block in self.complete_jobs():
            with self.subTest(reference=name, block=index):
                job = temp / ("%s-%d.ts" % (name, index))
                job.write_text(block, encoding="utf-8")
                status, detail = module.typecheck_job(job, ROOT)
                self.assertEqual(status, "passed", "%s block %d: %s" % (name, index, detail))


if __name__ == "__main__":
    unittest.main()

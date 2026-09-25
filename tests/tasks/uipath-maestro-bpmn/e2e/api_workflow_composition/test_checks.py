#!/usr/bin/env python3
"""Offline unit tests for the API-workflow composition eval's checkers.

Runs in seconds, no live tenant calls: every resolver a real `uip` call would
back is injected here as a plain callable returning a fixture-matching
constant, exactly the way `check_shape.collect_shape_problems` is designed to
be called. Exercises:

  * composition.py's discovery + BPMN/.uipx parsing helpers.
  * check_shape.py's structural + cross-tenant shape rules, against the real
    gold fixture (must be clean) and the full fixtures/mutations/ corpus
    (each mutation must be rejected with a diagnosable reason; the
    valid_* fixtures must be ACCEPTED, proving the checker is
    not overfit to gold's exact ids/ordering).
  * check_shape.assert_validate_clean, with synthetic payloads in the real
    CLI envelope (`Data.Warnings` is one string).
  * check_behavior.py's per-node provenance assertion, with synthetic
    `variables-all` payloads -- including the "one node cannot cover for
    another" case that is this suite's anti-cheat core.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import composition  # noqa: E402
import check_shape  # noqa: E402
import check_behavior  # noqa: E402
from check_shape import CheckFailure  # noqa: E402,F401  (re-exported for readability below)

GOLD = HERE / "fixtures" / "gold" / "GreetingPipelineGoldSolution"
MUTATIONS = HERE / "fixtures" / "mutations"

# Match the literal GUIDs baked into both the real gold fixture and the
# synthetic mutation fixtures (see fixtures/mutations' generation) -- the
# "real tenant" values every resolver below stands in for.
RELEASE_KEY_GOOD = "11111111-1111-4111-8111-111111111111"
FOLDER_KEY_GOOD = "22222222-2222-4222-8222-222222222222"


def matching_resolvers():
    return dict(
        resolve_release_key_for_row=lambda row, project_dir: (lambda binding: {RELEASE_KEY_GOOD}),
        resolve_folder_key=lambda: FOLDER_KEY_GOOD,
    )


def shape_problems(root: Path) -> list[str]:
    return check_shape.collect_shape_problems(root, **matching_resolvers())


class DiscoveryTests(unittest.TestCase):
    def test_finds_uipx_and_bpmn_in_gold(self):
        self.assertIsNotNone(composition.find_uipx(GOLD))
        self.assertIsNotNone(composition.find_bpmn(GOLD))

    def test_excludes_fixtures_and_node_modules(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fixtures" / "decoy").mkdir(parents=True)
            (root / "fixtures" / "decoy" / "Decoy.uipx").write_text("{}", encoding="utf-8")
            (root / "node_modules" / "pkg").mkdir(parents=True)
            (root / "node_modules" / "pkg" / "Pkg.uipx").write_text("{}", encoding="utf-8")
            (root / "Real").mkdir()
            (root / "Real" / "Real.uipx").write_text("{}", encoding="utf-8")

            found = composition.find_one(root, "*.uipx")
            self.assertIsNotNone(found)
            self.assertEqual(found.name, "Real.uipx")

    def test_no_match_returns_none_rather_than_wandering_into_fixtures(self):
        # The task dir's own fixtures/ hold every mutation's .uipx -- asking
        # find_one to search the task dir itself (not a specific solution
        # root) must not surface one of those as a false match.
        found = composition.find_one(HERE, "*.uipx")
        self.assertIsNone(found)

    def test_find_resource_project_requires_marker_alongside(self):
        row = composition.RESOURCES[0]
        project_dir = composition.find_resource_project(GOLD, row)
        self.assertEqual(project_dir.name, "GreetingApi")

    def test_missing_project_not_found(self):
        row = composition.RESOURCES[0]
        self.assertIsNone(
            composition.find_resource_project(MUTATIONS / "missing_project", row)
        )


class UipxRegistrationTests(unittest.TestCase):
    def test_gold_api_project_is_registered(self):
        uipx_path = composition.find_uipx(GOLD)
        project_dir = composition.find_resource_project(GOLD, composition.RESOURCES[0])
        self.assertTrue(composition.project_is_registered(uipx_path, project_dir))

    def test_unregistered_project_fixture_is_not_registered(self):
        root = MUTATIONS / "unregistered_project"
        uipx_path = composition.find_uipx(root)
        project_dir = composition.find_resource_project(root, composition.RESOURCES[0])
        self.assertIsNotNone(project_dir)
        self.assertFalse(composition.project_is_registered(uipx_path, project_dir))


class BpmnParsingTests(unittest.TestCase):
    def test_gold_context_fields(self):
        process = composition.parse_process(composition.find_bpmn(GOLD))
        task = composition.find_wrapper_task(process, composition.RESOURCES[0]["wrapper"])
        self.assertIsNotNone(task)
        context = composition.context_fields_of(task)
        self.assertEqual(set(context), {"releaseKey", "folderKey"})
        self.assertEqual(context["folderKey"]["value"], FOLDER_KEY_GOOD)

    def test_gold_var_refs_all_declared(self):
        process = composition.parse_process(composition.find_bpmn(GOLD))
        declared = composition.declared_variables(process)
        refs = composition.all_var_refs_in_process(process)
        self.assertTrue(refs, "expected at least one vars.<id> reference")
        self.assertEqual(refs - set(declared), set())


class ShapeCheckGoldTests(unittest.TestCase):
    def test_gold_is_clean(self):
        problems = shape_problems(GOLD)
        self.assertEqual(problems, [], f"gold fixture must be clean, got: {problems}")


class ShapeCheckMutationTests(unittest.TestCase):
    """Every mutation must be rejected, each for its own diagnosable reason."""

    def assert_rejected(self, name: str, pattern: str) -> None:
        problems = shape_problems(MUTATIONS / name)
        self.assertTrue(problems, f"{name}: expected a rejection, got none")
        joined = " | ".join(problems)
        self.assertRegex(joined, pattern, f"{name}: problems were {problems!r}")

    def test_missing_project(self):
        self.assert_rejected("missing_project", "no project found")

    def test_unregistered_project(self):
        self.assert_rejected("unregistered_project", "not registered")

    def test_missing_node(self):
        self.assert_rejected("missing_node", "no serviceTask")

    def test_bad_release_key(self):
        self.assert_rejected("bad_release_key", "does not match the resource's real process Key")

    def test_missing_release_key(self):
        self.assert_rejected("missing_release_key", r"context field 'releaseKey' missing")

    def test_bad_folder_key(self):
        self.assert_rejected("bad_folder_key", "does not match the seeded folder's real FolderKey")

    def test_missing_folder_key(self):
        self.assert_rejected("missing_folder_key", r"context field 'folderKey' missing")

    def test_literal_input(self):
        self.assert_rejected("literal_input", "must reference a process variable")

    def test_wrong_target_output(self):
        self.assert_rejected("wrong_target_output", "no end event publishes 'message'")

    def test_node_publishes_input(self):
        # The node's own output reads the process input, not `result`, so the
        # published value never touches the API workflow's response.
        self.assert_rejected("node_publishes_input", "no end event publishes 'message'")

    def test_stray_output_write(self):
        self.assert_rejected("stray_output_write", "'message' is also published from")

    def test_node_overwrites_response_from_input(self):
        # The invoking node itself declares a second `uipath:output` on the
        # same activity, same var, reading the process input instead of its
        # response -- must not slip past because `owner == node_id` for both.
        self.assert_rejected(
            "node_overwrites_response_from_input",
            r"also written by .*Task_InvokeGreeting.*only Task_InvokeGreeting's own response mapping may write",
        )

    def test_node_output_falls_back_to_input(self):
        for name in (
            "node_output_falls_back_to_input",
            "node_output_bracket_fallback",
            "node_output_optional_chain_fallback",
        ):
            with self.subTest(name):
                self.assert_rejected(name, "no end event publishes 'message'")

    def test_end_mapping_mixes_input(self):
        for name in (
            "end_mapping_mixes_input",
            "end_mapping_bracket_mix",
            "end_mapping_optional_chain_mix",
        ):
            with self.subTest(name):
                self.assert_rejected(name, "'message' is also published from")

    def test_unregistered_bpmn_project(self):
        self.assert_rejected("unregistered_bpmn_project", "BPMN project at .* is not registered")

    def test_inexact_contract(self):
        problems = shape_problems(MUTATIONS / "inexact_contract")
        joined = " | ".join(problems)
        self.assertIn("output must publish exactly ['message']", joined)
        self.assertIn("properties ['name'] must be type 'string'", joined)

    def test_undeclared_var_read(self):
        self.assert_rejected("undeclared_var_read", "undeclared variable id")

    def test_empty_published_contract(self):
        problems = shape_problems(MUTATIONS / "empty_published_contract")
        joined = " | ".join(problems)
        self.assertIn("input does not publish", joined)
        self.assertIn("output does not publish 'message'", joined)

    def test_script_overwrites_node_output(self):
        # Vector 1's shape-side half: a decoy scriptTask also writes the
        # invoking node's own output variable (Var_Message) downstream --
        # the BPMN wiring is otherwise gold-identical.
        self.assert_rejected(
            "script_overwrites_node_output",
            r"also written by .*Task_Decoy.*only Task_InvokeGreeting's own response mapping may write",
        )

    def test_unauthored_scaffold(self):
        # Vector 2: gold-correct BPMN wiring around an untouched
        # `uip api-workflow init` scaffold must not earn shape credit.
        self.assert_rejected("unauthored_scaffold", "declares no output for 'message'")
        problems = shape_problems(MUTATIONS / "unauthored_scaffold")
        joined = " | ".join(problems)
        self.assertIn("declares no input.schema.document.properties", joined)
        self.assertIn('no task with a "response" key', joined)

    def test_js_literal_input(self):
        # Vector 4: a `=js:` value with no `vars.` reference at all must not
        # pass just because it starts with `=js:`.
        self.assert_rejected("js_literal_input", "must reference a process variable")


class ShapeCheckAcceptsUnlikeGoldTests(unittest.TestCase):
    def test_valid_unlike_gold_is_accepted(self):
        problems = shape_problems(MUTATIONS / "valid_unlike_gold")
        self.assertEqual(problems, [], f"a structurally-different-but-valid shape must pass, got: {problems}")

    def test_js_end_mapping_is_accepted(self):
        # Node var named `greeting`, end event `=js:'Hello, ' + vars.<id>`,
        # and a leftover `folderPath` context field.
        problems = shape_problems(MUTATIONS / "valid_js_end_mapping")
        self.assertEqual(problems, [], problems)


# ---------------------------------------------------------------------------
# Vector 3 -- live resolvers fail CLOSED: abstention (never_resolves) still
# skips the comparison, but a resolver that raises (a real tenant hiccup)
# must surface as a problem, never a silent WARN-and-skip. Exercised as unit
# tests against check_resource_row directly (not main()'s real `uip` calls).
# ---------------------------------------------------------------------------

class LiveResolverFailClosedTests(unittest.TestCase):
    def setUp(self):
        self.bpmn_path = composition.find_bpmn(GOLD)
        self.process = composition.parse_process(self.bpmn_path)
        self.uipx_path = composition.find_uipx(GOLD)
        self.row = composition.RESOURCES[0]

    def _check(self, resolve_release_key=None, resolve_folder_key=None):
        return check_shape.check_resource_row(
            root=GOLD,
            uipx_path=self.uipx_path,
            process=self.process,
            row=self.row,
            resolve_release_key=resolve_release_key or (lambda binding: {RELEASE_KEY_GOOD}),
            resolve_folder_key=resolve_folder_key or (lambda: FOLDER_KEY_GOOD),
        )

    def test_folder_resolver_raising_is_recorded_as_a_problem(self):
        def boom():
            raise composition.CompositionError("folders get: tenant timeout")

        problems = self._check(resolve_folder_key=boom)
        self.assertTrue(
            any("could not resolve the seeded folder's real Key" in p for p in problems),
            problems,
        )

    def test_release_resolver_raising_is_recorded_as_a_problem(self):
        def boom(_binding):
            raise composition.CompositionError("processes list: tenant timeout")

        problems = self._check(resolve_release_key=boom)
        self.assertTrue(
            any("could not resolve the resource's real process Key" in p for p in problems),
            problems,
        )

    def test_release_resolver_two_keys_default_among_them_is_clean(self):
        problems = self._check(
            resolve_release_key=lambda binding: {RELEASE_KEY_GOOD, "OTHER-DEPLOYED-KEY"}
        )
        self.assertEqual(problems, [], problems)

    def test_release_resolver_default_in_neither_is_a_problem(self):
        problems = self._check(
            resolve_release_key=lambda binding: {"AAAA-KEY", "BBBB-KEY"}
        )
        self.assertTrue(
            any("does not match the resource's real process Key" in p for p in problems),
            problems,
        )

    def test_release_resolver_empty_set_is_a_problem(self):
        problems = self._check(resolve_release_key=lambda binding: set())
        self.assertTrue(
            any("no deployed process found" in p for p in problems),
            problems,
        )

    def test_none_still_abstains(self):
        # composition.never_resolves (or an equivalent) legitimately opts out
        # of the live comparison -- structural-only mode -- and must not be
        # treated as a failure.
        problems = self._check(
            resolve_release_key=lambda binding: None,
            resolve_folder_key=lambda: None,
        )
        self.assertEqual(problems, [], problems)


class ValidateCleanTests(unittest.TestCase):
    def test_valid_status_no_warnings_passes(self):
        payload = {"Result": "Success", "Data": {"File": "p.bpmn", "Status": "Valid"}}
        self.assertEqual(check_shape.assert_validate_clean(payload), [])

    def test_variable_not_set_alone_passes(self):
        # By construction: the node reading the start-event-scoped input.
        payload = {"Result": "Success", "Data": {"Status": "Valid", "Warnings": (
            "1 warning(s):\n  - [Task_InvokeGreeting] VARIABLE_NOT_SET: ..."
        )}}
        self.assertEqual(check_shape.assert_validate_clean(payload), [])

    def test_variable_does_not_exist_fails(self):
        payload = {"Result": "Success", "Data": {"Status": "Valid", "Warnings": (
            "2 warning(s):\n  - [Task_InvokeGreeting] VARIABLE_NOT_SET: ...\n"
            "  - [End_1] VARIABLE_DOES_NOT_EXIST: ..."
        )}}
        problems = check_shape.assert_validate_clean(payload)
        self.assertTrue(any("VARIABLE_DOES_NOT_EXIST" in p for p in problems))

    def test_failure_envelope_fails_with_instructions(self):
        payload = {"Result": "Failure", "Message": "Validation failed", "Instructions": "[End_1] boom"}
        problems = check_shape.assert_validate_clean(payload)
        self.assertTrue(any("Status" in p and "boom" in p for p in problems), problems)


# ---------------------------------------------------------------------------
# check_behavior.py -- per-node provenance, the suite's anti-cheat core
# ---------------------------------------------------------------------------

TOKEN = "tokabc12345"

BEHAVIOR_BPMN = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:uipath="http://uipath.org/schema/bpmn">
  <bpmn:process id="Process_1">
    <bpmn:extensionElements>
      <uipath:variables>
        <uipath:input id="input_name" name="name" type="string" elementId="Event_start"/>
        <uipath:output id="out_message" name="message" type="string" elementId="End_1"/>
      </uipath:variables>
    </bpmn:extensionElements>
    <bpmn:serviceTask id="Task_InvokeGreeting">
      <bpmn:extensionElements>
        <uipath:activity>
          <uipath:type value="Orchestrator.ExecuteApiWorkflowAsync"/>
        </uipath:activity>
      </bpmn:extensionElements>
    </bpmn:serviceTask>
    <bpmn:scriptTask id="Unrelated_Script"/>
  </bpmn:process>
</bpmn:definitions>
"""


def _process():
    import tempfile

    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "sample.bpmn"
        path.write_text(BEHAVIOR_BPMN, encoding="utf-8")
        return composition.parse_process(path)


def _variables_data(elements: list[dict], globals_map: dict) -> dict:
    return {
        "Variables": [
            {"ParentElementId": None, "Globals": globals_map, "Elements": elements}
        ]
    }


class RowProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.process = _process()
        self.row = composition.RESOURCES[0]

    def test_happy_path_passes(self):
        variables_data = _variables_data(
            elements=[
                {
                    "ElementId": "Task_InvokeGreeting",
                    "Outputs": {"response": {"message": f"Hello, {TOKEN}!"}},
                },
            ],
            globals_map={"out_message": f"Hello, {TOKEN}!"},
        )
        # Should not raise.
        check_behavior.assert_row_provenance(self.row, self.process, variables_data, TOKEN)

    def test_token_missing_from_global_fails(self):
        variables_data = _variables_data(
            elements=[{"ElementId": "Task_InvokeGreeting", "Outputs": {"response": {"message": "Hello, nobody!"}}}],
            globals_map={"out_message": "Hello, nobody!"},
        )
        with self.assertRaisesRegex(CheckFailure, "does not contain the minted token"):
            check_behavior.assert_row_provenance(self.row, self.process, variables_data, TOKEN)

    def test_bare_token_global_passes(self):
        # The prompt asks for no transformation: an echo mapped straight
        # through is valid.
        variables_data = _variables_data(
            elements=[{"ElementId": "Task_InvokeGreeting", "Outputs": {"response": {"message": TOKEN}}}],
            globals_map={"out_message": TOKEN},
        )
        check_behavior.assert_row_provenance(self.row, self.process, variables_data, TOKEN)

    def test_one_node_cannot_cover_for_another(self):
        """The suite's anti-cheat core: the global carries the token (so a
        naive "does the output contain the token" check would pass), but the
        invoking node's OWN Outputs never mention it -- only an unrelated
        ScriptTask's Outputs do. This must still fail."""

        variables_data = _variables_data(
            elements=[
                {"ElementId": "Task_InvokeGreeting", "Outputs": {"response": {"message": "unrelated"}}},
                {"ElementId": "Unrelated_Script", "Outputs": {"result": f"Hello, {TOKEN}!"}},
            ],
            globals_map={"out_message": f"Hello, {TOKEN}!"},
        )
        with self.assertRaisesRegex(CheckFailure, "another node may be covering"):
            check_behavior.assert_row_provenance(self.row, self.process, variables_data, TOKEN)

    def test_invoking_node_never_executed_fails(self):
        variables_data = _variables_data(
            elements=[{"ElementId": "Unrelated_Script", "Outputs": {"result": f"Hello, {TOKEN}!"}}],
            globals_map={"out_message": f"Hello, {TOKEN}!"},
        )
        with self.assertRaisesRegex(CheckFailure, "produced no runtime Outputs"):
            check_behavior.assert_row_provenance(self.row, self.process, variables_data, TOKEN)

    def test_echo_resource_with_bpmn_side_transform_passes(self):
        """Vector 1, CORRECTED per explicit product direction: a hello-world
        API workflow that echoes its raw input, composed with a BPMN-side
        output mapping that embeds the token in a fixed string
        (`=js:'Hello, ' + result.message`), is the INTENDED shape, not a
        cheat -- the checker must not require the resource itself to have
        transformed the token. The invoking node's own runtime Outputs still
        carry the (untransformed) token, which is all assert_row_provenance
        requires of Outputs; the "Hello, " concatenation lives in the
        published global, not in Outputs, and is unaffected either way."""

        variables_data = _variables_data(
            elements=[
                {"ElementId": "Task_InvokeGreeting", "Outputs": {"response": {"message": TOKEN}}},
            ],
            globals_map={"out_message": f"Hello, {TOKEN}!"},
        )
        # Should not raise.
        check_behavior.assert_row_provenance(self.row, self.process, variables_data, TOKEN)

    def test_missing_wrapper_node_fails(self):
        no_wrapper = BEHAVIOR_BPMN.replace(
            '<uipath:type value="Orchestrator.ExecuteApiWorkflowAsync"/>',
            '<uipath:type value="Something.Else"/>',
        )
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.bpmn"
            path.write_text(no_wrapper, encoding="utf-8")
            process = composition.parse_process(path)
        variables_data = _variables_data(elements=[], globals_map={})
        with self.assertRaisesRegex(CheckFailure, "no serviceTask"):
            check_behavior.assert_row_provenance(self.row, process, variables_data, TOKEN)


class CompletedAssertionTests(unittest.TestCase):
    def test_completed_passes(self):
        check_behavior.assert_completed({"FinalStatus": "Completed", "ElementExecutions": []}, [])

    def test_faulted_fails_with_detail(self):
        debug_data = {
            "FinalStatus": "Faulted",
            "ElementExecutions": [{"ElementId": "Task_1", "Status": "Faulted"}],
        }
        with self.assertRaisesRegex(CheckFailure, "Faulted"):
            check_behavior.assert_completed(debug_data, [{"Message": "boom"}])


if __name__ == "__main__":
    unittest.main()

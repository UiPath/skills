#!/usr/bin/env python3
"""Offline unit tests for the API-workflow composition eval's checkers.

Runs in seconds, no live tenant calls: every resolver a real `uip` call would
back is injected here as a plain callable returning a fixture-matching
constant, exactly the way `check_shape.collect_shape_problems` is designed to
be called. Exercises:

  * composition.py's discovery + BPMN/.uipx parsing helpers.
  * check_shape.py's structural + cross-tenant shape rules, against the real
    gold fixture (must be clean) and the full fixtures/mutations/ corpus
    (each mutation must be rejected with a diagnosable reason; the one
    valid-but-unlike-gold fixture must be ACCEPTED, proving the checker is
    not overfit to gold's exact ids/ordering).
  * check_shape.assert_validate_clean, with a synthetic `validate` payload.
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
RELEASE_KEY_GOOD = "C6ABA92A-AEB1-47FD-ACFF-39D5FA1CE45F"
FOLDER_KEY_GOOD = "1efad159-0c94-46d7-ad7a-4bdd22b4720b"


def matching_resolvers():
    return dict(
        resolve_release_key_for_row=lambda row, project_dir: (lambda binding: RELEASE_KEY_GOOD),
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
        self.assert_rejected("wrong_target_output", "does not publish 'message'")

    def test_undeclared_var_read(self):
        self.assert_rejected("undeclared_var_read", "undeclared variable id")

    def test_empty_published_contract(self):
        problems = shape_problems(MUTATIONS / "empty_published_contract")
        joined = " | ".join(problems)
        self.assertIn("input does not publish", joined)
        self.assertIn("output does not publish 'message'", joined)


class ShapeCheckAcceptsUnlikeGoldTests(unittest.TestCase):
    def test_valid_unlike_gold_is_accepted(self):
        problems = shape_problems(MUTATIONS / "valid_unlike_gold")
        self.assertEqual(problems, [], f"a structurally-different-but-valid shape must pass, got: {problems}")


class ValidateCleanTests(unittest.TestCase):
    def test_valid_status_no_warnings_passes(self):
        payload = {"Data": {"Status": "Valid", "Warnings": []}}
        self.assertEqual(check_shape.assert_validate_clean(payload), [])

    def test_variable_not_set_alone_passes(self):
        # By construction: the node reading the start-event-scoped input.
        payload = {"Data": {"Status": "Valid", "Warnings": [{"Code": "VARIABLE_NOT_SET"}]}}
        self.assertEqual(check_shape.assert_validate_clean(payload), [])

    def test_variable_does_not_exist_fails(self):
        payload = {"Data": {"Status": "Valid", "Warnings": [{"Code": "VARIABLE_DOES_NOT_EXIST"}]}}
        problems = check_shape.assert_validate_clean(payload)
        self.assertTrue(any("VARIABLE_DOES_NOT_EXIST" in p for p in problems))

    def test_non_valid_status_fails(self):
        payload = {"Data": {"Status": "Invalid", "Warnings": []}}
        problems = check_shape.assert_validate_clean(payload)
        self.assertTrue(any("Status" in p for p in problems))


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

    def test_bare_token_global_fails(self):
        # Nothing computed: the global IS the token, verbatim.
        variables_data = _variables_data(
            elements=[{"ElementId": "Task_InvokeGreeting", "Outputs": {"response": {"message": TOKEN}}}],
            globals_map={"out_message": TOKEN},
        )
        with self.assertRaisesRegex(CheckFailure, "nothing was computed"):
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

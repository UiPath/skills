#!/usr/bin/env python3
"""`drive_case._is_transient`: which CLI refusals get another attempt.

A route that ends on the tenant carries no verdict about the build, and across nine
runs of the seven-route SDD eleven route verdicts were lost that way. A refusal that
names its reason must still fail on the first attempt: retrying a real one turns a
plan defect into a pass.
"""

from __future__ import annotations

import ast
import builtins
import contextlib
import importlib.util
import io
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "drive_case_under_test", Path(__file__).parent / "drive_case.py"
)
drive_case = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(drive_case)


class TransientMarkerTests(unittest.TestCase):
    def assert_retries(self, detail: str):
        self.assertTrue(drive_case._is_transient(detail), detail)

    def assert_fails_at_once(self, detail: str):
        self.assertFalse(drive_case._is_transient(detail), detail)

    def test_gateway_timeout_retries(self):
        self.assert_retries("Error listing tasks | unknown_error | Gateway Timeout")

    def test_service_unavailable_retries(self):
        self.assert_retries("Error listing tasks | unknown_error | Service Unavailable")

    def test_a_reasonless_listing_failure_retries(self):
        """`unknown_error` plus a content-free message is a service that could not
        answer. It ended a route on 34632357797 after the buyer stage was selected."""
        self.assert_retries("Error listing tasks | unknown_error | An error occurred")

    def test_an_expired_session_retries(self):
        """A 403 naming `authentication_required` is the tenant's session, never the
        plan. It cost four route verdicts across 34558832471 and 34613296008."""
        self.assert_retries(
            "Error getting instance | Forbidden | authentication_required | Status: 403 Forbidden"
        )
        self.assert_retries(
            "Error getting variables | Forbidden | authentication_required | Status: 403"
        )

    def test_a_named_refusal_fails_at_once(self):
        self.assert_fails_at_once(
            "Error listing tasks | invalid_argument | Folder does not exist or the user "
            "does not have access to the folder."
        )

    def test_a_plan_defect_fails_at_once(self):
        self.assert_fails_at_once(
            "Validation failed | invalid_argument | the caseplan is not valid"
        )

    def test_a_missing_resource_fails_at_once(self):
        self.assert_fails_at_once(
            "Error getting instance | not_found | No instance exists with that id"
        )


class PlatformIncidentTests(unittest.TestCase):
    """Which case incidents mean the route judges nothing.

    Across 17 runs the case recorded 27 incidents. Twenty-five name something the build
    wrote: empty inputs, an expression that dereferenced undefined, an Integration
    Services 400, a catalog the folder does not hold. Two do not.
    """

    @staticmethod
    def _incident(message: str) -> dict:
        return {"ElementId": "t1", "Code": 170002, "Message": message}

    def test_a_debug_task_creation_timeout_judges_nothing(self):
        """The outer sentence can also name a real defect, an app the folder does not
        hold, so the marker is the inner exception. Run 34679634976 lost its sendback
        route to it after the loop-back had already landed `BuyerDecision='sendback'`."""
        timed_out = (
            "Failed to create app task in debug mode using deployed app Supplier "
            "Application Validation in folder Shared/uipath-maestro-case/Supplier "
            "Application Validation, Inner exception: The request was canceled due to "
            "the configured HttpClient.Timeout of 30 seconds elapsing."
        )
        self.assertTrue(drive_case.incidents_are_all_platform([self._incident(timed_out)]))
        self.assertFalse(drive_case.incidents_are_all_platform([self._incident(
            "Failed to create app task in debug mode using deployed app X in folder Y"
        )]))

    def test_a_gateway_timeout_and_a_reset_connection_judge_nothing(self):
        """Both arrived on runs that had already driven their gates: 34712368518 lost
        `no-withdraw-in-setup` to the first, 34694445000 the same route to the second."""
        for message in (
            "AppTasks request failed with status GatewayTimeout. Response body could "
            "not be parsed: Unexpected character encountered",
            "upstream connect error or disconnect/reset before headers. retried and the "
            "latest reset reason: connection failure",
        ):
            self.assertTrue(
                drive_case.incidents_are_all_platform([self._incident(message)]), message
            )

    def test_a_service_fault_alone_judges_nothing(self):
        for message in ("HTTP Request Failed", "LLM model not available"):
            self.assertTrue(
                drive_case.incidents_are_all_platform([self._incident(message)]), message
            )

    def test_a_plan_defect_still_counts(self):
        for message in (
            "Input validation failed",
            "Error evaluating data expression: Worker operation failed",
            "Request to Integration Services failed with status code '400'",
            "No task catalog exists with name phase-escalation",
        ):
            self.assertFalse(
                drive_case.incidents_are_all_platform([self._incident(message)]), message
            )

    def test_one_plan_defect_among_service_faults_still_counts(self):
        self.assertFalse(drive_case.incidents_are_all_platform([
            self._incident("HTTP Request Failed"),
            self._incident("Input validation failed"),
        ]))

    def test_no_incident_is_not_a_service_fault(self):
        """A case that faulted with nothing recorded still has to fail on its own terms."""
        self.assertFalse(drive_case.incidents_are_all_platform([]))


class AlreadyCompletedTests(unittest.TestCase):
    """A write that landed and then answered with a transient marker.

    `envelope_retrying` sends a refused write again, and Orchestrator refuses the second
    attempt of a completion with `This Action is already completed by the same user`. Run
    34672482504's compliance-reject lost its first gate there.
    """

    def test_the_marker_is_recognised_whatever_the_casing(self):
        for detail in (
            "Error completing task '101524657' | This Action is already completed by the same user",
            "error completing task | this action is ALREADY COMPLETED BY THE SAME USER",
        ):
            self.assertIn(drive_case._ALREADY_COMPLETED, detail.lower(), detail)

    def test_a_real_completion_refusal_is_not_it(self):
        for detail in (
            "Error completing task | This action is no longer assigned to you",
            "Error completing task | The task is not in a state that allows completion",
        ):
            self.assertNotIn(drive_case._ALREADY_COMPLETED, detail.lower(), detail)


if __name__ == "__main__":
    unittest.main()


class InstanceAdoptionTests(unittest.TestCase):
    """`drive_case.appeared_since`: which new instance this route agrees to drive.

    Every suite imports a solution of the same name into one tenant, and `instance list` is
    tenant-wide. A sibling's instance can be the only new one in the window, so a count-based
    guard passes it through. That happened: 34712367241 and 34712365629 both drove
    2db00be8-20c0-4672-a099-1b7f5bd44591.
    """

    MINE = ["Stage_ERNFO3", "Stage_Q2YFKc"]
    THEIRS = ["Stage_kR3nQ7", "Stage_pL8xM2"]

    def setUp(self):
        drive_case._FOREIGN_INSTANCES.clear()
        drive_case.CASE_FOLDER_KEY = ""
        self.addCleanup(drive_case._FOREIGN_INSTANCES.clear)

    def arrange(self, listing: dict, stages_by_instance: dict):
        drive_case.plan_nodes = lambda: [
            {"id": sid, "type": "case-management:Stage"} for sid in self.MINE
        ]
        drive_case.instance_ids = lambda: listing
        drive_case.executions = lambda iid, folder="": [
            {"ElementId": sid, "ElementType": "CaseStage"}
            for sid in stages_by_instance.get(iid, [])
        ]

    def test_adopts_the_instance_running_this_build(self):
        self.arrange({"ours": "folder-a"}, {"ours": self.MINE})
        self.assertEqual(drive_case.appeared_since({}), "ours")
        self.assertEqual(drive_case.CASE_FOLDER_KEY, "folder-a")

    def test_skips_a_sibling_suites_instance_even_when_it_is_the_only_new_one(self):
        self.arrange({"theirs": "folder-b"}, {"theirs": self.THEIRS})
        self.assertEqual(drive_case.appeared_since({}), "")
        self.assertIn("theirs", drive_case._FOREIGN_INSTANCES)

    def test_an_instance_with_no_stage_rows_yet_is_undecided(self):
        self.arrange({"young": "folder-c"}, {})
        self.assertEqual(drive_case.appeared_since({}), "")
        self.assertNotIn("young", drive_case._FOREIGN_INSTANCES)

    def test_picks_ours_out_of_a_pair_that_appeared_together(self):
        self.arrange({"theirs": "folder-b", "ours": "folder-a"},
                     {"theirs": self.THEIRS, "ours": self.MINE})
        self.assertEqual(drive_case.appeared_since({}), "ours")

    def test_an_instance_present_before_debug_is_not_a_candidate(self):
        self.arrange({"ours": "folder-a"}, {"ours": self.MINE})
        self.assertEqual(drive_case.appeared_since({"ours": "folder-a"}), "")


class AttemptCountTests(unittest.TestCase):
    """`drive_case.envelope_retrying` records how many attempts a write took.

    `complete_gate` needs it to read "already completed by the same user". Our own resent
    write and another driver's completion carry the same message, because every suite drives
    as one bot identity. Only the attempt count separates them.
    """

    def setUp(self):
        self.real_envelope = drive_case.envelope
        self.real_sleep = drive_case.time.sleep
        drive_case.time.sleep = lambda _s: None
        self.addCleanup(setattr, drive_case, "envelope", self.real_envelope)
        self.addCleanup(setattr, drive_case.time, "sleep", self.real_sleep)

    def replies(self, *seq):
        it = iter(seq)
        drive_case.envelope = lambda args, timeout=120: next(it)

    def test_a_write_that_lands_first_time_counts_one(self):
        self.replies({"Result": "Success"})
        self.assertEqual(drive_case.envelope_retrying(["uip", "tasks", "complete"])["_Attempts"], 1)

    def test_a_refusal_on_the_first_attempt_counts_one(self):
        self.replies({"Result": "Failure", "Message": "already completed by the same user"})
        self.assertEqual(drive_case.envelope_retrying(["uip", "tasks", "complete"])["_Attempts"], 1)

    def test_a_transient_then_success_counts_two(self):
        self.replies({"Result": "Failure", "Message": "Gateway Timeout"},
                     {"Result": "Success"})
        self.assertEqual(drive_case.envelope_retrying(["uip", "tasks", "complete"])["_Attempts"], 2)

    def test_a_resent_write_refused_as_already_completed_counts_two(self):
        self.replies({"Result": "Failure", "Message": "Gateway Timeout"},
                     {"Result": "Failure", "Message": "already completed by the same user"})
        self.assertEqual(drive_case.envelope_retrying(["uip", "tasks", "complete"])["_Attempts"], 2)


class CancellationDiagnosisTests(unittest.TestCase):
    """`drive_case.fail_with_diagnosis` on a case that ended with no incident.

    Sixteen routes have died that way and the artifact never said where. This is the last
    moment the instance can be asked: post_run deletes it with the solution. The path only
    runs when a route fails, so nothing else exercises it.
    """

    def setUp(self):
        self.saved = {name: getattr(drive_case, name)
                      for name in ("run_status", "incidents", "executions", "run_checked")}
        self.addCleanup(
            lambda: [setattr(drive_case, k, v) for k, v in self.saved.items()])
        drive_case.run_status = lambda instance: "Cancelled"
        drive_case.incidents = lambda instance: []
        drive_case.executions = lambda instance, folder="": [
            {"ElementType": "CaseStage", "ElementId": "Stage_A",
             "ElementRuns": [{"Status": "InProgress"}, {"Status": "Completed"}]},
            {"ElementType": "CaseTask", "ElementId": "tBuyer1",
             "ElementRuns": [{"Status": "Completed"}]},
        ]
        # Stubbed at the CLI boundary, in the shape `instance variables` actually answers:
        # the values sit under `Globals`. Stubbing the driver's own reader instead is how
        # the first version of this test passed while the code read the top level and
        # printed an empty dict on the first real cancellation it ran on.
        drive_case.run_checked = lambda args, timeout=120: {
            "InstanceId": "abc-123",
            "Globals": {"BuyerDecision": "reject", "ComplianceDecision": None,
                        "CaseOutcome": ""}}

    def diagnose(self) -> str:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit):
                drive_case.fail_with_diagnosis("abc-123", "the case ended 'Cancelled'")
        return out.getvalue()

    def test_names_the_last_elements_and_how_often_each_ran(self):
        printed = self.diagnose()
        self.assertIn("CaseStage Stage_A 2 run(s), last 'Completed'", printed)
        self.assertIn("CaseTask tBuyer1 1 run(s), last 'Completed'", printed)

    def test_prints_the_decision_variables_the_case_held(self):
        """`BuyerDecision` is what the rejection lane's guard reads, so whether it landed
        is the first thing to know about a case that died at the buyer stage."""
        printed = self.diagnose()
        self.assertIn("decision variables at the end:", printed)
        self.assertIn("'BuyerDecision': 'reject'", printed)

    def test_still_reports_the_stages_and_the_run_status(self):
        printed = self.diagnose()
        self.assertIn("run status 'Cancelled'", printed)
        self.assertIn("no incident; the case reached stages ['Stage_A']", printed)


class ElementRunReadingTests(unittest.TestCase):
    """Two readings of `element-executions` that have each been wrong once."""

    def setUp(self):
        self.saved = {n: getattr(drive_case, n) for n in ("executions", "plan_nodes")}
        self.addCleanup(
            lambda: [setattr(drive_case, k, v) for k, v in self.saved.items()])

    def test_a_single_visit_writes_two_element_runs(self):
        """One visit writes `InProgress` then `Completed`, so 2 is one visit and 4 is a
        return. Reading the count as visits is how the sendback assertion passed on a case
        that was never sent back."""
        drive_case.plan_nodes = lambda: [
            {"id": "Stage_A", "type": "case-management:Stage", "data": {"label": "Buyer review"}}]
        drive_case.executions = lambda instance, folder="": [
            {"ElementId": "Stage_A", "ElementType": "CaseStage",
             "ElementRuns": [{"Status": "InProgress"}, {"Status": "Completed"}]}]
        self.assertEqual(drive_case.stage_runs("i", "Buyer review"), 2)

    def test_a_second_visit_adds_two_more(self):
        drive_case.plan_nodes = lambda: [
            {"id": "Stage_A", "type": "case-management:Stage", "data": {"label": "Buyer review"}}]
        drive_case.executions = lambda instance, folder="": [
            {"ElementId": "Stage_A", "ElementType": "CaseStage",
             "ElementRuns": [{"Status": "InProgress"}, {"Status": "Completed"},
                             {"Status": "InProgress"}, {"Status": "Completed"}]}]
        self.assertEqual(drive_case.stage_runs("i", "Buyer review"), 4)

    def test_a_stage_never_reached_reads_zero(self):
        drive_case.plan_nodes = lambda: [
            {"id": "Stage_A", "type": "case-management:Stage", "data": {"label": "Buyer review"}}]
        drive_case.executions = lambda instance, folder="": []
        self.assertEqual(drive_case.stage_runs("i", "Buyer review"), 0)

    def test_a_second_selection_is_answered_as_well_as_the_first(self):
        """A sendback's second visit carries its own `ElementRunId`. Without keying on it
        the second looks like the first, is skipped, and the case waits forever."""
        drive_case.executions = lambda instance, folder="": [
            {"ElementId": "CaseWaitForUser_StageSelection_Stage_A",
             "ElementRuns": [{"Status": "Completed", "ElementRunId": "r1"},
                             {"Status": "InProgress", "ElementRunId": "r2"}]}]
        answered = set()
        self.assertEqual(drive_case.waiting_selection("i", answered), "Stage_A")
        self.assertIn("r2", answered)
        self.assertIsNone(drive_case.waiting_selection("i", answered))

    def test_an_element_not_waiting_is_not_offered(self):
        drive_case.executions = lambda instance, folder="": [
            {"ElementId": "CaseWaitForUser_StageSelection_Stage_A",
             "ElementRuns": [{"Status": "Completed", "ElementRunId": "r1"}]}]
        self.assertIsNone(drive_case.waiting_selection("i", set()))


class IncidentDescriptionTests(unittest.TestCase):
    """`drive_case.describe_incident` keeps both ends of a long message.

    A rules-evaluation failure reads `Failed to evaluate expression <the whole rule>:
    <the reason>`, so the reason sits at the end. Printing only the head shows the rule
    and cuts off the sentence that says what went wrong.
    """

    def test_a_long_message_keeps_its_tail(self):
        tail = "the reason it actually failed"
        item = {"ElementId": "tX", "ErrorCode": 102003,
                "ErrorDetails": "head " + ("x" * 900) + " " + tail}
        described = drive_case.describe_incident(item)
        self.assertIn("head", described)
        self.assertIn(tail, described)
        self.assertIn("chars]...", described)

    def test_a_short_message_is_untouched(self):
        item = {"ElementId": "tX", "ErrorCode": 1, "ErrorMessage": "Input validation failed"}
        self.assertEqual(drive_case.describe_incident(item),
                         "'tX' (1): Input validation failed")

    def test_it_reads_whichever_field_carries_the_text(self):
        for field in ("ErrorDetails", "ErrorMessage", "Message"):
            with self.subTest(field=field):
                described = drive_case.describe_incident(
                    {"ElementId": "tX", "ErrorCode": 7, field: "something went wrong"})
                self.assertIn("something went wrong", described)


class ImportRetryTests(unittest.TestCase):
    """`drive_case._import_is_retryable`: which refused import gets a second `case debug`.

    Run 34729813548's `onboard` route died at the import and carried no verdict. The CLI's
    own answer named the remedy and nothing was reading it:

        "Message": "Failed during import-solution: HTTP 503 on POST .../Solution/Import"
        "ErrorCode": "server_error"
        "Retry": "RetryLater"
    """

    REAL = """{
      "Result": "Failure",
      "Message": "Failed during import-solution: HTTP 503 on POST /codereval/studio_/backend/api/Solution/Import",
      "Context": { "HttpStatus": 503, "Stage": "import-solution", "Method": "POST" },
      "ErrorCode": "server_error",
      "Retry": "RetryLater"
    }"""

    def test_the_run_that_lost_a_route_retries(self):
        self.assertTrue(drive_case._import_is_retryable(self.REAL))

    def test_retrylater_alone_is_enough(self):
        self.assertTrue(drive_case._import_is_retryable('{"Retry": "RetryLater"}'))

    def test_a_five_hundred_at_import_retries_without_the_hint(self):
        for code in (500, 502, 503, 504):
            with self.subTest(code=code):
                self.assertTrue(drive_case._import_is_retryable(
                    '{"Context": {"HttpStatus": %d, "Stage": "import-solution"}}' % code))

    def test_a_four_hundred_at_import_does_not(self):
        """A refused package is the build's, and retrying it hides a real defect."""
        self.assertFalse(drive_case._import_is_retryable(
            '{"Context": {"HttpStatus": 400, "Stage": "import-solution"}}'))

    def test_a_five_hundred_somewhere_else_does_not(self):
        self.assertFalse(drive_case._import_is_retryable(
            '{"Context": {"HttpStatus": 503, "Stage": "publish-process"}}'))

    def test_ordinary_debug_output_does_not(self):
        self.assertFalse(drive_case._import_is_retryable(
            "Starting Studio Web debug session for: SupplierOnboarding/SupplierOnboarding"))


class UndefinedNameTests(unittest.TestCase):
    """No function loads a name nothing in its scope or the module defines.

    `main` is never executed by this suite, and `ast.parse` accepts a file that reads an
    undefined name, so a refactor can ship a `NameError` with every test green. Extracting
    the `case debug` session into a helper left `main` still referring to its local
    `debug`, and run 34771121384 lost all seven routes to
    `NameError: name 'debug' is not defined` after each had driven its case to the end.
    """

    def loaded_but_undefined(self, path) -> dict:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        module = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        for node in tree.body:
            if isinstance(node, ast.Assign):
                module |= {t.id for t in node.targets if isinstance(t, ast.Name)}
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                module.add(node.target.id)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                module |= {a.asname or a.name.split(".")[0] for a in node.names}
        out = {}
        for fn in [n for n in tree.body if isinstance(n, ast.FunctionDef)]:
            local = {a.arg for a in fn.args.args} | {a.arg for a in fn.args.kwonlyargs}
            for node in ast.walk(fn):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    local.add(node.id)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    local.add(node.name)
                elif isinstance(node, ast.ExceptHandler) and node.name:
                    local.add(node.name)
                elif isinstance(node, ast.arg):
                    local.add(node.arg)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    local |= {a.asname or a.name.split(".")[0] for a in node.names}
            used = {n.id for n in ast.walk(fn)
                    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
            missing = sorted(used - local - module - set(dir(builtins)))
            if missing:
                out[fn.name] = missing
        return out

    def test_every_task_module_resolves_its_names(self):
        here = Path(__file__).parent
        checked = 0
        for path in sorted(here.glob("*.py")):
            if path.name.startswith("test_"):
                continue
            checked += 1
            with self.subTest(module=path.name):
                self.assertEqual(self.loaded_but_undefined(path), {})
        self.assertGreater(checked, 5, "expected the task's own modules to be found")

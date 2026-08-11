#!/usr/bin/env python3
"""Behavioral matrix for the reachability / run-once regression graders.

Covers the two sdd.md checkers (picker pairing, deterministic reject route) and
the JMESPath assertions the two caseplan-emit tasks grade with. Every grader is
exercised against a compliant artifact AND against each regression it exists to
catch, so a grader that silently passes everything fails here first.

Runs with no model and no tenant:

    python3 tests/tasks/uipath-maestro-case/_shared/test_reentry_reachability_checks.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parents[1]
PICKER_CHECK = CASE_ROOT / "phase_0_finalize_draft_picker" / "check_picker_pairing.py"
REJECT_CHECK = CASE_ROOT / "phase_0_finalize_draft_reject" / "check_reject_route.py"
ADD_TASK_YAML = CASE_ROOT / "edit" / "add_task_run_once_default" / "add_task_run_once_default.yaml"
ENVELOPE_YAML = CASE_ROOT / "single_node" / "run_once_envelope" / "run_once_envelope.yaml"
LINEAR_FIXTURE = (
    CASE_ROOT / "edit" / "templates" / "LinearThreeStages" / "LinearThreeStages" / "caseplan.json"
)


# --------------------------------------------------------------------------
# sdd.md builders
# --------------------------------------------------------------------------

def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def stage(
    label: str,
    entry: list[list[str]],
    exits: list[list[str]],
    *,
    secondary: bool = False,
    rationale: str = "",
    display_name_column: bool = False,
) -> str:
    heading = f"### Secondary Stage: {label}" if secondary else f"### Stage 1: {label}"
    entry_headers = ["WHEN", "IF", "Interrupting"]
    exit_headers = ["WHEN", "IF", "Exit Type", "Marks Stage Complete"]
    if display_name_column:
        exit_headers.append("Display Name")
        exits = [row + ["—"] for row in exits]
    return "\n\n".join(
        [
            heading,
            f"**Type:** {'Secondary Stage' if secondary else 'Stage'}",
            f"**Description:** {label} stage.",
            f"**Design Rationale:** {rationale or f'{label} routing.'}",
            "#### Stage Entry Conditions",
            table(entry_headers, entry),
            "#### Stage Exit Conditions",
            table(exit_headers, exits),
            "",
        ]
    )


COMPLETION_EXIT = ["`required-tasks-completed`", "—", "exit-only", "Yes"]
PICKER_ENTRY = ["`user-selected-stage`", "—", "Yes"]
WAIT_FOR_USER_EXIT = ["`required-tasks-completed`", "—", "wait-for-user", "Yes"]


def picker_sdd(
    *,
    document_exits: list[list[str]] | None = None,
    upstream_exits: list[list[str]] | None = None,
    lane_entry: list[list[str]] | None = None,
    lane_exits: list[list[str]] | None = None,
    lane_rationale: str = "",
    include_lane: bool = True,
) -> str:
    parts = [
        "# SDD — VendorOnboarding\n",
        "## Section 2: Stages & Tasks\n",
        stage(
            "Document Collection",
            [["`case-entered`", "—", "No"]],
            document_exits or [COMPLETION_EXIT],
        ),
        stage("Vendor Approval", [["`case-entered`", "—", "No"]], upstream_exits or [COMPLETION_EXIT]),
    ]
    if include_lane:
        parts.append(
            stage(
                "Compliance Hold",
                lane_entry or [PICKER_ENTRY],
                lane_exits or [["`required-tasks-completed`", "—", "return-to-origin", "Yes"]],
                secondary=True,
                rationale=lane_rationale,
            )
        )
    return "\n".join(parts)


REJECT_ENTRY = [
    '`selected-stage-exited("Eligibility Review")`',
    '`=js:(vars.reviewDecision === "Reject")`',
    "Yes",
]
DIVERTING_EXIT = [
    '`selected-tasks-completed("Reviewer Decision")`',
    '`=js:(vars.reviewDecision === "Reject")`',
    "exit-only",
    "No",
]
GATED_COMPLETION = [
    "`required-tasks-completed`",
    '`=js:(vars.reviewDecision !== "Reject")`',
    "exit-only",
    "Yes",
]


def reject_sdd(
    *,
    origin_exits: list[list[str]] | None = None,
    lane_entry: list[list[str]] | None = None,
    origin_rationale: str = "",
    display_name_column: bool = False,
) -> str:
    return "\n".join(
        [
            "# SDD — GrantReview\n",
            "## Section 2: Stages & Tasks\n",
            stage(
                "Eligibility Review",
                [["`case-entered`", "—", "No"]],
                origin_exits or [DIVERTING_EXIT, GATED_COMPLETION],
                rationale=origin_rationale,
                display_name_column=display_name_column,
            ),
            stage(
                "Application Rejected",
                lane_entry or [REJECT_ENTRY],
                [COMPLETION_EXIT],
                secondary=True,
                display_name_column=display_name_column,
            ),
        ]
    )


def run_check(script: Path, sdd_text: str, *args: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as workdir:
        (Path(workdir) / "sdd.md").write_text(sdd_text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(script), *args],
            cwd=workdir,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )


class SharedParserTest(unittest.TestCase):
    """Direct cover for the shared parser. Real SDDs carry `###` headings that are not
    stages (`### Case Metadata`, `### Case Variables`) — the graders' fixtures alone never
    exercise them."""

    def setUp(self) -> None:
        sys.path.insert(0, str(CASE_ROOT))
        from _shared import entry_rule_check  # noqa: PLC0415

        self.mod = entry_rule_check

    def test_section_one_headings_are_not_parsed_as_stages(self) -> None:
        text = "\n\n".join(
            [
                "## Section 1: Case Definition",
                "### Case Metadata",
                table(["Property", "Value"], [["Case Name", "VendorOnboarding"]]),
                "### Case Variables",
                table(["Variable", "Type"], [["vendorName", "String"]]),
                "## Section 2: Stages & Tasks",
                stage("Vendor Approval", [["`case-entered`", "—", "No"]], [COMPLETION_EXIT]),
            ]
        )
        self.assertEqual(list(self.mod.stage_blocks(text)), ["Vendor Approval"])

    def test_a_non_stage_heading_terminates_the_previous_stage_block(self) -> None:
        text = "\n\n".join(
            [
                stage("Vendor Approval", [["`case-entered`", "—", "No"]], [COMPLETION_EXIT]),
                "### Personas",
                table(
                    ["WHEN", "IF", "Exit Type", "Marks Stage Complete"],
                    [["`required-tasks-completed`", "—", "wait-for-user", "No"]],
                ),
            ]
        )
        block = self.mod.stage_blocks(text)["Vendor Approval"]
        self.assertNotIn("wait-for-user", block)

    def test_stage_kind_reads_the_heading_qualifier(self) -> None:
        blocks = self.mod.stage_blocks(
            "\n\n".join(
                [
                    stage("Vendor Approval", [["`case-entered`", "—", "No"]], [COMPLETION_EXIT]),
                    stage(
                        "Compliance Hold", [PICKER_ENTRY], [COMPLETION_EXIT], secondary=True
                    ),
                    "### Exception Stage: Payment Failure",
                    "**Type:** Exception Stage",
                ]
            )
        )
        kinds = {label: self.mod.stage_kind(body) for label, body in blocks.items()}
        self.assertEqual(kinds["Vendor Approval"], "primary")
        self.assertEqual(kinds["Compliance Hold"], "secondary")
        self.assertEqual(kinds["Payment Failure"], "exception")

    def test_exact_header_wins_over_a_substring_match(self) -> None:
        # "notify" contains "if" — substring-first would return the wrong column.
        row = {"notify": "owner@example.com", "when": "`case-entered`", "if": "=js:vars.x"}
        self.assertEqual(self.mod.column(row, "if"), "=js:vars.x")


class PickerPairingCheckTest(unittest.TestCase):
    def assert_pass(self, sdd_text: str) -> None:
        result = run_check(PICKER_CHECK, sdd_text)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_fail(self, sdd_text: str, expected: str) -> None:
        result = run_check(PICKER_CHECK, sdd_text)
        self.assertNotEqual(result.returncode, 0, "grader accepted a regression")
        self.assertIn(expected, (result.stdout + result.stderr).lower())

    def test_accepts_picker_entry_exposed_from_every_primary_stage(self) -> None:
        self.assert_pass(
            picker_sdd(
                document_exits=[WAIT_FOR_USER_EXIT],
                upstream_exits=[WAIT_FOR_USER_EXIT],
            )
        )

    def test_rejects_picker_entry_with_no_wait_for_user_anywhere(self) -> None:
        self.assert_fail(picker_sdd(), "wait-for-user")

    def test_rejects_wait_for_user_declared_only_on_the_lane_itself(self) -> None:
        self.assert_fail(
            picker_sdd(lane_exits=[WAIT_FOR_USER_EXIT]),
            "wait-for-user",
        )

    def test_rejects_lane_rekeyed_off_the_picker(self) -> None:
        self.assert_fail(
            picker_sdd(
                upstream_exits=[COMPLETION_EXIT, WAIT_FOR_USER_EXIT],
                lane_entry=[['`selected-stage-completed("Vendor Approval")`', "—", "Yes"]],
            ),
            "user-selected-stage",
        )

    def test_rejects_non_interrupting_picker_entry(self) -> None:
        self.assert_fail(
            picker_sdd(
                upstream_exits=[COMPLETION_EXIT, WAIT_FOR_USER_EXIT],
                lane_entry=[["`user-selected-stage`", "—", "No"]],
            ),
            "interrupting",
        )

    def test_rejects_missing_lane(self) -> None:
        self.assert_fail(picker_sdd(include_lane=False), "compliance hold")

    def test_wait_for_user_on_an_exception_lane_does_not_expose_the_picker_lane(self) -> None:
        # An `### Exception Stage:` heading must terminate the preceding stage's block. If it
        # does not, its exit table is graded as the previous stage's own and a document whose
        # only wait-for-user sits on an exception lane passes — naming the wrong stage.
        sdd_text = "\n\n".join(
            [
                "# SDD — VendorOnboarding",
                "## Section 2: Stages & Tasks",
                stage(
                    "Document Collection",
                    [["`case-entered`", "—", "No"]],
                    [COMPLETION_EXIT],
                ),
                "### Stage 1: Vendor Approval",
                "**Type:** Stage",
                "#### Stage Entry Conditions",
                table(["WHEN", "IF", "Interrupting"], [["`case-entered`", "—", "No"]]),
                "### Exception Stage: Payment Failure",
                "**Type:** Exception Stage",
                "#### Stage Exit Conditions",
                table(
                    ["WHEN", "IF", "Exit Type", "Marks Stage Complete"],
                    [["`required-tasks-completed`", "—", "wait-for-user", "No"]],
                ),
                stage(
                    "Compliance Hold",
                    [PICKER_ENTRY],
                    [["`required-tasks-completed`", "—", "return-to-origin", "Yes"]],
                    secondary=True,
                ),
            ]
        )
        self.assert_fail(sdd_text, "wait-for-user")

    def test_missing_entry_table_is_not_read_off_the_following_table(self) -> None:
        # A stage whose condition section has no table must read as absent, not silently pick up
        # the next table in the block (the Tasks table) as if those rows were entry rules.
        sdd_text = "\n\n".join(
            [
                "# SDD — VendorOnboarding",
                "## Section 2: Stages & Tasks",
                stage(
                    "Vendor Approval",
                    [["`case-entered`", "—", "No"]],
                    [COMPLETION_EXIT, WAIT_FOR_USER_EXIT],
                ),
                "### Secondary Stage: Compliance Hold",
                "**Type:** Secondary Stage",
                "#### Stage Entry Conditions",
                "#### Tasks",
                table(
                    ["#", "Task Name", "Type", "Required"],
                    [["1", "Compliance Review", "action", "Yes"]],
                ),
            ]
        )
        self.assert_fail(sdd_text, "no stage entry conditions table")

    def test_rationale_prose_naming_wait_for_user_is_not_an_authored_exit(self) -> None:
        self.assert_fail(
            picker_sdd(lane_rationale="Entered from the picker; a wait-for-user exit exposes it."),
            "wait-for-user",
        )


class RejectRouteCheckTest(unittest.TestCase):
    def assert_pass(self, sdd_text: str) -> None:
        result = run_check(REJECT_CHECK, sdd_text)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_fail(self, sdd_text: str, expected: str) -> None:
        result = run_check(REJECT_CHECK, sdd_text)
        self.assertNotEqual(result.returncode, 0, "grader accepted a regression")
        self.assertIn(expected, (result.stdout + result.stderr).lower())

    def test_accepts_decision_keyed_lane_with_mutually_exclusive_origin_exits(self) -> None:
        self.assert_pass(reject_sdd())

    def test_accepts_selected_stage_completed_variant(self) -> None:
        self.assert_pass(
            reject_sdd(
                lane_entry=[
                    [
                        '`selected-stage-completed("Eligibility Review")`',
                        '`=js:(vars.reviewDecision === "Reject")`',
                        "Yes",
                    ]
                ]
            )
        )

    def test_accepts_condition_tables_carrying_the_display_name_column(self) -> None:
        self.assert_pass(reject_sdd(display_name_column=True))

    def test_rejects_picker_entry_on_a_deterministic_route(self) -> None:
        # Match the picker verdict specifically. "user-selected-stage" alone also appears in the
        # not-decision-keyed verdict's dump of authored rows, so it would pass for the wrong reason.
        self.assert_fail(reject_sdd(lane_entry=[PICKER_ENTRY]), "picker rule cannot carry")

    def test_rejects_decision_keyed_entry_with_no_guard(self) -> None:
        self.assert_fail(
            reject_sdd(lane_entry=[['`selected-stage-exited("Eligibility Review")`', "—", "Yes"]]),
            "keyed on the decision",
        )

    def test_rejects_entry_guarded_on_the_wrong_value(self) -> None:
        self.assert_fail(
            reject_sdd(
                lane_entry=[
                    [
                        '`selected-stage-exited("Eligibility Review")`',
                        '`=js:(vars.reviewDecision === "Approve")`',
                        "Yes",
                    ]
                ]
            ),
            "keyed on the decision",
        )

    def test_rejects_missing_origin_diverting_exit(self) -> None:
        self.assert_fail(reject_sdd(origin_exits=[GATED_COMPLETION]), "diverting exit")

    def test_rejects_ungated_origin_completion_exit(self) -> None:
        self.assert_fail(
            reject_sdd(origin_exits=[DIVERTING_EXIT, COMPLETION_EXIT]),
            "complement",
        )

    # -- guard polarity: a token test alone accepts the exact inverse of the route ----------

    def test_rejects_lane_entry_guarded_on_the_negated_reject(self) -> None:
        self.assert_fail(
            reject_sdd(
                lane_entry=[
                    [
                        '`selected-stage-exited("Eligibility Review")`',
                        '`=js:(vars.reviewDecision !== "Reject")`',
                        "Yes",
                    ]
                ]
            ),
            "keyed on the decision",
        )

    def test_rejects_diverting_exit_guarded_on_the_negated_reject(self) -> None:
        negated = [
            '`selected-tasks-completed("Reviewer Decision")`',
            '`=js:(vars.reviewDecision !== "Reject")`',
            "exit-only",
            "No",
        ]
        self.assert_fail(reject_sdd(origin_exits=[negated, GATED_COMPLETION]), "diverting exit")

    def test_rejects_completion_repeating_the_diverting_guard(self) -> None:
        same_as_diverting = [
            "`required-tasks-completed`",
            '`=js:(vars.reviewDecision === "Reject")`',
            "exit-only",
            "Yes",
        ]
        self.assert_fail(
            reject_sdd(origin_exits=[DIVERTING_EXIT, same_as_diverting]), "complement"
        )

    def test_accepts_completion_gated_on_the_positive_approve_value(self) -> None:
        approve = [
            "`required-tasks-completed`",
            '`=js:(vars.reviewDecision === "Approve")`',
            "exit-only",
            "Yes",
        ]
        self.assert_pass(reject_sdd(origin_exits=[DIVERTING_EXIT, approve]))

    # -- scope flag ------------------------------------------------------------------------

    def test_lane_scope_ignores_a_missing_origin_diverting_exit(self) -> None:
        result = run_check(REJECT_CHECK, reject_sdd(origin_exits=[COMPLETION_EXIT]), "--scope", "lane")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_origin_scope_still_catches_the_missing_diverting_exit(self) -> None:
        result = run_check(
            REJECT_CHECK, reject_sdd(origin_exits=[COMPLETION_EXIT]), "--scope", "origin"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("diverting exit", (result.stdout + result.stderr).lower())

    def test_unknown_scope_is_rejected(self) -> None:
        result = run_check(REJECT_CHECK, reject_sdd(), "--scope", "everything")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid choice", (result.stdout + result.stderr).lower())

    def test_rationale_prose_naming_the_anti_pattern_does_not_fail_a_correct_design(self) -> None:
        self.assert_pass(
            reject_sdd(
                origin_rationale=(
                    "Routed from the decision fact rather than `user-selected-stage`, "
                    "which is the picker rule and cannot carry a deterministic route."
                )
            )
        )


# --------------------------------------------------------------------------
# JMESPath assertions embedded in the two caseplan-emit task YAMLs
# --------------------------------------------------------------------------

def load_expressions(task_yaml: Path, *, advisory: bool = False) -> list[tuple[str, object]]:
    """Assertions from the task's json_check criteria.

    Gating criteria (pass_threshold > 0) and advisory ones (pass_threshold == 0) are
    loaded separately — mixing them would let an advisory miss read as a gate failure.
    """
    import yaml  # noqa: PLC0415 — optional dependency, guarded by skipUnless

    spec = yaml.safe_load(task_yaml.read_text(encoding="utf-8"))
    out: list[tuple[str, object]] = []
    for criterion in spec["success_criteria"]:
        if criterion.get("type") != "json_check":
            continue
        is_advisory = float(criterion.get("pass_threshold", 1.0)) == 0
        if is_advisory != advisory:
            continue
        for assertion in criterion["assertions"]:
            out.append((assertion["expression"], assertion["expected"]))
    return out


# `None` means the key is omitted entirely — what a run actually produced for the
# unspecified SDD row, and the reason the gate gred on behavior rather than serialization.
def timer_task(name: str, run_once: bool | None) -> dict:
    # Deterministic id — hash() is salted per process, so ids would differ every run.
    task = {
        "id": "t" + re.sub(r"[^a-z0-9]", "", name.lower())[:8],
        "type": "wait-for-timer",
        "displayName": name,
        "isRequired": False,
        "data": {"timerType": "timeDuration", "timeDuration": "PT10M"},
    }
    if run_once is not None:
        task["shouldRunOnlyOnce"] = run_once
    return task


def _dependencies_present() -> bool:
    try:
        import jmespath  # noqa: F401,PLC0415
        import yaml  # noqa: F401,PLC0415
    except ImportError:
        return False
    return True


@unittest.skipUnless(_dependencies_present(), "requires jmespath and PyYAML")
class TaskYamlAssertionTest(unittest.TestCase):
    """The two emit tasks grade with JMESPath only — a typo there grades nothing."""

    def evaluate(self, task_yaml: Path, plan: dict, *, advisory: bool = False) -> list[bool]:
        import jmespath  # noqa: PLC0415

        return [
            jmespath.search(expression, plan) == expected
            for expression, expected in load_expressions(task_yaml, advisory=advisory)
        ]

    # -- add_task_run_once_default -----------------------------------------

    def linear_plan(self, new_task_run_once: bool | None, *, added: bool = True) -> dict:
        """`added=False` omits the task entirely; `new_task_run_once=None` adds it with no
        `shouldRunOnlyOnce` key. The two are different failures and must not be conflated."""
        plan = json.loads(LINEAR_FIXTURE.read_text(encoding="utf-8"))
        if added:
            review = next(n for n in plan["nodes"] if (n.get("data") or {}).get("label") == "Review")
            review["data"]["tasks"].append([timer_task("Second Reminder", new_task_run_once)])
        return plan

    def test_add_task_assertions_pass_on_the_default_false_emit(self) -> None:
        self.assertTrue(all(self.evaluate(ADD_TASK_YAML, self.linear_plan(False))))

    def test_add_task_assertions_fail_on_the_stale_true_default(self) -> None:
        self.assertFalse(all(self.evaluate(ADD_TASK_YAML, self.linear_plan(True))))

    def test_add_task_assertions_fail_when_the_task_was_never_added(self) -> None:
        self.assertFalse(all(self.evaluate(ADD_TASK_YAML, self.linear_plan(False, added=False))))

    def test_add_task_assertions_fail_when_an_existing_flag_is_flipped(self) -> None:
        plan = self.linear_plan(False)
        review = next(n for n in plan["nodes"] if (n.get("data") or {}).get("label") == "Review")
        for lane in review["data"]["tasks"]:
            for task in lane:
                if task["displayName"] == "Hold For 1 Hour":
                    task["shouldRunOnlyOnce"] = False
        self.assertFalse(all(self.evaluate(ADD_TASK_YAML, plan)))

    # -- run_once_envelope -------------------------------------------------

    def envelope_plan(
        self, freeze: bool | None, reminder: bool | None, escalation: bool | None
    ) -> dict:
        return {
            "nodes": [
                {
                    "id": "Stage_hold",
                    "type": "case-management:Stage",
                    "data": {
                        "label": "Hold",
                        "tasks": [
                            [timer_task("Freeze Snapshot", freeze)],
                            [timer_task("Reminder Ping", reminder)],
                            [timer_task("Escalation Hold", escalation)],
                        ],
                    },
                }
            ]
        }

    def test_envelope_assertions_pass_when_the_sdd_is_honored(self) -> None:
        plan = self.envelope_plan(freeze=True, reminder=False, escalation=False)
        self.assertTrue(all(self.evaluate(ENVELOPE_YAML, plan)))

    def test_envelope_assertions_fail_on_the_stale_true_default(self) -> None:
        plan = self.envelope_plan(freeze=True, reminder=False, escalation=True)
        self.assertFalse(all(self.evaluate(ENVELOPE_YAML, plan)))

    def test_envelope_assertions_fail_on_a_blanket_flip_to_false(self) -> None:
        plan = self.envelope_plan(freeze=False, reminder=False, escalation=False)
        self.assertFalse(all(self.evaluate(ENVELOPE_YAML, plan)))

    def test_envelope_assertions_fail_on_a_blanket_flip_to_true(self) -> None:
        plan = self.envelope_plan(freeze=True, reminder=True, escalation=True)
        self.assertFalse(all(self.evaluate(ENVELOPE_YAML, plan)))

    # -- omitted key: behaviorally correct, serialization differs ---------------------------
    # A real codex run emitted no `shouldRunOnlyOnce` for the unspecified SDD row. The task must
    # pass (it is not run-once) while the advisory records the omission.

    def test_envelope_gate_passes_when_the_falsy_key_is_omitted(self) -> None:
        plan = self.envelope_plan(freeze=True, reminder=False, escalation=None)
        self.assertTrue(all(self.evaluate(ENVELOPE_YAML, plan)))

    def test_envelope_advisory_records_the_omitted_key(self) -> None:
        plan = self.envelope_plan(freeze=True, reminder=False, escalation=None)
        self.assertFalse(all(self.evaluate(ENVELOPE_YAML, plan, advisory=True)))

    def test_envelope_advisory_passes_when_the_key_is_written(self) -> None:
        plan = self.envelope_plan(freeze=True, reminder=False, escalation=False)
        self.assertTrue(all(self.evaluate(ENVELOPE_YAML, plan, advisory=True)))

    def test_envelope_gate_still_fails_when_the_stated_yes_row_is_omitted(self) -> None:
        # `Run Only Once: Yes` was explicit in the SDD — omitting it there is a behavior change.
        plan = self.envelope_plan(freeze=None, reminder=False, escalation=False)
        self.assertFalse(all(self.evaluate(ENVELOPE_YAML, plan)))

    def test_add_task_gate_passes_when_the_falsy_key_is_omitted(self) -> None:
        self.assertTrue(all(self.evaluate(ADD_TASK_YAML, self.linear_plan(None, added=True))))

    def test_add_task_advisory_records_the_omitted_key(self) -> None:
        self.assertFalse(
            all(self.evaluate(ADD_TASK_YAML, self.linear_plan(None, added=True), advisory=True))
        )


if __name__ == "__main__":
    unittest.main()

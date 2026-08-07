#!/usr/bin/env python3
"""Behavioral matrix for the case-design finalize graders (planner suite).

Covers the two sdd.md checkers (picker pairing, deterministic reject route)
and the shared entry-rule parser they import. Every grader is exercised
against a compliant artifact AND against each regression it exists to catch,
so a grader that silently passes everything fails here first.

Runs with no model and no tenant:

    python3 tests/tasks/uipath-planner/_shared/test_finalize_checkers.py
"""


from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLANNER_ROOT = Path(__file__).resolve().parents[1]
PICKER_CHECK = PLANNER_ROOT / "case_finalize_draft_picker" / "check_picker_pairing.py"
REJECT_CHECK = PLANNER_ROOT / "case_finalize_draft_reject" / "check_reject_route.py"


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
        # Import by module name from this _shared dir, NOT via the `_shared`
        # package: in a combined-suite pytest run the maestro-case `_shared`
        # package can already occupy sys.modules and shadow this one.
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import entry_rule_check  # noqa: PLC0415

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


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Offline behavioral tests for the SupplierOnboarding graders.

Takes a caseplan the graders accept, mutates ONE fact at a time, and asserts each
mutation is caught with the message that names it. An assertion that can never fail
is worth nothing and looks like coverage, so every finding a grader claims to make
gets a test that makes it happen.

Asserting on the message, not only the exit code, is deliberate: a mutation that
trips some *other* assertion would otherwise pass this suite while the assertion
under test stayed dead.

The plan comes from `caseplan_builder.build()` — built in code, generated from a real
build, so the suite is self-contained and runs in CI. Committing a real caseplan.json
is not how this suite works: every grader unit test here builds its plan the same way.

Run: python3 -m unittest discover -s <this directory>
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).parent
CHECKERS = {
    "topology": HERE / "check_topology.py",
    "guards": HERE / "check_guards.py",
    "sla": HERE / "check_sla.py",
    "tasks_io": HERE / "check_tasks_io.py",
    "fieldnames": HERE / "check_fieldnames.py",
}

sys.path.insert(0, str(HERE))
import expected as E  # noqa: E402
import caseplan_builder  # noqa: E402


def baseline_plan() -> dict:
    """A plan all five graders accept. Fresh object per call, safe to mutate."""
    return caseplan_builder.build()


def run_checker(name: str, plan: dict) -> subprocess.CompletedProcess:
    """Run one grader against `plan` in a scratch directory."""
    with tempfile.TemporaryDirectory() as tmp:
        nested = Path(tmp) / "Case" / "Case"
        nested.mkdir(parents=True)
        with open(nested / "caseplan.json", "w", encoding="utf-8") as stream:
            json.dump(plan, stream)
        return subprocess.run(
            [sys.executable, str(CHECKERS[name])],
            cwd=tmp,
            capture_output=True,
            text=True,
        )


def stage(plan: dict, label: str) -> dict:
    return next(
        node
        for node in plan["nodes"]
        if (node.get("data") or {}).get("label") == label
    )


def tasks_of(node: dict) -> list[dict]:
    out = []
    for row in (node.get("data") or {}).get("tasks") or []:
        out.extend(row if isinstance(row, list) else [row])
    return out


def guard_of(cond: dict) -> str:
    """Read a condition's guard the way the graders do: condition first, then rules.

    The two placements mean the same thing at runtime, and this plan puts the stage-exit
    guards on the rules. A test that only wrote `conditionExpression` would mutate
    nothing and pass while the assertion under test stayed dead.
    """
    direct = cond.get("conditionExpression")
    if direct:
        return str(direct)
    for group in cond.get("rules") or []:
        for rule in group if isinstance(group, list) else [group]:
            expr = rule.get("conditionExpression")
            if expr:
                return str(expr)
    return ""


def set_guard(cond: dict, expression: str) -> None:
    cond["conditionExpression"] = expression
    for group in cond.get("rules") or []:
        for rule in group if isinstance(group, list) else [group]:
            if "conditionExpression" in rule:
                rule["conditionExpression"] = expression


def task(plan: dict, name: str) -> dict:
    for node in plan["nodes"]:
        for item in tasks_of(node):
            if (item.get("data") or {}).get("displayName") == name or item.get(
                "displayName"
            ) == name:
                return item
    raise AssertionError(f"task {name!r} not in the baseline plan")


class CheckerBase(unittest.TestCase):
    checker = ""

    def accepts(self, plan: dict):
        result = run_checker(self.checker, plan)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def rejects(self, plan: dict, needle: str):
        result = run_checker(self.checker, plan)
        blob = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, f"mutation was accepted:\n{blob}")
        self.assertIn(needle, blob, f"caught, but not by the assertion under test:\n{blob}")
        return result


class TopologyTests(CheckerBase):
    checker = "topology"

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

    def test_rejects_missing_stage(self):
        plan = baseline_plan()
        plan["nodes"] = [
            n for n in plan["nodes"] if (n.get("data") or {}).get("label") != E.WITHDRAWN
        ]
        self.rejects(plan, "missing stage")

    def test_rejects_secondary_lane_promoted_to_primary(self):
        plan = baseline_plan()
        stage(plan, E.REJECTED)["data"].pop("stageType", None)
        self.rejects(plan, "the SDD makes it secondary")

    def test_rejects_interrupting_oversight_lane(self):
        plan = baseline_plan()
        for cond in stage(plan, E.SLA_REVIEW)["data"]["entryConditions"]:
            cond["isInterrupting"] = True
        self.rejects(plan, "entry is interrupting")

    def test_rejects_unguarded_rejection_entry(self):
        plan = baseline_plan()
        conds = stage(plan, E.REJECTED)["data"]["entryConditions"]
        conds[0].pop("conditionExpression", None)
        for group in conds[0].get("rules") or []:
            for rule in group if isinstance(group, list) else [group]:
                rule.pop("conditionExpression", None)
        self.rejects(plan, "carries no guard")

    def test_rejects_dropped_corrections_loop(self):
        plan = baseline_plan()
        node = stage(plan, E.CHECKING)
        buyer_id = stage(plan, E.BUYER)["id"]
        node["data"]["entryConditions"] = [
            c
            for c in node["data"]["entryConditions"]
            if buyer_id not in json.dumps(c)
        ]
        self.rejects(plan, "send-back for corrections")

    def test_rejects_withdrawal_offered_during_setup(self):
        plan = baseline_plan()
        for cond in stage(plan, E.SETUP)["data"]["exitConditions"]:
            if cond.get("marksStageComplete"):
                cond["type"] = "wait-for-user"
        self.rejects(plan, "withdrawal picker")

    def test_rejects_withdrawal_missing_from_a_review_phase(self):
        plan = baseline_plan()
        for cond in stage(plan, E.BUYER)["data"]["exitConditions"]:
            if cond.get("type") == "wait-for-user":
                cond["type"] = "exit-only"
        self.rejects(plan, "withdrawal picker")

    def test_rejects_withdrawal_marked_case_complete(self):
        plan = baseline_plan()
        wid = stage(plan, E.WITHDRAWN)["id"]
        touched = False
        for cond in (plan.get("metadata") or {}).get("caseExitRules") or []:
            if wid in json.dumps(cond):
                cond["marksCaseComplete"] = True
                touched = True
        self.assertTrue(touched, "the mutation found no case exit fed by the withdrawal lane")
        self.rejects(plan, "marks the case complete")


class GuardTests(CheckerBase):
    checker = "guards"

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

    def test_rejects_business_label_instead_of_form_enum(self):
        plan = baseline_plan()
        blob = json.dumps(plan).replace('=== \\"sendback\\"', '=== \\"SendBack\\"')
        self.rejects(json.loads(blob), "which none of the deployed forms can emit")

    def test_rejects_dropped_signoff_threshold(self):
        plan = baseline_plan()
        for node in plan["nodes"]:
            for item in tasks_of(node):
                if "500000" in str(item.get("skipCondition") or ""):
                    item.pop("skipCondition")
        self.rejects(plan, "appears in no guard")

    def test_rejects_overlapping_buyer_exits(self):
        plan = baseline_plan()
        conds = stage(plan, E.BUYER)["data"]["exitConditions"]
        completing = next(c for c in conds if c.get("marksStageComplete"))
        diverting = next(c for c in conds if not c.get("marksStageComplete"))
        set_guard(diverting, guard_of(completing))
        self.rejects(plan, "would fire into two destinations")

    def test_rejects_guard_over_unknown_variable(self):
        plan = baseline_plan()
        cond = stage(plan, E.COMPLIANCE)["data"]["entryConditions"][0]
        cond["conditionExpression"] = '=js:vars.notAThing === "approve"'
        self.rejects(plan, "never routes")


class SlaTests(CheckerBase):
    checker = "sla"

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

    def test_rejects_stage_at_risk_band_on_the_case(self):
        plan = baseline_plan()
        for rule in (plan.get("metadata") or {}).get("slaRules") or []:
            for esc in rule.get("escalationRule") or []:
                info = esc.get("triggerInfo") or {}
                if info.get("type") == "at-risk":
                    info["atRiskPercentage"] = E.STAGE_AT_RISK_PERCENT
        self.rejects(plan, "case at-risk band")

    def test_rejects_dropped_stage_sla(self):
        plan = baseline_plan()
        stage(plan, E.BUYER)["data"].pop("slaRules", None)
        self.rejects(plan, "carries no slaRules")

    def test_rejects_breach_moved_to_a_stage_entry_rule(self):
        plan = baseline_plan()
        node = stage(plan, E.CHECKING)
        escalation = task(plan, "Escalate delayed application check")
        moved = copy.deepcopy(escalation["entryConditions"])
        escalation["entryConditions"] = [
            {"displayName": "adhoc", "rules": [[{"rule": "adhoc"}]]}
        ]
        node["data"]["entryConditions"].extend(moved)
        self.rejects(plan, "re-enters the stage")

    def test_rejects_shared_revised_date_slot(self):
        plan = baseline_plan()
        blob = json.dumps(plan).replace(
            E.PHASE_REVISED_DATE[E.BUYER], E.PHASE_REVISED_DATE[E.CHECKING]
        )
        self.rejects(json.loads(blob), "belongs to another phase")

    def test_rejects_delay_note_reading_nothing(self):
        plan = baseline_plan()
        note = task(plan, E.DELAY_NOTE_OF_PHASE[E.CHECKING])
        blob = json.dumps(note).replace(
            "vars." + E.PHASE_REVISED_DATE[E.CHECKING], "vars.escalationNotes"
        )
        note.clear()
        note.update(json.loads(blob))
        self.rejects(plan, "the new expected date blank")

    def test_rejects_wrap_up_starting_remediation(self):
        plan = baseline_plan()
        node = stage(plan, E.REJECTED)
        escalation = copy.deepcopy(task(plan, "Escalate delayed application check"))
        node["data"]["tasks"].append([escalation])
        self.rejects(plan, "starts task(s)")


class TasksIoTests(CheckerBase):
    checker = "tasks_io"

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

    def test_rejects_wrong_task_class(self):
        plan = baseline_plan()
        task(plan, "Confirm offering category match")["type"] = "api-workflow"
        self.rejects(plan, "runs on a different runtime")

    def test_rejects_extra_task(self):
        plan = baseline_plan()
        node = stage(plan, E.ONBOARDED)
        extra = copy.deepcopy(tasks_of(node)[0])
        extra["id"] = "extraTask01"
        extra["data"]["displayName"] = "Unexpected extra task"
        extra["displayName"] = "Unexpected extra task"
        node["data"]["tasks"].append([extra])
        self.rejects(plan, "extra task(s)")

    def test_rejects_dropped_run_once(self):
        plan = baseline_plan()
        task(plan, "Register supplier in ERP")["shouldRunOnlyOnce"] = False
        self.rejects(plan, "would run it twice")

    def test_rejects_recipient_as_bare_string(self):
        plan = baseline_plan()
        item = task(plan, "Record buyer review decision")
        item["data"]["recipient"] = E.EXPRESSION_RECIPIENT_VALUE
        self.rejects(plan, "must be the object")

    def test_rejects_dropped_recipient(self):
        plan = baseline_plan()
        task(plan, "Record buyer review decision")["data"].pop("recipient", None)
        self.rejects(plan, "reaches nobody")

    def test_rejects_dropped_output(self):
        plan = baseline_plan()
        item = task(plan, "Determine sign-off tier")
        item["data"]["outputs"] = [
            o for o in item["data"]["outputs"] if o.get("var") != "signOffTier"
        ]
        self.rejects(plan, "nothing in the plan writes 'signOffTier'")

    def test_rejects_adhoc_task_in_the_wrong_stage(self):
        plan = baseline_plan()
        moved = copy.deepcopy(task(plan, "Obtain legal opinion"))
        stage(plan, E.BUYER)["data"]["tasks"].append([moved])
        self.rejects(plan, "the source restricts it to")

    def test_rejects_unbound_resource(self):
        plan = baseline_plan()
        target = "Shared/uipath-maestro-case/SupplierOnboardingKit.SupplierErpRegistration"
        plan["bindings"] = [
            b for b in plan["bindings"] if b.get("resourceKey") != target
        ]
        self.rejects(plan, "bound nowhere in the plan")


class FieldNameTests(CheckerBase):
    checker = "fieldnames"

    def test_accepts_baseline(self):
        self.accepts(baseline_plan())

    def test_accepts_pascal_case_output_labels(self):
        """A PascalCase `displayName` is a label, not the wire path."""
        plan = baseline_plan()
        for node in plan["nodes"]:
            for item in tasks_of(node):
                for out in (item.get("data") or {}).get("outputs") or []:
                    if out.get("displayName"):
                        out["displayName"] = out["displayName"].title()
        self.accepts(plan)

    def test_rejects_pascal_cased_wire_path(self):
        plan = baseline_plan()
        for node in plan["nodes"]:
            for item in tasks_of(node):
                for out in (item.get("data") or {}).get("outputs") or []:
                    if out.get("source") == "=" + E.CONNECTOR_OUTPUT_PATH:
                        out["source"] = "=Response.Status"
        self.rejects(plan, "re-cased variant")

    def test_rejects_status_landing_in_the_wrong_slot(self):
        plan = baseline_plan()
        for node in plan["nodes"]:
            for item in tasks_of(node):
                for out in (item.get("data") or {}).get("outputs") or []:
                    if out.get("source") == "=" + E.CONNECTOR_OUTPUT_PATH:
                        out["var"] = "escalationNotes"
        self.rejects(plan, "lands in")

    def test_rejects_dotted_read_of_an_unknown_root(self):
        """A dereference off a variable the plan does not hold yields undefined."""
        plan = baseline_plan()
        item = task(plan, "Confirm offering category match")
        item["data"]["inputs"].append(
            {"name": "injected", "type": "string",
             "value": "=js:(vars.noSuchDocument.FullName)"}
        )

        self.rejects(plan, "the read yields undefined")

    def test_rejects_dropped_document_read(self):
        """The category-match agent must still read all four supporting documents."""
        plan = baseline_plan()
        item = task(plan, E.DOCUMENT_READER_TASK)
        item["data"]["inputs"] = [
            {"name": "submittedDocuments", "type": "string",
             "value": "=js:(vars.registrationCertificate)"}
        ]

        self.rejects(plan, "does not read")

    def test_accepts_guarded_document_walk(self):
        """The build's guarded array walk reads the same four variables and must pass.

        An assertion that pinned the SDD's literal `vars.X.FullName` spelling would fail
        this — and this shape is strictly better, since it survives a missing document.
        """
        self.accepts(baseline_plan())


if __name__ == "__main__":
    unittest.main()

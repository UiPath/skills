#!/usr/bin/env python3
"""Behavioral matrix for the run-once caseplan-emit graders.

Covers the JMESPath assertions the two caseplan-emit tasks grade with. The
sdd.md finalize checkers (picker pairing, reject route) moved with their tasks
to tests/tasks/uipath-planner/_shared/test_finalize_checkers.py.

Runs with no model and no tenant:

    python3 tests/tasks/uipath-maestro-case/_shared/test_reentry_reachability_checks.py
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

CASE_ROOT = Path(__file__).resolve().parents[1]
ADD_TASK_YAML = CASE_ROOT / "edit" / "add_task_run_once_default" / "add_task_run_once_default.yaml"
ENVELOPE_YAML = CASE_ROOT / "single_node" / "run_once_envelope" / "run_once_envelope.yaml"
LINEAR_FIXTURE = (
    CASE_ROOT / "edit" / "templates" / "LinearThreeStages" / "LinearThreeStages" / "caseplan.json"
)

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

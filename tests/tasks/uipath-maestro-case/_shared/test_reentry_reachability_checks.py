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

def json_checks(task_yaml: Path) -> list[dict]:
    import yaml  # noqa: PLC0415 — optional dependency, guarded by skipUnless

    spec = yaml.safe_load(task_yaml.read_text(encoding="utf-8"))
    return [c for c in spec["success_criteria"] if c.get("type") == "json_check"]


def load_expressions(task_yaml: Path) -> list[tuple[str, object]]:
    """Assertions from the task's json_check criteria."""
    out: list[tuple[str, object]] = []
    for criterion in json_checks(task_yaml):
        for assertion in criterion["assertions"]:
            out.append((assertion["expression"], assertion["expected"]))
    return out


# `None` means the key is omitted entirely — what a run actually produced for the
# unspecified SDD row, and the reason the gate grades on behavior rather than serialization.
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

    def evaluate(self, task_yaml: Path, plan: dict) -> list[bool]:
        import jmespath  # noqa: PLC0415

        return [
            jmespath.search(expression, plan) == expected
            for expression, expected in load_expressions(task_yaml)
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

    # -- omitted key: same task as an explicit false --------------------------------------
    # A real codex run emitted no `shouldRunOnlyOnce` for the unspecified SDD row, and the
    # builder SDK omits the key unless `.runOnce()` / `.runOnReEntry()` is called. The case
    # converter maps an omitted key to `runOnlyOnce: false`, the same rules as an explicit
    # `false`, so both shapes must score the same — no criterion may tell them apart.

    def test_envelope_gate_passes_when_the_falsy_key_is_omitted(self) -> None:
        plan = self.envelope_plan(freeze=True, reminder=False, escalation=None)
        self.assertTrue(all(self.evaluate(ENVELOPE_YAML, plan)))

    def test_envelope_gate_still_fails_when_the_stated_yes_row_is_omitted(self) -> None:
        # `Run Only Once: Yes` was explicit in the SDD — omitting it there is a behavior change.
        plan = self.envelope_plan(freeze=None, reminder=False, escalation=False)
        self.assertFalse(all(self.evaluate(ENVELOPE_YAML, plan)))

    def test_add_task_gate_passes_when_the_falsy_key_is_omitted(self) -> None:
        self.assertTrue(all(self.evaluate(ADD_TASK_YAML, self.linear_plan(None, added=True))))

    def test_envelope_gate_passes_when_every_falsy_key_is_omitted(self) -> None:
        plan = self.envelope_plan(freeze=True, reminder=None, escalation=None)
        self.assertTrue(all(self.evaluate(ENVELOPE_YAML, plan)))

    def test_no_criterion_tells_an_omitted_key_from_an_explicit_false(self) -> None:
        # Every json_check — gating or advisory, both carry score weight — must give the same
        # verdict on the two shapes. The 2026-11-05 same-ground run lost v2 0.14 / 0.06 to a
        # weighted advisory that required the explicit key.
        import jmespath  # noqa: PLC0415

        cases = [
            (ADD_TASK_YAML, self.linear_plan(None), self.linear_plan(False)),
            (
                ENVELOPE_YAML,
                self.envelope_plan(freeze=True, reminder=None, escalation=None),
                self.envelope_plan(freeze=True, reminder=False, escalation=False),
            ),
        ]
        for task_yaml, omitted, explicit in cases:
            for criterion in json_checks(task_yaml):
                for assertion in criterion["assertions"]:
                    expression, expected = assertion["expression"], assertion["expected"]
                    with self.subTest(task=task_yaml.name, expression=expression):
                        self.assertEqual(
                            jmespath.search(expression, omitted) == expected,
                            jmespath.search(expression, explicit) == expected,
                        )


if __name__ == "__main__":
    unittest.main()

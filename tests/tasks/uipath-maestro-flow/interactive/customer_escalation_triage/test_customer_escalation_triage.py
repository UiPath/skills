"""Focused tests for the escalation sandbox seed and output comparison."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load("customer_escalation_checker", "check_customer_escalation_triage.py")
seed = _load("customer_escalation_seed", "_setup/seed.py")


def _payload(**outputs):
    return {"Variables": {"Globals": outputs}}


class CustomerEscalationTriageTests(unittest.TestCase):
    def test_seed_cases_isolated(self) -> None:
        cases = seed.build_seed()["cases"]

        self.assertEqual(
            [case["expected"]["severity"] for case in cases], ["Sev1", "Sev2", "Sev3"]
        )
        self.assertEqual(
            len({case["inputs"]["correlationId"] for case in cases}), checker.CASE_COUNT
        )

    def test_named_comparison_accepts_runtime_string_booleans(self) -> None:
        checker.assert_named_equals(
            _payload(engineeringNeeded="true"), "engineeringNeeded", True
        )
        checker.assert_named_equals(
            _payload(engineeringNeeded="false"), "engineeringNeeded", False
        )

    def test_named_comparison_is_case_insensitive_for_text(self) -> None:
        checker.assert_named_equals(_payload(severity="SEV1"), "severity", "Sev1")
        checker.assert_named_equals(
            _payload(responseMode="draft"), "responseMode", "Draft"
        )

    def test_named_comparison_rejects_wrong_business_outcome(self) -> None:
        with self.assertRaisesRegex(SystemExit, "expected 'Sev1'"):
            checker.assert_named_equals(
                _payload(severity="Sev3"), "severity", "Sev1"
            )


if __name__ == "__main__":
    unittest.main()

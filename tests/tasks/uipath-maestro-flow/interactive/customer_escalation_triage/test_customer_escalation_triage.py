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
seed = _load("customer_escalation_seed", "seed.py")


def _payload(**outputs):
    return {"Variables": {"Globals": outputs}}


class CustomerEscalationTriageTests(unittest.TestCase):
    def test_seed_has_isolated_sev1_and_sev3_cases(self) -> None:
        document = seed.build_seed()

        self.assertEqual(len(document["cases"]), 2)
        self.assertEqual(document["cases"][0]["expected"]["severity"], "Sev1")
        self.assertEqual(document["cases"][1]["expected"]["severity"], "Sev3")
        self.assertNotEqual(
            document["cases"][0]["inputs"]["correlationId"],
            document["cases"][1]["inputs"]["correlationId"],
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

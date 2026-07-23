"""Unit tests for hidden runtime-case aggregation."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any


CHECKER_PATH = Path(__file__).with_name("check_customer_escalation_runtime.py")
SPEC = importlib.util.spec_from_file_location(
    "customer_escalation_runtime_checker", CHECKER_PATH
)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


class RuntimeCheckerTests(unittest.TestCase):
    def test_main_runs_every_case_and_aggregates_failures(self) -> None:
        original_bpmn = checker.BPMN
        original_cases = checker.cases
        original_verify_case = checker.verify_case
        visited: list[str] = []
        hidden_cases = [{"name": f"case-{index}"} for index in range(10)]

        def fake_verify(case: dict[str, Any]) -> None:
            visited.append(case["name"])
            if case["name"] in {"case-2", "case-7"}:
                raise SystemExit(f"FAIL: {case['name']} mismatch")

        try:
            checker.BPMN = Path(__file__)
            checker.cases = lambda: hidden_cases
            checker.verify_case = fake_verify
            with self.assertRaisesRegex(SystemExit, "2/10 hidden cases failed") as caught:
                checker.main()
        finally:
            checker.BPMN = original_bpmn
            checker.cases = original_cases
            checker.verify_case = original_verify_case

        self.assertEqual(visited, [case["name"] for case in hidden_cases])
        self.assertIn("case-2 mismatch", str(caught.exception))
        self.assertIn("case-7 mismatch", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

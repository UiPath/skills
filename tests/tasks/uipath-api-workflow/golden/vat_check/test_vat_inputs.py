#!/usr/bin/env python3
"""Offline tests for check_vat.py: which workflow it grades and which input contracts it
tries on it.

Run: python3 -m unittest discover -s <this directory>
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vat_fakes import check_vat, workflow_with_inputs  # noqa: E402


class InputContractTests(unittest.TestCase):
    def candidates(self, *names):
        return check_vat.input_candidates(list(names), "RO", "34737997")

    def test_single_input_gets_the_prefixed_then_the_bare_number(self):
        self.assertEqual(self.candidates("vatNumber"), [{"vatNumber": "RO34737997"}, {"vatNumber": "34737997"}])

    def test_country_and_number_inputs_are_recognised_by_name(self):
        self.assertEqual(self.candidates("countryCode", "vatNumber"),
                         [{"vatNumber": "RO34737997"}, {"vatNumber": "34737997"},
                          {"countryCode": "RO", "vatNumber": "34737997"}])
        self.assertIn({"memberState": "RO", "taxId": "34737997"}, self.candidates("memberState", "taxId"))

    def test_two_unnamed_inputs_get_the_split_in_both_orders(self):
        candidates = self.candidates("a", "b")
        self.assertIn({"a": "RO", "b": "34737997"}, candidates)
        self.assertIn({"a": "34737997", "b": "RO"}, candidates)
        self.assertIn({"a": "RO34737997"}, candidates)

    def test_swagger_requester_and_trader_fields_are_left_out(self):
        names = ["countryCode", "vatNumber", "requesterMemberStateCode", "requesterNumber", "traderName"]
        self.assertEqual(self.candidates(*names), self.candidates("countryCode", "vatNumber"))

    def test_extra_input_is_left_out_before_any_split_is_tried(self):
        self.assertEqual(self.candidates("vatNumber", "timeoutSeconds")[:2],
                         [{"vatNumber": "RO34737997"}, {"vatNumber": "34737997"}])

    def test_unrecognised_country_input_still_gets_the_split(self):
        self.assertIn({"cc": "RO", "vatNumber": "34737997"}, self.candidates("cc", "vatNumber"))

    def test_a_lone_country_looking_input_still_gets_the_vat_id(self):
        self.assertIn({"vatCountryNumber": "RO34737997"}, self.candidates("vatCountryNumber"))

    def test_candidates_are_capped_and_empty_without_inputs(self):
        self.assertLessEqual(len(self.candidates(*[f"in{i}" for i in range(30)])), check_vat.MAX_CANDIDATES)
        self.assertEqual(self.candidates(), [])

    def test_declared_inputs_reads_input_schema_properties(self):
        self.assertEqual(check_vat.declared_inputs(workflow_with_inputs("countryCode", "vatNumber")),
                         ["countryCode", "vatNumber"])
        self.assertEqual(check_vat.declared_inputs({}), [])
        self.assertEqual(check_vat.declared_inputs({"input": {"schema": {"document": {"properties": []}}}}), [])
        for malformed in ({"input": []}, {"input": {"schema": "x"}}, {"input": {"schema": {"document": 3}}}):
            with self.subTest(malformed=malformed):
                self.assertEqual(check_vat.declared_inputs(malformed), [])
        self.assertEqual(len(check_vat.declared_inputs(workflow_with_inputs(*[f"in{i}" for i in range(50)]))), 20)


class FindWorkflowTests(unittest.TestCase):
    def test_ignores_root_and_node_modules_and_picks_the_first_project_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Workflow.json").write_text("{}")
            (root / "node_modules" / "pkg").mkdir(parents=True)
            (root / "node_modules" / "pkg" / "Workflow.json").write_text("{}")
            self.assertIsNone(check_vat.find_workflow(root))
            for project in ("Vat", "Vat-Check"):
                (root / project).mkdir()
                (root / project / "Workflow.json").write_text("{}")
            self.assertEqual(check_vat.find_workflow(root), (root / "Vat-Check" / "Workflow.json").resolve())


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression tests for the contract-variant wrapper grader's element rules."""

from __future__ import annotations

import os
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.check_contract_variant_wrappers import (  # noqa: E402
    EXPECTED_MODEL_OR_PRESERVE_SHELLS,
    require_wrapper,
)

CASE_RULES = next(
    spec for spec in EXPECTED_MODEL_OR_PRESERVE_SHELLS if spec[2] == "Maestro.CaseRulesEvaluator"
)


def process_with(element: str, type_value: str = "Maestro.CaseRulesEvaluator") -> ET.Element:
    return ET.fromstring(
        f"""<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
             xmlns:uipath="http://uipath.org/schema/bpmn">
          <bpmn:process id="P">
            <bpmn:{element} id="rules">
              <bpmn:extensionElements>
                <uipath:activity version="v1">
                  <uipath:type value="{type_value}" version="v1" />
                </uipath:activity>
              </bpmn:extensionElements>
            </bpmn:{element}>
          </bpmn:process>
        </bpmn:definitions>"""
    )


class CaseRulesEvaluatorElementTests(unittest.TestCase):
    def check(self, root: ET.Element) -> None:
        wrapper, extension_name, type_value = CASE_RULES
        require_wrapper(root, wrapper, extension_name, type_value)

    def test_plain_task_passes_as_studio_web_writes_it(self) -> None:
        self.check(process_with("task"))

    def test_service_task_passes_as_the_sdk_snapshot_writes_it(self) -> None:
        self.check(process_with("serviceTask"))

    def test_other_element_fails(self) -> None:
        with self.assertRaises(SystemExit):
            self.check(process_with("scriptTask"))

    def test_task_without_the_typed_shell_fails(self) -> None:
        with self.assertRaises(SystemExit):
            self.check(process_with("task", type_value="uipath:Activity"))


if __name__ == "__main__":
    unittest.main()

"""Unit tests for the ExpenseReimbursementRunnable structural checker."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_expense_runnable_structure import (  # noqa: E402
    _assert_bindings_v2_metadata,
    _assert_required_external_bindings,
)


class BindingsV2MetadataTests(unittest.TestCase):
    def test_accepts_documented_bindings_v2_metadata_shape(self) -> None:
        _assert_bindings_v2_metadata(
            {
                "version": "2.0",
                "resources": [
                    {
                        "resource": "process",
                        "key": "Shared/Example/API Workflow",
                        "metadata": {"subType": "Api"},
                    },
                    {
                        "resource": "process",
                        "key": "Shared/Example/RPA Workflow",
                        "metadata": {},
                    },
                ],
            }
        )

    def test_rejects_bindings_version_metadata(self) -> None:
        with self.assertRaisesRegex(SystemExit, "bindingsVersion"):
            _assert_bindings_v2_metadata(
                {
                    "version": "2.0",
                    "resources": [
                        {
                            "resource": "process",
                            "key": "Shared/Example/API Workflow",
                            "metadata": {"subType": "Api", "bindingsVersion": "2.2"},
                        }
                    ],
                }
            )
    def test_rejects_solutions_support_metadata(self) -> None:
        with self.assertRaisesRegex(SystemExit, "solutionsSupport"):
            _assert_bindings_v2_metadata(
                {
                    "version": "2.0",
                    "resources": [
                        {
                            "resource": "process",
                            "key": "Shared/Example/API Workflow",
                            "metadata": {"subType": "Api", "solutionsSupport": "true"},
                        }
                    ],
                }
            )


class RunLimitTests(unittest.TestCase):
    def test_turn_timeout_covers_the_full_e2e_task_budget(self) -> None:
        task_yaml = Path(__file__).with_name("expense_runnable_e2e.yaml").read_text(
            encoding="utf-8"
        )
        limits = {}
        for line in task_yaml.splitlines():
            name, separator, value = line.strip().partition(":")
            if separator and name in {"task_timeout", "turn_timeout"}:
                limits[name] = int(value.strip())
        self.assertEqual(limits["turn_timeout"], limits["task_timeout"])


class ResourceBindingTests(unittest.TestCase):
    def test_accepts_runnable_resource_display_names(self) -> None:
        _assert_required_external_bindings(
            {
                "resources": [
                    {
                        "key": "Shared/uipath-maestro-case/NameToAgeFixed2.API Workflow",
                        "value": {"name": {"defaultValue": "API Workflow"}},
                    },
                    {
                        "key": "Shared/uipath-maestro-flow/CountLetters CodedAgent.CountLetters",
                        "value": {"name": {"defaultValue": "CountLetters"}},
                    },
                    {
                        "key": "Shared/uipath-agents/ProcurementProcess.ProcurementProcess",
                        "value": {"name": {"defaultValue": "ProcurementProcess"}},
                    },
                    {
                        "key": "Shared/uipath-maestro-flow/ProjectEuler RPA.RPA Workflow",
                        "value": {"name": {"defaultValue": "RPA Workflow"}},
                    },
                    {
                        "key": "Shared/uipath-maestro-case/CaseTest.Maestro Case",
                        "value": {"name": {"defaultValue": "Maestro Case"}},
                    },
                ]
            }
        )

    def test_rejects_resource_alias_in_place_of_display_name(self) -> None:
        with self.assertRaisesRegex(SystemExit, "API Workflow"):
            _assert_required_external_bindings(
                {
                    "resources": [
                        {
                            "key": "Shared/uipath-maestro-case/NameToAgeFixed2.NameToAgeFixed2",
                            "value": {"name": {"defaultValue": "NameToAgeFixed2"}},
                        }
                    ]
                }
            )

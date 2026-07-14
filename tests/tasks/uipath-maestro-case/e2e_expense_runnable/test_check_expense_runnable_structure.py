"""Unit tests for the ExpenseReimbursementRunnable structural checker."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_expense_runnable_structure import _assert_bindings_v2_metadata  # noqa: E402


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

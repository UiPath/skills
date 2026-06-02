#!/usr/bin/env python3
"""S1 — All 5 entity-record activities present on CodingAgentsEvalEntity."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
from xaml_check import assert_activities_present, assert_no_unexpected_uda  # noqa: E402

EXPECTED = [
    "CreateEntityRecord",
    "GetEntityRecordById",
    "UpdateEntityRecord",
    "DeleteEntityRecord",
    "QueryEntityRecords",
]

if __name__ == "__main__":
    xaml = sys.argv[1] if len(sys.argv) > 1 else "DataServiceEval/Main.xaml"
    assert_activities_present(xaml, EXPECTED, "CodingAgentsEvalEntity")
    assert_no_unexpected_uda(xaml, EXPECTED)
    print(f"PASS: {xaml} contains all 5 entity-record activities")

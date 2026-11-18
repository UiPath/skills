"""Should-match / should-not-match fixtures for Rule 14 and diagnose guard regexes.

Patterns load from the task YAMLs, so a narrowing is checked against true positives
as well as the false positive that prompted it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

CASE_TASKS = Path(__file__).resolve().parent.parent


def _pattern(relative: str, criterion_type: str, description_prefix: str) -> str:
    task = yaml.safe_load((CASE_TASKS / relative).read_text())
    matches = [
        c["command_pattern"]
        for c in task["success_criteria"]
        if c["type"] == criterion_type and c["description"].startswith(description_prefix)
    ]
    assert len(matches) == 1, f"{relative}: expected one {criterion_type} '{description_prefix}…', found {len(matches)}"
    return matches[0]


def _hits(pattern: str, command: str) -> bool:
    return re.search(pattern, command, re.DOTALL) is not None


SAFETY = _pattern(
    "safety_guard/artifact_safety_guard.yaml",
    "command_not_executed",
    "Rule 14: no inline interpreter",
)
GOLDEN = _pattern(
    "golden_rebuild/cm_golden_expense/cm_golden_expense.yaml",
    "command_not_executed",
    "Agent did not edit caseplan.json in place",
)
FAULTED_READ = _pattern(
    "diagnose/faulted_instance_runtime/faulted_instance_runtime.yaml",
    "command_executed",
    "Agent read the instance's incidents",
)
FAULTED_WRITE = _pattern(
    "diagnose/faulted_instance_runtime/faulted_instance_runtime.yaml",
    "command_not_executed",
    "Read-only",
)

CASEPLAN_EDITS = [
    "sed -i 's/a/b/' P/P/caseplan.json",
    "sed -i 's/\"a\"/\"b\"/g; s/\"c\"/\"d\"/g' P/P/caseplan.json",
    "sed -i 's/x/& y/' P/P/caseplan.json",
    "sed -i.bak -e 's/a/b/' P/P/caseplan.case",
    "perl -pi -e 's/foo/bar/; s/baz/qux/' P/P/caseplan.case",
    "cd P && sed -i 's/a/b/' P/caseplan.json",
]

NOT_CASEPLAN_EDITS = [
    # 2026-11-18 nightly false positive: the in-place edit targets the .case.ts source.
    "sed -i 's/Old/New/' .flow-sdk/CMGoldenExpense.case.ts; cp CMGoldenExpense/caseplan.case .flow-sdk/",
    "sed -i 's/Old/New/' X.case.ts && cat P/caseplan.json",
    "sed -n '1,40p' P/P/caseplan.json",
    "perl -ne 'print if /stage/' P/P/caseplan.json",
    "python3 -c \"import json; print(json.load(open('P/P/caseplan.json')))\"",
]


@pytest.mark.parametrize("command", CASEPLAN_EDITS)
@pytest.mark.parametrize("pattern", [SAFETY, GOLDEN], ids=["safety", "golden"])
def test_rule14_guards_catch_caseplan_edits(pattern: str, command: str) -> None:
    assert _hits(pattern, command)


@pytest.mark.parametrize("command", NOT_CASEPLAN_EDITS)
@pytest.mark.parametrize("pattern", [SAFETY, GOLDEN], ids=["safety", "golden"])
def test_rule14_guards_allow_reads_and_source_edits(pattern: str, command: str) -> None:
    assert not _hits(pattern, command)


@pytest.mark.parametrize(
    "command",
    [
        "sed -i 's/a/b/' registry-resolved.json",
        "python3 -c \"import json;f=open('registry-resolved.json','w');f.write('{}')\"",
        "python3 -c \"open('P/P/caseplan.json','w').write('{}')\"",
        "node -e \"require('fs').writeFileSync('P/P/caseplan.json','{}')\"",
        "sed -i 's/a/b/' P/P/bindings_v2.json",
    ],
)
def test_safety_guard_covers_every_skill_artifact(command: str) -> None:
    assert _hits(SAFETY, command)


def test_safety_guard_allows_uuid_subprocess() -> None:
    assert not _hits(SAFETY, "node -e \"console.log(require('crypto').randomUUID())\"")


@pytest.mark.parametrize(
    "command",
    [
        "uip maestro case instances list --folder-path Shared --output json",
        "uip maestro case instance incidents 123 --output json",
        "uip maestro case processes incidents abc --output json",
    ],
)
def test_faulted_read_accepts_singular_and_plural(command: str) -> None:
    assert _hits(FAULTED_READ, command)


@pytest.mark.parametrize(
    "command,mutates",
    [
        ("uip maestro case instances retry 123", True),
        ("uip maestro case instance cancel 123", True),
        ("uip maestro case instances list --output json", False),
    ],
)
def test_faulted_write_guard(command: str, mutates: bool) -> None:
    assert _hits(FAULTED_WRITE, command) is mutates

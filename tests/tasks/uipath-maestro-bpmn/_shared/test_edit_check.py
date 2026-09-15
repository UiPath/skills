"""Unit tests for the brownfield-edit checkers' fixture wiring.

The checkers live in `_shared/` while their fixtures stay with the task, so
moving either side resolves to a missing file and every edit eval fails grading
with the agent's work untouched.
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.edit_check import load_original  # noqa: E402

SHARED = Path(__file__).resolve().parent


def _load_original_calls() -> list[tuple[str, tuple[str, ...]]]:
    calls = []
    for checker in sorted(SHARED.glob("check_*.py")):
        tree = ast.parse(checker.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if getattr(node.func, "id", None) != "load_original":
                continue
            calls.append(
                (
                    checker.name,
                    tuple(a.value for a in node.args if isinstance(a, ast.Constant)),
                )
            )
    return calls


CALLS = _load_original_calls()


def test_edit_checkers_are_discovered() -> None:
    assert CALLS


@pytest.mark.parametrize("checker,args", CALLS, ids=[name for name, _ in CALLS])
def test_pristine_fixture_loads(checker: str, args: tuple[str, ...]) -> None:
    assert len(args) == 2, f"{checker}: load_original needs literal (task_dir, basename)"
    assert load_original(*args).tag.endswith("definitions")

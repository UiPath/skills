"""Unit tests for the brownfield-edit checkers' fixture wiring.

The checkers live in `_shared/` while their fixtures stay with the task, so
moving either side resolves to a missing file and every edit eval fails grading
with the agent's work untouched.
"""

from __future__ import annotations

import ast
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.edit_check import canonical, load_original  # noqa: E402

SHARED = Path(__file__).resolve().parent
EDIT_ROOT = SHARED.parent / "edit"


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
GUARDED = {args[0] for _, args in CALLS if args}
SHIPPED = {f"edit/{path.parent.name}" for path in EDIT_ROOT.glob("*/fixture")}


def test_every_shipped_fixture_is_guarded() -> None:
    assert SHIPPED, f"no edit task ships a fixture under {EDIT_ROOT}"
    assert GUARDED == SHIPPED


@pytest.mark.parametrize("checker,args", CALLS, ids=[name for name, _ in CALLS])
def test_pristine_fixture_loads(checker: str, args: tuple[str, ...]) -> None:
    assert len(args) == 2, f"{checker}: load_original needs literal (task_dir, basename)"
    assert load_original(*args).tag.endswith("definitions")

def _el(inner: str):
    return ET.fromstring(f'<bpmn:t xmlns:bpmn="b" xmlns:uipath="u">{inner}</bpmn:t>')


def test_extension_children_of_different_types_compare_equal_in_any_order() -> None:
    """Readers pick them by type, and the authoring routes disagree on order."""
    a = _el('<bpmn:extensionElements><uipath:scriptVersion value="v3"/><uipath:mapping id="m"/></bpmn:extensionElements>')
    b = _el('<bpmn:extensionElements><uipath:mapping id="m"/><uipath:scriptVersion value="v3"/></bpmn:extensionElements>')
    assert canonical(a) == canonical(b)


def test_swapping_two_children_of_the_SAME_type_still_differs() -> None:
    """Sorting whole views would have hidden this, and it changes the runtime contract.

    Readers that select by type also disagree about which of several same-type siblings
    wins — ``ScriptReader`` takes the FIRST ``uipath:scriptVersion``, the local engine's
    parser lets the LAST ``uipath:Mapping`` set the serviceType — so the order of two of
    a kind is meaning, not formatting.
    """
    a = _el('<bpmn:extensionElements><uipath:scriptVersion value="v1"/><uipath:scriptVersion value="v3"/></bpmn:extensionElements>')
    b = _el('<bpmn:extensionElements><uipath:scriptVersion value="v3"/><uipath:scriptVersion value="v1"/></bpmn:extensionElements>')
    assert canonical(a) != canonical(b)


def test_order_still_matters_outside_extension_elements() -> None:
    a = _el('<uipath:variables><uipath:input id="a"/><uipath:input id="b"/></uipath:variables>')
    b = _el('<uipath:variables><uipath:input id="b"/><uipath:input id="a"/></uipath:variables>')
    assert canonical(a) != canonical(b)

"""check_timer_from_input_run.py plan check against an SDK-compiled TimerHoldCase.

testdata/plan.json is `case-compile` output (builder-sdk 6.120.17) for an input
holdFor (default PT10S) and `waitForTimer({ duration: '=js:vars.holdFor' })`;
the Case Designer saves the same timer data when a variable is picked. No tenant
is touched.

    cd tests && uv run -q --with pytest python -m pytest -q tasks/uipath-maestro-case/single_node/timer_from_input
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
PLAN = json.loads((HERE / "testdata" / "plan.json").read_text())


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


grader = _load("check_timer_from_input_run_under_test", HERE / "check_timer_from_input_run.py")


def _timer_data(plan: dict) -> dict:
    return next(t for t in grader.iter_tasks(plan) if t.get("type") == "wait-for-timer")["data"]


def _with_value(value: str) -> dict:
    plan = copy.deepcopy(PLAN)
    _timer_data(plan)["timeDuration"] = value
    return plan


def test_the_compiled_plan_passes() -> None:
    assert grader.timer_task(PLAN)["data"]["timeDuration"] == "=js:vars.holdFor"


def test_spaces_inside_the_expression_pass() -> None:
    assert grader.timer_task(_with_value("=js: vars.holdFor "))


@pytest.mark.parametrize(
    "value",
    ["=vars.holdFor", "PT10S", "=js:vars.other", "=js:vars.holdFor + 'S'", ""],
    ids=["csharp", "literal", "other-variable", "expression-not-a-read", "empty"],
)
def test_a_timer_that_does_not_read_hold_for_in_js_fails(value: str) -> None:
    with pytest.raises(SystemExit, match="no wait-for-timer reads holdFor"):
        grader.timer_task(_with_value(value))


def test_a_date_timer_fails() -> None:
    plan = copy.deepcopy(PLAN)
    data = _timer_data(plan)
    data["timerType"] = "timeDate"
    with pytest.raises(SystemExit, match="no wait-for-timer reads holdFor"):
        grader.timer_task(plan)


def test_a_wrong_default_fails() -> None:
    plan = copy.deepcopy(PLAN)
    for v in grader.get_variables(plan)["inputs"]:
        if v["name"] == "holdFor":
            v["default"] = "PT1H"
    with pytest.raises(SystemExit, match="defaults to 'PT1H'"):
        grader.timer_task(plan)


def test_no_timer_fails() -> None:
    plan = copy.deepcopy(PLAN)
    for t in grader.iter_tasks(plan):
        t["type"] = "process"
    with pytest.raises(SystemExit, match="no wait-for-timer task"):
        grader.timer_task(plan)

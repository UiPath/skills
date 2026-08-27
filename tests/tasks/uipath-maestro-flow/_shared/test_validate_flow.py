"""Unit tests for validate_flow.py's timeout budget and retry.

`uip maestro flow validate` refreshes the node manifest from the tenant on every
invocation, so its wall time is bimodal: ~8-14s typical, 60-67s on the tail.
Before this budget existed the harness kill was the only guard, and
``coder_eval/sandbox.py`` discards partial stdout on timeout — so a stalled
validate reported ``exit -1`` with an empty stdout and read like a broken flow.
skill-flow-feet-inches failed that way on a flow that validates clean.

These pin the behavior that replaced it: a stall is retried and then reported
readably, a real fault is not retried, and no attempt outlives the criterion
budget. Faked at ``subprocess.run`` like :mod:`test_flow_check`, so nothing here
needs a tenant, a real ``uip``, or wall-clock sleeping.
"""

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import validate_flow  # noqa: E402

# Scaled down from the shipped 180/20/30 so the arithmetic stays checkable by
# hand: 6s usable, so attempt 1 caps at 3.0s and its retry at what is left.
_BUDGET = 8
_HEADROOM = 2
_MIN_ATTEMPT = 1


def _cp(returncode, stdout="", stderr=""):
    return subprocess.CompletedProcess(
        args=["uip", "maestro", "flow", "validate"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _timeout(stdout=b"partial", stderr=b"stub stderr"):
    return subprocess.TimeoutExpired(
        cmd=["uip", "maestro", "flow", "validate"],
        timeout=1,
        output=stdout,
        stderr=stderr,
    )


def _stub(monkeypatch, results, *, flows=("a.flow",)):
    """Feed validate_flow a queue of results, stub discovery, sleep, and glob.

    A queued ``BaseException`` is raised rather than returned, which is how the
    ``subprocess.TimeoutExpired`` path is exercised.

    ``time.monotonic`` is replaced by a counter the fake ``subprocess.run``
    advances: a stalled attempt burns its whole cap, a returning one costs
    almost nothing. Without that the budget never appears to shrink — real
    attempts consume wall time and faked ones do not — and every deadline
    assertion here would pass vacuously.

    ``calls["deadline"]`` is what :func:`validate_flow.main` will compute, so
    tests can assert no attempt was ever allowed to run past it."""
    calls = {"n": 0, "timeouts": [], "flows": [], "clock": 0.0, "overruns": []}
    queue = list(results)

    monkeypatch.setattr(validate_flow, "find_project_dir", lambda: "/tmp/proj")
    monkeypatch.setattr(validate_flow.glob, "glob", lambda *a, **k: list(flows))
    monkeypatch.setattr(validate_flow.time, "sleep", lambda *_: None)
    monkeypatch.setattr(validate_flow.time, "monotonic", lambda: calls["clock"])
    monkeypatch.setattr(validate_flow, "_CRITERION_BUDGET_SECONDS", _BUDGET)
    monkeypatch.setattr(validate_flow, "_BUDGET_HEADROOM_SECONDS", _HEADROOM)
    monkeypatch.setattr(validate_flow, "_MIN_ATTEMPT_SECONDS", _MIN_ATTEMPT)
    calls["deadline"] = float(_BUDGET - _HEADROOM)

    def fake_run(cmd, **kwargs):
        calls["n"] += 1
        timeout = kwargs.get("timeout")
        calls["timeouts"].append(timeout)
        calls["flows"].append(cmd[4])
        if calls["clock"] + timeout > calls["deadline"]:
            calls["overruns"].append((cmd[4], calls["clock"], timeout))
        result = queue.pop(0)
        if isinstance(result, BaseException):
            calls["clock"] += timeout  # the stall ran out its cap
            raise result
        calls["clock"] += 0.1
        return result

    monkeypatch.setattr(validate_flow.subprocess, "run", fake_run)
    return calls


def test_valid_flow_exits_zero(monkeypatch, capsys):
    calls = _stub(monkeypatch, [_cp(0, '{"Data":{"Status":"Valid"}}')])
    assert validate_flow.main() == 0
    assert calls["n"] == 1
    assert '"Valid"' in capsys.readouterr().out


def test_stall_is_retried_then_reported_readably(monkeypatch, capsys):
    """The failure mode this module exists for: the report must name the file,
    surface the CLI's partial output, and say the flow may still be valid."""
    calls = _stub(monkeypatch, [_timeout(), _timeout()])

    assert validate_flow.main() == 1
    assert calls["n"] == 2

    err = capsys.readouterr().err
    assert "attempt 1/2" in err and "attempt 2/2" in err
    assert "a.flow" in err
    assert "partial" in err  # TimeoutExpired hands output back as bytes
    assert "may well be valid" in err


def test_stall_then_success_exits_zero(monkeypatch):
    """One stalled manifest fetch must not fail a flow the retry validates."""
    calls = _stub(monkeypatch, [_timeout(), _cp(0, '{"Data":{"Status":"Valid"}}')])
    assert validate_flow.main() == 0
    assert calls["n"] == 2


def test_invalid_flow_fails_without_retry(monkeypatch, capsys):
    """A schema or graph fault reproduces exactly, so retrying it only burns
    budget that a genuinely stalled file may need."""
    calls = _stub(monkeypatch, [_cp(1, '{"Result":"Failure"}')])
    assert validate_flow.main() == 1
    assert calls["n"] == 1
    assert '"Failure"' in capsys.readouterr().out


def test_every_flow_file_is_validated(monkeypatch):
    calls = _stub(
        monkeypatch,
        [_cp(0), _cp(0)],
        flows=("a.flow", "b.flow"),
    )
    assert validate_flow.main() == 0
    assert calls["flows"] == ["a.flow", "b.flow"]


def test_one_bad_file_fails_the_run(monkeypatch):
    calls = _stub(monkeypatch, [_cp(0), _cp(1)], flows=("a.flow", "b.flow"))
    assert validate_flow.main() == 1
    assert calls["n"] == 2


def test_budget_exhaustion_reports_instead_of_running(monkeypatch, capsys):
    """When an earlier file consumed the budget, the next one must say so rather
    than start an attempt the harness would SIGKILL mid-flight."""
    # Only two runs queued: a.flow's two stalled attempts spend the whole
    # budget, so a third call would pop an empty queue and fail this test.
    calls = _stub(monkeypatch, [_timeout(), _timeout()], flows=("a.flow", "b.flow"))

    assert validate_flow.main() == 1
    assert calls["flows"] == ["a.flow", "a.flow"]  # b.flow never ran

    err = capsys.readouterr().err
    assert "budget exhausted" in err
    assert "b.flow" in err
    assert "-0s left" not in err  # negative remainder is clamped for display


def test_no_flow_file_fails(monkeypatch, capsys):
    _stub(monkeypatch, [], flows=())
    assert validate_flow.main() == 1
    assert "No .flow file found" in capsys.readouterr().err


@pytest.mark.parametrize(
    "remaining, attempts_left, expected",
    [
        (160.0, 2, 80.0),  # first of two attempts gets half, leaving room to retry
        (75.0, 1, 75.0),  # last attempt may spend everything left
        (0.5, 2, _MIN_ATTEMPT),  # never below the floor
    ],
)
def test_attempt_cap_leaves_room_for_the_retry(
    monkeypatch, remaining, attempts_left, expected
):
    monkeypatch.setattr(validate_flow, "_MIN_ATTEMPT_SECONDS", _MIN_ATTEMPT)
    assert validate_flow._attempt_cap(remaining, attempts_left) == expected


def test_no_attempt_outlives_the_budget(monkeypatch):
    """No attempt may be allowed to run past the deadline, or the harness kill
    beats this module to the failure and the diagnostic is lost again."""
    calls = _stub(monkeypatch, [_timeout(), _timeout()])
    validate_flow.main()
    assert calls["overruns"] == []
    assert sum(calls["timeouts"]) <= _BUDGET - _HEADROOM

"""Unit tests for case_check runtime-payload helpers.

Run with ``pytest`` from any directory.

These pin the CLI #2266 contract: the ``uip maestro case debug --output json``
runtime payload must be readable whether its keys are camelCase (the documented
Studio Web shape, and what the CLI emits once case debug opts into
``preserveDataKeys``) or PascalCase (what a #2266-carrying CLI emits without the
opt-out). A checker must not depend on which CLI build the eval image runs.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from case_check import (  # noqa: E402
    _get_ci,
    collect_outputs,
    run_debug,
)
import case_check  # noqa: E402


def test_get_ci_reads_camelcase_and_pascalcase():
    assert _get_ci({"finalStatus": "Completed"}, "finalStatus", "FinalStatus") == "Completed"
    assert _get_ci({"FinalStatus": "Completed"}, "finalStatus", "FinalStatus") == "Completed"
    assert _get_ci({}, "finalStatus", "FinalStatus", default="<none>") == "<none>"


def test_collect_outputs_handles_pascalcase_payload():
    pascal = {
        "Variables": {
            "Globals": {"result": "approved"},
            "GlobalVariables": [{"Name": "score", "Value": 7}],
            "Outputs": [{"Name": "note", "Value": "done"}],
        }
    }
    out = collect_outputs(pascal)
    assert "approved" in out
    assert 7 in out
    assert "done" in out


def test_collect_outputs_walks_pascalcase_runtime_task():
    """Task executions nested under PascalCase keys must still yield outputs."""
    pascal = {
        "Stages": [
            {
                "Tasks": [
                    {"DisplayName": "Triage", "Type": "rpa", "Outputs": [{"Value": "ok"}]}
                ]
            }
        ]
    }
    assert "ok" in collect_outputs(pascal)


def test_collect_outputs_pascalcase_matches_camelcase():
    camel = {"variables": {"globals": {"a": "x"}, "globalVariables": [{"value": 1}]}}
    pascal = {"Variables": {"Globals": {"a": "x"}, "GlobalVariables": [{"Value": 1}]}}
    assert sorted(map(str, collect_outputs(camel))) == sorted(map(str, collect_outputs(pascal)))


def test_run_debug_gate_accepts_pascalcase_finalstatus(monkeypatch):
    """run_debug's Completed gate must pass on a PascalCase payload (the exact
    #2266 break that made case debug look like it 'did not complete')."""
    monkeypatch.setattr(case_check, "start_debug", lambda **kw: {"FinalStatus": "Completed"})
    assert run_debug() == {"FinalStatus": "Completed"}


def test_run_debug_gate_still_rejects_incomplete(monkeypatch):
    monkeypatch.setattr(case_check, "start_debug", lambda **kw: {"FinalStatus": "Faulted"})
    with pytest.raises(SystemExit, match="Case did not complete"):
        run_debug()

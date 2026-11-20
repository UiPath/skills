"""Checker-level tests for check_coded_agent.py.

The flow on disk is one a passing agent built: a manual trigger, a `uipath.core.agent.<key>` node
`countApprovers` and an end node, with `sentence` in and `approvedCount` out.
Only `run_debug` is replaced, with payloads in the `Data` shape
`uip maestro flow debug --output json` returns.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_coded_agent.py"
REFERENCE_FLOW = HERE / "ApproverCountAgent.reference.flow"
AGENT_ID = "countApprovers"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_coded_agent", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    project = tmp_path / "ApproverCountAgent" / "ApproverCountAgent"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    shutil.copy(REFERENCE_FLOW, project / "ApproverCountAgent.flow")
    monkeypatch.chdir(tmp_path)
    return project


def _payload(globals_, *, agent_status="Completed"):
    return {
        "finalStatus": "Completed",
        "elementExecutions": [
            {"elementId": "start", "status": "Completed"},
            {"elementId": AGENT_ID, "status": agent_status},
            {"elementId": "end", "status": "Completed"},
        ],
        "variables": {"globals": {"sentence": "…", **globals_}},
    }


def _run(payload, monkeypatch):
    checker = _load_checker()
    monkeypatch.setattr(checker, "run_debug", lambda **_: payload)
    checker.main()


@pytest.mark.parametrize("count", [3, "3", 3.0])
def test_agent_ran_and_returned_three_passes(sandbox, monkeypatch, count):
    _run(_payload({"approvedCount": count}), monkeypatch)


def test_three_under_another_output_name_fails(sandbox, monkeypatch):
    # The old grader accepted 3 in any output; the prompt now names approvedCount.
    with pytest.raises(SystemExit) as exc:
        _run(_payload({"approvedCount": None, "total": 3}), monkeypatch)
    assert "approvedCount" in str(exc.value)


def test_wrong_count_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run(_payload({"approvedCount": 5}), monkeypatch)
    assert "expected 3" in str(exc.value)


def test_agent_node_that_did_not_complete_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run(_payload({"approvedCount": 3}, agent_status="Faulted"), monkeypatch)
    assert "did not complete" in str(exc.value)


def test_the_sentence_goes_to_an_input_the_agent_named_itself(tmp_path, monkeypatch):
    """The prompt does not name the input."""
    project = tmp_path / "ApproverCountAgent" / "ApproverCountAgent"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    flow = REFERENCE_FLOW.read_text().replace('"sentence"', '"reviewText"').replace(".sentence", ".reviewText")
    (project / "ApproverCountAgent.flow").write_text(flow)
    monkeypatch.chdir(tmp_path)
    checker = _load_checker()
    sent = {}

    def fake(*, inputs, **_):
        sent.update(inputs)
        return _payload({"approvedCount": 3})

    monkeypatch.setattr(checker, "run_debug", fake)
    checker.main()
    assert sent == {"reviewText": checker.SENTENCE}

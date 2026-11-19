"""The staged request note, and attribution when the agent tests its own build.

The prompt asks the agent to build and test, so its own debug run writes
token-bearing records shortly before the harness's run. The outcome probes
must count only records the harness's run made. No tenant is touched.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

SETUP = Path(__file__).resolve().parent / "_setup"
sys.path.insert(0, str(SETUP))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


seed = _load("seed_outcome_under_test", SETUP / "seed_outcome.py")
probe = _load("outcome_probe_under_test", SETUP / "outcome_probe.py")


def test_seed_stages_the_request_note_with_this_runs_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(seed, "check_connections", lambda: [])

    assert seed.main() == 0

    token = json.loads((tmp_path / "seed.json").read_text())["run_token"]
    note = (tmp_path / "request.md").read_text()
    assert token in note and "{{RUN_TOKEN}}" not in note
    # The connection IDs must sit in a staged file so localize_tenant_ids.py
    # can rewrite them for the running tenant.
    for connection_id in seed.REQUIRED_CONNECTIONS.values():
        assert connection_id in note
    assert not (tmp_path / "sdd.md").exists()


def _floor(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, iso: str) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / probe.DEBUG_RESULT).write_text(json.dumps({"debug_started_at": iso}))


def test_a_record_from_the_agents_own_test_run_is_not_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The agent's run ends seconds before the harness stamps its floor."""
    _floor(monkeypatch, tmp_path, "2026-11-18T10:00:00+00:00")
    agents = {"key": "SJP-1", "created": "2026-11-18T09:59:50Z"}
    harness = {"key": "SJP-2", "created": "2026-11-18T10:00:41Z"}

    assert probe._only_after([agents, harness], "created", "jira") == [harness]


def test_a_record_stamped_seconds_before_the_harness_debug_start_is_not_counted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The harness's run cannot write before it starts; the agent's run can."""
    _floor(monkeypatch, tmp_path, "2026-11-18T10:00:00+00:00")
    early = {"subject": "x", "received": "2026-11-18T09:59:57Z"}
    on_time = {"subject": "y", "received": "2026-11-18T10:00:00Z"}

    assert probe._only_after([early, on_time], "received", "email") == [on_time]

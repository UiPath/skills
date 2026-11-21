"""Teardown contract for the escalation task's Jira helper."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

HERE = Path(__file__).parent


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("escalation_jira_is", HERE / "_setup" / "jira_is.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Result:
    def __init__(self, envelope: object, returncode: int = 0) -> None:
        self.stdout = json.dumps(envelope)
        self.stderr = ""
        self.returncode = returncode


def _stub(monkeypatch: pytest.MonkeyPatch, jira_is: ModuleType, envelope: object) -> list[list[str]]:
    seen: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        seen.append(list(cmd))
        return Result(envelope)

    monkeypatch.setattr(jira_is.subprocess, "run", fake_run)
    return seen


def test_delete_issue_confirms_and_reports_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI refuses an unconfirmed delete with a Failure envelope
    ("Confirmation required … Re-run with --yes"), which `delete_issue`
    correctly reports as NOT confirmed — so every run 08-19 → 09-01 printed
    `WARN: could NOT confirm deletion` and left its ticket in CE. `--yes` is
    the missing word."""
    jira_is = _load_module()
    seen = _stub(monkeypatch, jira_is, {"Result": "Success", "Data": {"Value": ""}})
    assert jira_is.delete_issue("conn", "CE-1257") is True
    (cmd,) = seen
    assert cmd[:5] == ["uip", "is", "resources", "run", "delete"]
    assert "--yes" in cmd and "issueId=CE-1257" in cmd


def test_delete_issue_unconfirmed_failure_is_not_a_deletion(monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load_module()
    _stub(monkeypatch, jira_is, {
        "Result": "Failure",
        "Message": "Confirmation required: this will delete resource 'issue' and cannot be undone.",
        "Instructions": "Re-run with --yes to confirm.",
    })
    assert jira_is.delete_issue("conn", "CE-1257") is False


def test_delete_issue_structured_404_counts_as_gone(monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load_module()
    _stub(monkeypatch, jira_is, {
        "Result": "Failure",
        "Message": "Request failed with status code '404': Issue does not exist or you do not have permission to see it.",
    })
    assert jira_is.delete_issue("conn", "CE-1257") is True


SHARED = HERE.parents[1] / "_shared" / "jira_is.py"
WORKSTREAM = {"Result": "Success", "Data": {"fields": {"summary": "[TEST] ESC-1", "issuetype": {"name": "Workstream"}}}}


def _load_shared() -> ModuleType:
    spec = importlib.util.spec_from_file_location("shared_jira_is", SHARED)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("load", [_load_module, _load_shared])
def test_get_issue_reads_any_issue_type(monkeypatch: pytest.MonkeyPatch, load) -> None:
    jira_is = load()
    seen = _stub(monkeypatch, jira_is, WORKSTREAM)
    fields = jira_is.get_issue("conn", "CE-9")
    assert fields["issuetype"]["name"] == "Workstream"
    (cmd,) = seen
    assert "curated_get_issue" in cmd and "issuetype" not in " ".join(cmd)


@pytest.mark.parametrize("load", [_load_module, _load_shared])
def test_issue_absent_reads_any_issue_type(monkeypatch: pytest.MonkeyPatch, load) -> None:
    jira_is = load()
    seen = _stub(monkeypatch, jira_is, WORKSTREAM)
    assert jira_is.issue_absent("conn", "CE-9") is False
    (cmd,) = seen
    assert "curated_get_issue" in cmd and "issuetype" not in " ".join(cmd)


def _run_teardown(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, patches: dict) -> str:
    import contextlib
    import io
    import sys

    monkeypatch.syspath_prepend(str(HERE / "_setup"))
    monkeypatch.delitem(sys.modules, "jira_is", raising=False)
    import jira_is

    monkeypatch.chdir(tmp_path)
    (tmp_path / ".created_keys").write_text("CE-1 CE-2 CE-3 CE-4 CE-5 CE-6")
    for name, value in patches.items():
        monkeypatch.setattr(jira_is, name, value)
    spec = importlib.util.spec_from_file_location("teardown_jira_run", HERE / "_setup" / "teardown_jira.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.suppress(SystemExit):
        spec.loader.exec_module(module)
    monkeypatch.delitem(sys.modules, "jira_is", raising=False)
    return out.getvalue()


def test_teardown_stops_at_the_deadline_and_stays_under_post_run(monkeypatch, tmp_path) -> None:
    now = [0.0]
    started: list[float] = []

    def slow_delete(_conn, _key):
        started.append(now[0])
        now[0] += 60
        return True

    out = _run_teardown(monkeypatch, tmp_path, {
        "_now": lambda: now[0],
        "connection_id": lambda: "conn",
        "delete_issue": slow_delete,
    })
    assert "skipped CE-3" in out
    assert len(started) == 2
    assert now[0] <= 120


def test_every_call_timeout_is_capped_at_the_remaining_time(monkeypatch) -> None:
    jira_is = _load_module()
    now = [0.0]
    seen: list[float] = []
    monkeypatch.setattr(jira_is, "_now", lambda: now[0])

    def fake_run(cmd, **kwargs):
        seen.append(kwargs["timeout"])
        return Result({"Result": "Success", "Data": {}})

    monkeypatch.setattr(jira_is.subprocess, "run", fake_run)
    jira_is.set_deadline(30)
    jira_is._run("is", "connections", "list")
    now[0] = 25
    jira_is._run("is", "connections", "list")
    now[0] = 31
    with pytest.raises(TimeoutError):
        jira_is._run("is", "connections", "list")
    assert seen == [30, 5]

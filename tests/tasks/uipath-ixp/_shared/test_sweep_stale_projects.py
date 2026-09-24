"""Unit tests for _setup/sweep_stale_projects.py. Run with ``pytest`` from any directory.

The sweep deletes projects on a shared tenant unattended, so what these pin is
the selection rule: never a project younger than STALE_AFTER, never one without
a parseable CreatedAt, never one outside PROJECT_PREFIX. `uip` is stubbed out
everywhere, so no test can reach a tenant.
"""

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "_setup" / "sweep_stale_projects.py"
_spec = importlib.util.spec_from_file_location("sweep_stale_projects", SCRIPT)
sweep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sweep)

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)


def project(name, created_at):
    return {"Name": name, "Title": name, "CreatedAt": created_at}


def aged(name, age, now=NOW):
    return project(name, (now - age).isoformat())


class TestStaleProjects:
    def test_sweeps_only_old_prefixed_projects(self):
        projects = [
            aged("codereval-e2e-old-1a2b3c4d-ixp", timedelta(hours=4)),
            aged("codereval-e2e-live-5e6f7a8b-ixp", timedelta(hours=1)),
            aged("vendor-invoices-5a097334-ixp", timedelta(days=60)),
            aged("flow-build-60e84770-6e3c41c6-ixp", timedelta(days=1)),
        ]
        assert sweep.stale_projects(projects, NOW) == ["codereval-e2e-old-1a2b3c4d-ixp"]

    def test_threshold_is_exclusive(self):
        at_threshold = aged("codereval-integ-a-ixp", sweep.STALE_AFTER)
        past_threshold = aged("codereval-integ-b-ixp", sweep.STALE_AFTER + timedelta(seconds=1))
        assert sweep.stale_projects([at_threshold, past_threshold], NOW) == ["codereval-integ-b-ixp"]

    def test_threshold_outlasts_the_longest_task_budget(self):
        # publish_lifecycle and versions_and_metrics allow 6000s.
        assert sweep.STALE_AFTER > timedelta(seconds=6000)

    @pytest.mark.parametrize("created_at", [None, "", "not-a-date", "2026-13-45T99:00:00"])
    def test_undateable_projects_are_kept(self, created_at):
        assert sweep.stale_projects([project("codereval-e2e-x-ixp", created_at)], NOW) == []

    def test_missing_name_is_skipped(self):
        assert sweep.stale_projects([{"CreatedAt": "2026-01-01T00:00:00+00:00"}], NOW) == []

    @pytest.mark.parametrize("created_at", [
        "2026-09-23T06:00:00.54035+00:00",  # 5-digit fraction, as the tenant emits
        "2026-09-23T06:00:00.1234567+00:00",  # 7-digit fraction
        "2026-09-23T06:00:00Z",
        "2026-09-23T06:00:00",  # naive, read as UTC
    ])
    def test_parses_tenant_timestamp_shapes(self, created_at):
        assert sweep.stale_projects([project("codereval-e2e-x-ixp", created_at)], NOW) == ["codereval-e2e-x-ixp"]

    def test_naive_timestamp_is_utc_not_local(self):
        # One hour old in UTC: must be kept whatever the runner's local zone is.
        young = project("codereval-e2e-x-ixp", (NOW - timedelta(hours=1)).replace(tzinfo=None).isoformat())
        assert sweep.stale_projects([young], NOW) == []

    def test_oldest_first(self):
        projects = [
            aged("codereval-b-ixp", timedelta(hours=5)),
            aged("codereval-a-ixp", timedelta(days=30)),
            aged("codereval-c-ixp", timedelta(hours=4)),
        ]
        assert sweep.stale_projects(projects, NOW) == ["codereval-a-ixp", "codereval-b-ixp", "codereval-c-ixp"]


class FakeUip:
    """Stands in for `sweep.run`: serves one listing, records every delete."""

    def __init__(self, projects, total=None, list_rc=0, failing_deletes=()):
        self.listing = json.dumps({
            "Result": "Success",
            "Data": {"Projects": projects, "Total": len(projects) if total is None else total},
        })
        self.list_rc = list_rc
        self.failing_deletes = set(failing_deletes)
        self.deletes = []

    def __call__(self, cmd, timeout=60):
        if cmd[1:4] == ["ixp", "projects", "list"]:
            return subprocess.CompletedProcess(cmd, self.list_rc, self.listing if self.list_rc == 0 else "", "boom")
        if cmd[1:4] == ["ixp", "projects", "delete"]:
            name = cmd[4]
            self.deletes.append(name)
            rc = 1 if name in self.failing_deletes else 0
            return subprocess.CompletedProcess(cmd, rc, '{"Result": "Failure"}' if rc else '{"Result": "Success"}', "")
        raise AssertionError(f"unexpected uip call: {cmd}")


def tenant(monkeypatch, **kwargs):
    now = datetime.now(timezone.utc)
    fake = FakeUip(
        kwargs.pop("projects", None) or [
            aged("codereval-e2e-old-ixp", timedelta(days=2), now),
            aged("codereval-integ-old-ixp", timedelta(hours=5), now),
            aged("codereval-e2e-live-ixp", timedelta(minutes=20), now),
            aged("ap-invoices-d7aa26ca-ixp", timedelta(days=90), now),
        ],
        **kwargs,
    )
    monkeypatch.setattr(sweep, "run", fake)
    return fake


class TestMain:
    def test_deletes_exactly_the_stale_set(self, monkeypatch):
        fake = tenant(monkeypatch)
        sweep.main()
        assert fake.deletes == ["codereval-e2e-old-ixp", "codereval-integ-old-ixp"]

    def test_a_failed_delete_does_not_stop_the_rest(self, monkeypatch, capsys):
        fake = tenant(monkeypatch, failing_deletes={"codereval-e2e-old-ixp"})
        sweep.main()
        assert fake.deletes == ["codereval-e2e-old-ixp", "codereval-integ-old-ixp"]
        assert "WARN: could not delete 'codereval-e2e-old-ixp'" in capsys.readouterr().out

    def test_failed_listing_deletes_nothing(self, monkeypatch, capsys):
        fake = tenant(monkeypatch, list_rc=1)
        sweep.main()
        assert fake.deletes == []
        assert "could not list projects" in capsys.readouterr().out

    def test_truncated_listing_still_sweeps_what_came_back(self, monkeypatch, capsys):
        fake = tenant(monkeypatch, total=500)
        sweep.main()
        assert fake.deletes == ["codereval-e2e-old-ixp", "codereval-integ-old-ixp"]
        assert "truncated (4 of 500)" in capsys.readouterr().out

    def test_spent_budget_stops_deleting(self, monkeypatch, capsys):
        fake = tenant(monkeypatch)
        monkeypatch.setattr(sweep, "DELETE_BUDGET_SECONDS", -1)
        sweep.main()
        assert fake.deletes == []
        assert "2 left for the next run" in capsys.readouterr().out


def test_script_exits_zero_without_a_cli(tmp_path):
    # PATH holds no `uip`, so this can never reach a real tenant.
    env = dict(os.environ, PATH=str(tmp_path))
    proc = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert proc.returncode == 0
    assert "WARN" in proc.stdout

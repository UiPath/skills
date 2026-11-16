"""Unit tests for _setup/sweep_stale_projects.py. Run with ``pytest`` from any directory.

The sweep deletes projects and AuthZ role assignments on a shared tenant
unattended, so what these pin is the selection rule: never a project younger
than STALE_AFTER, never one without a parseable CreatedAt, never one outside
PROJECT_PREFIX; never an assignment of another tenant, of a live project, or
younger than STALE_AFTER, and no purge at all from a doubtful project list.
`uip` and HTTP are stubbed out everywhere, so no test can reach a tenant.
"""

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "_setup" / "sweep_stale_projects.py"
_spec = importlib.util.spec_from_file_location("sweep_stale_projects", SCRIPT)
sweep = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sweep)
REAL_READ_AUTH = sweep.read_auth

NOW = datetime(2026, 9, 23, 12, 0, tzinfo=timezone.utc)

ORG_ID = "11111111-1111-1111-1111-111111111111"
TENANT_ID = "aaaaaaaa-2222-2222-2222-222222222222"
OTHER_TENANT_ID = "bbbbbbbb-3333-3333-3333-333333333333"
AUTH = {
    "UIPATH_ACCESS_TOKEN": "token",
    "UIPATH_URL": "https://cloud.example",
    "UIPATH_ORGANIZATION_NAME": "org",
    "UIPATH_ORGANIZATION_ID": ORG_ID,
    "UIPATH_TENANT_NAME": "tenant",
    "UIPATH_TENANT_ID": TENANT_ID,
}


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """No test reads the developer's real `.auth` or sends a request unless it opts in."""
    monkeypatch.setattr(sweep, "read_auth", lambda: None)

    def no_network(*args, **kwargs):
        raise AssertionError("unexpected HTTP call")

    monkeypatch.setattr(sweep, "api", no_network)


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
    # PATH holds no `uip`, so the listing fails and the purge, which needs it,
    # never runs: this can never reach a real tenant.
    env = dict(os.environ, PATH=str(tmp_path))
    proc = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, env=env, cwd=tmp_path)
    assert proc.returncode == 0
    assert "WARN" in proc.stdout


def assignment(assignment_id, project_hex, age, tenant_id=TENANT_ID, now=None, **extra):
    created = (now or datetime.now(timezone.utc)) - age
    return {
        "id": assignment_id,
        "scope": f"/tenant/{tenant_id}/Reinfer/project/{project_hex}",
        "createdOn": created.isoformat(),
        "mutable": True,
        **extra,
    }


def live(*hexes):
    return [{"id": h, "name": f"project-{h}-ixp", "created_at": "2026-01-01T00:00:00+00:00"} for h in hexes]


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now


class FakeApi:
    """Stands in for `sweep.api`: pages AuthZ one principal per assignment, records PATCHes."""

    def __init__(self, assignments, projects, projects_error=None, failing_batches=0, clock=None):
        self.principals = [{"roleAssignmentDtos": [a]} for a in assignments]
        self.projects = projects
        self.projects_error = projects_error
        self.failing_batches = failing_batches
        self.clock = clock
        self.assignment_pages = 0
        self.patches = []

    def __call__(self, auth, method, url, headers, body=None):
        parts = urllib.parse.urlsplit(url)
        if parts.path == f"/{ORG_ID}/pap_/api/userroleassignments" and method == "GET":
            query = urllib.parse.parse_qs(parts.query)
            assert (query["scope"], query["serviceName"], query["noInheritance"]) == (["/"], ["Reinfer"], ["false"])
            skip, top = int(query["skip"][0]), int(query["top"][0])
            self.assignment_pages += 1
            return {"totalCount": len(self.principals), "results": self.principals[skip:skip + top]}
        if parts.path == "/org/tenant/reinfer_/api/_private/projects" and method == "GET":
            assert headers["x-uipath-internal-tenantid"] == TENANT_ID
            if self.projects_error:
                raise RuntimeError(self.projects_error)
            return {"status": "ok", "projects": self.projects}
        if parts.path == f"/{ORG_ID}/pap_/api/userroleassignments" and method == "PATCH":
            assert body["roleAssignmentsToAdd"] == []
            self.patches.append(body["roleAssignmentsToDelete"])
            if self.clock:
                self.clock.now += 30
            if len(self.patches) <= self.failing_batches:
                raise RuntimeError("PATCH answered 500")
            return {}
        raise AssertionError(f"unexpected HTTP call: {method} {url}")


def authz(monkeypatch, assignments, projects, **kwargs):
    fake = FakeApi(assignments, projects, **kwargs)
    monkeypatch.setattr(sweep, "read_auth", lambda: dict(AUTH))
    monkeypatch.setattr(sweep, "api", fake)
    return fake


def purged(fake):
    return [i for batch in fake.patches for i in batch]


class TestStaleAssignments:
    def test_only_old_assignments_of_gone_projects(self):
        assignments = [
            ("gone-old", "dead01", (NOW - timedelta(hours=4)).isoformat()),
            ("live-old", "live01", (NOW - timedelta(days=9)).isoformat()),
            ("gone-fresh", "dead02", (NOW - timedelta(minutes=5)).isoformat()),
        ]
        assert sweep.stale_assignments(assignments, {"live01"}, NOW) == ["gone-old"]

    def test_threshold_is_exclusive(self):
        assignments = [
            ("at", "dead01", (NOW - sweep.STALE_AFTER).isoformat()),
            ("past", "dead02", (NOW - sweep.STALE_AFTER - timedelta(seconds=1)).isoformat()),
        ]
        assert sweep.stale_assignments(assignments, set(), NOW) == ["past"]

    @pytest.mark.parametrize("created_on", [None, "", "not-a-date"])
    def test_undateable_assignments_are_kept(self, created_on):
        assert sweep.stale_assignments([("x", "dead01", created_on)], set(), NOW) == []


class TestPurge:
    def test_purges_only_this_tenants_dangling_project_assignments(self, monkeypatch, capsys):
        old = timedelta(hours=5)
        fake = authz(monkeypatch, [
            assignment("gone", "dead01", old),
            assignment("gone-upper", "DEAD02", old, tenant_id=TENANT_ID.upper()),
            assignment("live", "11ve01", old),
            assignment("fresh", "dead03", timedelta(minutes=10)),
            assignment("other-tenant", "dead04", old, tenant_id=OTHER_TENANT_ID),
            assignment("immutable", "dead05", old, mutable=False),
            {**assignment("tenant-level", "", old), "scope": f"/tenant/{TENANT_ID}/Reinfer"},
            {**assignment("no-id", "dead06", old), "id": None},
        ], live("11ve01"))
        sweep.purge_dangling_role_assignments(set())
        assert purged(fake) == ["gone", "gone-upper"]
        assert "OK: purged 2 dangling AuthZ role assignment(s)" in capsys.readouterr().out

    def test_pages_through_every_principal(self, monkeypatch):
        ids = [f"gone-{n}" for n in range(25)]
        fake = authz(monkeypatch, [assignment(i, f"dead{n:02}", timedelta(days=1)) for n, i in enumerate(ids)],
                     live("11ve01"))
        sweep.purge_dangling_role_assignments(set())
        assert fake.assignment_pages == 3
        assert purged(fake) == ids

    def test_batches_deletes_and_a_failed_batch_does_not_stop_the_rest(self, monkeypatch, capsys):
        ids = [f"gone-{n}" for n in range(120)]
        fake = authz(monkeypatch, [assignment(i, f"dead{n:03}", timedelta(days=1)) for n, i in enumerate(ids)],
                     live("11ve01"), failing_batches=1)
        sweep.purge_dangling_role_assignments(set())
        assert [len(batch) for batch in fake.patches] == [50, 50, 20]
        out = capsys.readouterr().out
        assert "WARN: could not delete 50 role assignment(s)" in out
        assert "OK: purged 70 dangling" in out

    def test_spent_budget_stops_deleting(self, monkeypatch, capsys):
        clock = FakeClock()
        monkeypatch.setattr(sweep, "time", clock)
        ids = [f"gone-{n}" for n in range(120)]
        fake = authz(monkeypatch, [assignment(i, f"dead{n:03}", timedelta(days=1)) for n, i in enumerate(ids)],
                     live("11ve01"), clock=clock)
        sweep.purge_dangling_role_assignments(set())
        assert [len(batch) for batch in fake.patches] == [50, 50]
        assert "20 left for the next run" in capsys.readouterr().out

    def test_spent_budget_before_listing_sends_nothing(self, monkeypatch, capsys):
        monkeypatch.setattr(sweep, "PURGE_BUDGET_SECONDS", -1)
        fake = authz(monkeypatch, [assignment("gone", "dead01", timedelta(days=1))], live("11ve01"))
        sweep.purge_dangling_role_assignments(set())
        assert (fake.assignment_pages, fake.patches) == (0, [])
        assert "AuthZ purge skipped: budget spent" in capsys.readouterr().out

    def test_failed_project_list_purges_nothing(self, monkeypatch, capsys):
        fake = authz(monkeypatch, [assignment("gone", "dead01", timedelta(days=1))], live("11ve01"),
                     projects_error="GET answered 403")
        sweep.purge_dangling_role_assignments(set())
        assert fake.patches == []
        assert "WARN: AuthZ purge skipped: GET answered 403" in capsys.readouterr().out

    def test_empty_project_list_purges_nothing(self, monkeypatch, capsys):
        fake = authz(monkeypatch, [assignment("gone", "dead01", timedelta(days=1))], [])
        sweep.purge_dangling_role_assignments(set())
        assert fake.patches == []
        assert "reinfer listed no projects" in capsys.readouterr().out

    def test_project_list_missing_a_cli_project_purges_nothing(self, monkeypatch, capsys):
        fake = authz(monkeypatch, [assignment("gone", "dead01", timedelta(days=1))], live("11ve01"))
        sweep.purge_dangling_role_assignments({"project-11ve01-ixp", "codereval-unseen-ixp"})
        assert fake.patches == []
        assert "lacks 1 project(s) the CLI lists (e.g. 'codereval-unseen-ixp')" in capsys.readouterr().out

    def test_no_assignments_skips_the_project_list(self, monkeypatch, capsys):
        fake = authz(monkeypatch, [], live("11ve01"), projects_error="must not be called")
        sweep.purge_dangling_role_assignments(set())
        assert fake.patches == []
        assert "no Reinfer project-scope role assignments" in capsys.readouterr().out


class TestMainWithPurge:
    def projects(self):
        now = datetime.now(timezone.utc)
        return [
            aged("codereval-e2e-old-ixp", timedelta(days=2), now),
            aged("codereval-e2e-live-ixp", timedelta(minutes=20), now),
        ]

    def test_sweeps_then_purges(self, monkeypatch):
        uip = tenant(monkeypatch, projects=self.projects())
        # The swept project is gone from reinfer; only the unswept one must be listed.
        api = authz(monkeypatch, [assignment("gone", "dead01", timedelta(days=2))],
                    [{"id": "11ve01", "name": "codereval-e2e-live-ixp"}])
        sweep.main()
        assert uip.deletes == ["codereval-e2e-old-ixp"]
        assert purged(api) == ["gone"]

    def test_dry_run_deletes_nothing(self, monkeypatch, capsys):
        uip = tenant(monkeypatch, projects=self.projects())
        api = authz(monkeypatch, [assignment("gone", "dead01", timedelta(days=2))],
                    [{"id": "11ve01", "name": "codereval-e2e-live-ixp"}])
        sweep.main(dry_run=True)
        assert (uip.deletes, api.patches) == ([], [])
        out = capsys.readouterr().out
        assert "would delete ['codereval-e2e-old-ixp']" in out
        assert "would delete ['gone']" in out

    def test_no_auth_still_sweeps(self, monkeypatch, capsys):
        uip = tenant(monkeypatch, projects=self.projects())
        sweep.main()
        assert uip.deletes == ["codereval-e2e-old-ixp"]
        assert "SKIP: no usable .auth file" in capsys.readouterr().out


class TestReadAuth:
    def write(self, path, **overrides):
        values = {**AUTH, **overrides}
        path.write_text("".join(f"{k}={v}\n" for k, v in values.items() if v is not None), encoding="utf-8")
        return str(path)

    def test_reads_the_first_complete_file(self, monkeypatch, tmp_path):
        good = self.write(tmp_path / "good", UIPATH_URL="https://cloud.example/")
        monkeypatch.setattr(sweep, "AUTH_FILES", (str(tmp_path / "missing"), good))
        assert REAL_READ_AUTH() == AUTH

    @pytest.mark.parametrize("overrides", [
        {"UIPATH_URL": "http://cloud.example"},
        {"UIPATH_TENANT_ID": None},
        {"UIPATH_ACCESS_TOKEN": ""},
    ])
    def test_rejects_an_unusable_file(self, monkeypatch, tmp_path, overrides):
        monkeypatch.setattr(sweep, "AUTH_FILES", (self.write(tmp_path / "auth", **overrides),))
        assert REAL_READ_AUTH() is None

"""Audit-exclusion tasks running at the same time against one organization.

The exclusion tasks (create, delete, replace-rename, staged, list, org-scope and
refusal) share one organization's rule set. Run in parallel, they once failed
each other. Skills run 44425066507 is an example: the delete task snapshotted a
rule that another run owned, that rule's owner removed it, and the delete check
then reported collateral deletion that the agent never did.

These tests drive the real setup, cleanup and verify scripts against a fake
organization. They assert that a peer run's test rule (the reserved prefix with
another run's uuid8) is ignored, while a customer rule, an agent-named rule and
this run's own rule are still graded strictly.
"""

import datetime
import importlib.util
import io
import json
import logging
import os
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

ADMIN_DIR = Path(__file__).resolve().parent.parent
SETUP_DIR = ADMIN_DIR / "_setup"
AUDIT_DIR = ADMIN_DIR / "audit"
SETUP_SCRIPT = AUDIT_DIR / "_setup" / "setup_exclusion_rule.py"
CLEANUP_SCRIPT = AUDIT_DIR / "_setup" / "cleanup_exclusion_marker.py"
VERIFY_SCRIPT = AUDIT_DIR / "verify_audit_exclusions.py"

# Ranked by setup_exclusion_rule.rank(): robot login first, then read/decision
# events by name, then the rest.
CATALOG = [
    ("t-rl", "Robot Login"),
    ("t-ev", "Policy Evaluated"),
    ("t-vw", "Asset Viewed"),
    ("t-qa", "Queue Item Added"),
    ("t-pa", "Package Uploaded"),
]
RANKED = ["t-rl", "t-vw", "t-ev", "t-pa", "t-qa"]

NOW = datetime.datetime.now(datetime.timezone.utc)


def iso(delta):
    return (NOW - delta).isoformat().replace("+00:00", "Z")


def rule(policy_id, name, type_id="t-x", created=datetime.timedelta(minutes=5), active=True):
    return {
        "PolicyId": policy_id,
        "Name": name,
        "Enforcement": "Exclude",
        "IsActive": active,
        "Selectors": [
            {"Type": "EventType", "Values": [type_id]},
            {"Type": "Status", "Values": ["Success"]},
        ],
        "CreatedOn": iso(created),
    }


class FakeOrg:
    """Just enough of `uip admin audit org …` for the exclusion scripts.

    `create` refuses a type that another rule already excludes, the way the
    service answers `OverlappingRuleExists`.
    """

    def __init__(self, rules=()):
        self.rules = [dict(r) for r in rules]
        self.created = 0

    def ids(self):
        return {r["PolicyId"] for r in self.rules}

    def __call__(self, args, timeout=30, quiet=False):
        args = list(args)
        if args[:4] == ["admin", "audit", "org", "sources"]:
            types_ = [{"Id": i, "Name": n} for i, n in CATALOG]
            return {"Result": "Success", "Data": [
                {"Name": "Orchestrator", "EventTargets": [{"Name": "Robots", "EventTypes": types_}]},
            ]}
        if args[:5] == ["admin", "audit", "org", "exclusions", "list"]:
            return {"Result": "Success", "Code": "AuditOrgExclusionsList",
                    "Data": [dict(r) for r in self.rules]}
        if args[:5] == ["admin", "audit", "org", "exclusions", "create"]:
            opts, rest = {}, args[5:]
            while rest:
                key = rest.pop(0)
                if key == "--inactive":
                    opts[key] = True
                elif rest:
                    opts[key] = rest.pop(0)
            covered = {v for r in self.rules for s in r["Selectors"]
                       if s["Type"] == "EventType" for v in s["Values"]}
            if opts["--type"] in covered:
                return {"Result": "Failure", "Context": {"errorCode": "OverlappingRuleExists"}}
            self.created += 1
            new = rule(f"pol-new-{self.created}", opts["--name"], opts["--type"],
                       created=datetime.timedelta(0), active="--inactive" not in opts)
            self.rules.append(new)
            return {"Result": "Success", "Data": {"PolicyId": new["PolicyId"]}}
        if args[:5] == ["admin", "audit", "org", "exclusions", "delete"]:
            self.rules = [r for r in self.rules if r["PolicyId"] != args[5]]
            return {"Result": "Success"}
        raise AssertionError(f"unexpected CLI call: {args}")


def run_script(script, org, tmp_path, monkeypatch, **env):
    """Execute a script with `run_cli` stubbed, in tmp_path, under `env`.

    Returns (exit_code, stdout). The scripts call main() at import and exit
    through SystemExit, so each call loads them fresh.
    """
    monkeypatch.chdir(tmp_path)
    for key in [k for k in os.environ if k.startswith("EXCL_")]:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, str(value))

    spec = importlib.util.spec_from_file_location("admin_helpers", SETUP_DIR / "admin_helpers.py")
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    helpers.run_cli = org
    helpers.poll = lambda fn, max_attempts=1, delay=0: fn()
    sys.modules["admin_helpers"] = helpers
    sys.modules.pop("audit_helpers", None)

    buf, code = io.StringIO(), 0
    try:
        with redirect_stdout(buf):
            exec(compile(script.read_text(encoding="utf-8"), str(script), "exec"),
                 {"__name__": "under_test", "__file__": str(script)})
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    finally:
        sys.modules.pop("admin_helpers", None)
        sys.modules.pop("audit_helpers", None)
    return code, buf.getvalue()


def seed(tmp_path):
    path = tmp_path / "seed.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


CUSTOMER = rule("pol-customer", "Mute nightly robot noise", "t-qa", created=datetime.timedelta(days=90))
# A test rule an earlier run left behind (same shape as the 2026-10-15 orphan).
PEER = rule("pol-peer", "ce-audit-excl-create-894b24f9", "t-rl", created=datetime.timedelta(minutes=2))


def test_reserved_prefix_is_the_same_in_all_three_scripts():
    found = {}
    for script in (SETUP_SCRIPT, CLEANUP_SCRIPT, VERIFY_SCRIPT):
        match = re.search(r'^RESERVED_PREFIX = "([^"]+)"', script.read_text(encoding="utf-8"), re.M)
        assert match, f"{script.name} has no RESERVED_PREFIX"
        found[script.name] = match.group(1)
    assert len(set(found.values())) == 1, found


def test_snapshot_leaves_out_a_peer_runs_test_rule(tmp_path, monkeypatch):
    org = FakeOrg([CUSTOMER, PEER])
    run_script(SETUP_SCRIPT, org, tmp_path, monkeypatch, EXCL_SNAPSHOT=1)
    assert seed(tmp_path)["excl_snapshot"] == ["pol-customer"]
    assert seed(tmp_path)["uuid8"]


def delete_scenario(tmp_path, monkeypatch, org):
    run_script(SETUP_SCRIPT, org, tmp_path, monkeypatch, EXCL_SNAPSHOT=1)
    run_script(SETUP_SCRIPT, org, tmp_path, monkeypatch, EXCL_SEED_KEY="rule",
               EXCL_RULE_BASE="ce-audit-excl-delete", EXCL_STATUS="Success", EXCL_TYPE_SLOT=1)
    seeded = seed(tmp_path)["rule"]
    assert seeded["id"] in org.ids(), "the delete scenario did not seed its rule"
    return seeded


def verify_delete(tmp_path, monkeypatch, org):
    return run_script(VERIFY_SCRIPT, org, tmp_path, monkeypatch, EXCL_MODE="absent",
                      EXCL_SEED_KEY="rule", EXCL_EXPECT_SNAPSHOT_INTACT=1)


def test_delete_passes_when_a_peer_rule_disappears_mid_run(tmp_path, monkeypatch):
    """Skills run 44425066507: the peer's owner removed it during the delete task."""
    org = FakeOrg([CUSTOMER, PEER])
    seeded = delete_scenario(tmp_path, monkeypatch, org)
    org.rules = [r for r in org.rules if r["PolicyId"] not in (seeded["id"], "pol-peer")]
    code, out = verify_delete(tmp_path, monkeypatch, org)
    assert code == 0, out


def test_delete_still_fails_when_the_agent_removes_a_customer_rule(tmp_path, monkeypatch):
    org = FakeOrg([CUSTOMER, PEER])
    seeded = delete_scenario(tmp_path, monkeypatch, org)
    org.rules = [r for r in org.rules if r["PolicyId"] not in (seeded["id"], "pol-customer")]
    code, out = verify_delete(tmp_path, monkeypatch, org)
    assert code == 1 and "existed before the run are gone" in out, out


def test_unchanged_ignores_peers_coming_and_going(tmp_path, monkeypatch):
    org = FakeOrg([CUSTOMER, PEER])
    run_script(SETUP_SCRIPT, org, tmp_path, monkeypatch, EXCL_SNAPSHOT=1)
    org.rules = [r for r in org.rules if r["PolicyId"] != "pol-peer"]
    org.rules.append(rule("pol-peer-2", "ce-audit-excl-rename-before-aaaa1111", "t-ev"))
    code, out = run_script(VERIFY_SCRIPT, org, tmp_path, monkeypatch, EXCL_MODE="unchanged")
    assert code == 0, out


@pytest.mark.parametrize("name_of_new_rule", [
    "Mute everything",              # an agent-named rule
    "ce-audit-excl-refusal-{own}",  # a prefixed rule that carries THIS run's uuid8
])
def test_unchanged_still_catches_a_rule_this_run_created(name_of_new_rule, tmp_path, monkeypatch):
    org = FakeOrg([CUSTOMER, PEER])
    run_script(SETUP_SCRIPT, org, tmp_path, monkeypatch, EXCL_SNAPSHOT=1)
    org.rules.append(rule("pol-agent", name_of_new_rule.format(own=seed(tmp_path)["uuid8"]), "t-pa"))
    code, out = run_script(VERIFY_SCRIPT, org, tmp_path, monkeypatch, EXCL_MODE="unchanged")
    assert code == 1 and "created during the run" in out, out


def test_unchanged_still_catches_a_removed_customer_rule(tmp_path, monkeypatch):
    org = FakeOrg([CUSTOMER, PEER])
    run_script(SETUP_SCRIPT, org, tmp_path, monkeypatch, EXCL_SNAPSHOT=1)
    org.rules = [r for r in org.rules if r["PolicyId"] != "pol-customer"]
    code, out = run_script(VERIFY_SCRIPT, org, tmp_path, monkeypatch, EXCL_MODE="unchanged")
    assert code == 1 and "existed before the run are gone" in out, out


def readback(tmp_path, monkeypatch, org, saved_rules):
    (tmp_path / "exclusions.json").write_text(
        json.dumps({"Result": "Success", "Data": saved_rules}), encoding="utf-8")
    return run_script(VERIFY_SCRIPT, org, tmp_path, monkeypatch, EXCL_MODE="readback",
                      EXCL_SAVED_FILE="exclusions.json")


def test_readback_ignores_a_peer_that_came_or_went_after_the_agent_listed(tmp_path, monkeypatch):
    org = FakeOrg([CUSTOMER, rule("pol-peer-2", "ce-audit-excl-staged-before-bbbb2222", "t-ev")])
    code, out = readback(tmp_path, monkeypatch, org, [CUSTOMER, PEER])
    assert code == 0, out


def test_readback_still_fails_when_a_customer_rule_is_missing(tmp_path, monkeypatch):
    org = FakeOrg([CUSTOMER, PEER])
    code, out = readback(tmp_path, monkeypatch, org, [PEER])
    assert code == 1 and "is missing 1" in out, out


def plan(tmp_path, monkeypatch, org, slot):
    run_script(SETUP_SCRIPT, org, tmp_path, monkeypatch, EXCL_SEED_KEY="rule",
               EXCL_RULE_BASE="ce-audit-excl-create", EXCL_PLAN_ONLY=1,
               EXCL_STATUS="Success", EXCL_TYPE_SLOT=slot)
    return seed(tmp_path)["rule"]["type_id"]


def test_plan_only_keeps_robot_login_when_it_is_free(tmp_path, monkeypatch):
    assert plan(tmp_path, monkeypatch, FakeOrg([CUSTOMER]), slot=0) == "t-rl"


def test_plan_only_skips_a_type_another_rule_already_excludes(tmp_path, monkeypatch):
    """The 2026-10-15 orphan covered Robot Login, so the create agent had to take it over."""
    assert plan(tmp_path, monkeypatch, FakeOrg([CUSTOMER, PEER]), slot=0) == "t-vw"


def test_parallel_tasks_get_distinct_event_types(tmp_path, monkeypatch):
    """The four seeding tasks take slots 0-3 and never compete for one type."""
    org = FakeOrg([CUSTOMER])
    seeded = {}
    for slot, base in ((1, "ce-audit-excl-delete"), (2, "ce-audit-excl-rename-before"),
                       (3, "ce-audit-excl-staged-before")):
        task_dir = tmp_path / base
        task_dir.mkdir()
        run_script(SETUP_SCRIPT, org, task_dir, monkeypatch, EXCL_SEED_KEY="rule",
                   EXCL_RULE_BASE=base, EXCL_STATUS="Success", EXCL_TYPE_SLOT=slot)
        seeded[base] = seed(task_dir)["rule"]["type_id"]
    create_dir = tmp_path / "create"
    create_dir.mkdir()
    planned = plan(create_dir, monkeypatch, org, slot=0)
    assert seeded == {
        "ce-audit-excl-delete": RANKED[1],
        "ce-audit-excl-rename-before": RANKED[2],
        "ce-audit-excl-staged-before": RANKED[3],
    }
    assert planned == RANKED[0]


def test_seed_falls_back_in_rank_order_when_its_slot_is_taken(tmp_path, monkeypatch):
    org = FakeOrg([CUSTOMER, rule("pol-peer-vw", "ce-audit-excl-x-cccc3333", "t-vw")])
    run_script(SETUP_SCRIPT, org, tmp_path, monkeypatch, EXCL_SEED_KEY="rule",
               EXCL_RULE_BASE="ce-audit-excl-delete", EXCL_STATUS="Success", EXCL_TYPE_SLOT=1)
    assert seed(tmp_path)["rule"]["type_id"] == "t-rl"


def cleanup_rules(own):
    return [
        rule("pol-own", f"ce-audit-excl-create-{own}", created=datetime.timedelta(minutes=1)),
        rule("pol-orphan", "ce-audit-excl-create-894b24f9", created=datetime.timedelta(days=35)),
        rule("pol-inflight", "ce-audit-excl-create-dddd4444", created=datetime.timedelta(minutes=3)),
        rule("pol-other-marker", "ce-audit-excl-delete-eeee5555", created=datetime.timedelta(days=35)),
        dict(rule("pol-no-date", "ce-audit-excl-create-ffff6666"), CreatedOn=None),
        # An administrator's rule whose name merely mentions the marker: not
        # test-owned, because it doesn't START with the reserved prefix.
        dict(CUSTOMER, Name="Copy of ce-audit-excl-create"),
    ]


def test_cleanup_removes_this_runs_rule_and_old_orphans_only(tmp_path, monkeypatch):
    (tmp_path / "seed.json").write_text(json.dumps({"uuid8": "12ab34cd"}), encoding="utf-8")
    org = FakeOrg(cleanup_rules("12ab34cd"))
    run_script(CLEANUP_SCRIPT, org, tmp_path, monkeypatch, EXCL_CLEANUP_MARKER="ce-audit-excl-create")
    assert org.ids() == {"pol-inflight", "pol-other-marker", "pol-no-date", "pol-customer"}


def test_cleanup_orphan_sweep_can_be_turned_off(tmp_path, monkeypatch):
    (tmp_path / "seed.json").write_text(json.dumps({"uuid8": "12ab34cd"}), encoding="utf-8")
    org = FakeOrg(cleanup_rules("12ab34cd"))
    run_script(CLEANUP_SCRIPT, org, tmp_path, monkeypatch,
               EXCL_CLEANUP_MARKER="ce-audit-excl-create", EXCL_ORPHAN_HOURS=0)
    assert "pol-orphan" in org.ids() and "pol-own" not in org.ids()


OLD = NOW - datetime.timedelta(days=35)


@pytest.mark.parametrize("created_on", [
    # What the service returns, e.g. the 2026-10-15 orphan's "2026-10-15T10:52:22.988Z".
    OLD.strftime("%Y-%m-%dT%H:%M:%S.") + f"{OLD.microsecond // 1000:03d}Z",
    OLD.strftime("%Y-%m-%dT%H:%M:%S.%f") + "1Z",  # the 7-digit .NET form
    OLD.strftime("%Y-%m-%dT%H:%M:%SZ"),
    OLD.strftime("%Y-%m-%dT%H:%M:%S"),  # no offset: read as UTC
])
def test_cleanup_reads_the_service_timestamp_forms(created_on, tmp_path, monkeypatch):
    (tmp_path / "seed.json").write_text(json.dumps({"uuid8": "12ab34cd"}), encoding="utf-8")
    org = FakeOrg([dict(rule("pol-orphan", "ce-audit-excl-create-894b24f9"), CreatedOn=created_on)])
    run_script(CLEANUP_SCRIPT, org, tmp_path, monkeypatch, EXCL_CLEANUP_MARKER="ce-audit-excl-create")
    assert org.ids() == set()


def test_cleanup_says_why_it_left_another_runs_rule(tmp_path, monkeypatch, caplog):
    (tmp_path / "seed.json").write_text(json.dumps({"uuid8": "12ab34cd"}), encoding="utf-8")
    org = FakeOrg([
        dict(rule("pol-undated", "ce-audit-excl-create-ffff6666"), CreatedOn="last month"),
        rule("pol-inflight", "ce-audit-excl-create-dddd4444", created=datetime.timedelta(minutes=3)),
    ])
    with caplog.at_level(logging.INFO):
        run_script(CLEANUP_SCRIPT, org, tmp_path, monkeypatch, EXCL_CLEANUP_MARKER="ce-audit-excl-create")
    assert org.ids() == {"pol-undated", "pol-inflight"}
    assert "ce-audit-excl-create-ffff6666: its CreatedOn 'last month' can't be read" in caplog.text
    assert "ce-audit-excl-create-dddd4444: another run's rule" in caplog.text
    assert "(orphan after 6 h)" in caplog.text


class FakeOrgListingFails(FakeOrg):
    def __call__(self, args, timeout=30, quiet=False):
        if list(args)[:5] == ["admin", "audit", "org", "exclusions", "list"]:
            return {"Result": "Failure", "Message": "HTTP 503"}
        return super().__call__(args, timeout, quiet)


def test_setup_warns_when_it_cannot_skip_covered_types(tmp_path, monkeypatch, caplog):
    with caplog.at_level(logging.INFO):
        assert plan(tmp_path, monkeypatch, FakeOrgListingFails([PEER]), slot=0) == "t-rl"
    assert "Could not list the existing rules, so no covered event type is skipped" in caplog.text

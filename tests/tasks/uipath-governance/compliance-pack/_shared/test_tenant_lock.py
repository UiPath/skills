"""Unit tests for the live e2e's tenant lock (`_setup/tenant_lock.py`).

The lock deletes Orchestrator assets on the shared test tenant unattended, so
its selection rule is pinned here: a regression would delete another run's
live lock, or leave an orphan that stalls every run for STALE_SECONDS.

Runs against an in-memory asset store and a fake clock — no `uip`, no tenant.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

LOCK_PY = Path(__file__).resolve().parent.parent / "_setup" / "tenant_lock.py"


def load_lock():
    spec = importlib.util.spec_from_file_location("tenant_lock", LOCK_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeStore:
    """Asset store behind `run_cli`: names unique per folder unless `dupes`."""

    def __init__(self, dupes=False, fail_list=False, fail_delete=False, key_in_create=True):
        self.assets, self.calls, self.next_key, self.timeouts = [], 0, 1, []
        self.dupes, self.fail_list, self.fail_delete, self.key_in_create = dupes, fail_list, fail_delete, key_in_create

    def seed(self, name, value):
        self.assets.append({"Name": name, "StringValue": value, "Key": f"k{self.next_key}"})
        self.next_key += 1

    def run_cli(self, args, timeout=60):
        self.calls += 1
        self.timeouts.append(timeout)
        if self.calls > 200:
            raise AssertionError("lock loop is spinning without sleeping")
        verb = args[2]
        if verb == "create":
            name, value = args[3], args[4]
            if not self.dupes and any(a["Name"] == name for a in self.assets):
                return None
            self.seed(name, value)
            return {"Result": "Success", "Data": {"Key": self.assets[-1]["Key"]} if self.key_in_create else {}}
        if verb == "list":
            if self.fail_list:
                return None
            needle = args[args.index("--name") + 1]
            return {"Result": "Success", "Data": [dict(a) for a in self.assets if needle in a["Name"]]}
        if verb == "delete":
            if self.fail_delete:
                return None
            self.assets = [a for a in self.assets if a["Key"] != args[3]]
            return {"Result": "Success"}
        raise AssertionError(f"unexpected call {args}")

    def values(self):
        return sorted(a["StringValue"] for a in self.assets)


@pytest.fixture
def env(tmp_path, monkeypatch):
    lock = load_lock()
    store = FakeStore()
    clock = [10_000.0]
    monkeypatch.chdir(tmp_path)  # OWNER_FILE is relative to the sandbox
    monkeypatch.setattr(lock.time, "time", lambda: clock[0])
    monkeypatch.setattr(lock.time, "sleep", lambda s: clock.__setitem__(0, clock[0] + s))
    monkeypatch.setattr(lock, "WAIT_SECONDS", 60.0)
    monkeypatch.setattr(lock, "run_cli", lambda args, timeout=60: store.run_cli(args, timeout))
    return lock, store, clock, tmp_path


def holds(tmp_path) -> bool:
    return (tmp_path / ".compliance-lock-owner").exists()


def test_acquire_then_release(env):
    lock, store, _, tmp = env
    lock.acquire()
    assert holds(tmp)
    assert len(store.assets) == 1
    lock.release()
    assert store.assets == []


def test_second_acquire_step_is_a_no_op(env):
    lock, store, _, tmp = env
    lock.acquire()
    calls = store.calls
    lock.acquire()
    assert store.calls == calls
    assert len(store.assets) == 1


def test_only_an_exact_name_match_counts_as_the_lock(env):
    # `assets list --name` is a contains match; a look-alike must be neither a holder nor deleted.
    lock, store, clock, tmp = env
    store.seed(lock.LOCK_NAME + "-old", f"someone|{clock[0]:.0f}")
    lock.acquire()
    assert holds(tmp)
    assert any(a["Name"] == lock.LOCK_NAME + "-old" for a in store.assets)


def test_live_holder_blocks_and_waiting_run_leaves_nothing_behind(env):
    lock, store, clock, tmp = env
    store.seed(lock.LOCK_NAME, f"holder|{clock[0]:.0f}")
    lock.acquire()
    assert not holds(tmp)
    assert [a["StringValue"].split("|")[0] for a in store.assets] == ["holder"]  # untouched, no orphan


def test_value_without_epoch_is_stale_and_broken(env):
    lock, store, _, tmp = env
    store.seed(lock.LOCK_NAME, "garbage-without-separator")
    lock.acquire()
    assert holds(tmp)
    assert all(not a["StringValue"].startswith("garbage") for a in store.assets)


def test_old_holder_is_broken_after_stale_seconds(env):
    lock, store, clock, tmp = env
    store.seed(lock.LOCK_NAME, f"crashed|{clock[0] - lock.STALE_SECONDS - 100:.0f}")
    lock.acquire()
    assert holds(tmp)
    assert not any(a["StringValue"].startswith("crashed") for a in store.assets)


def test_oldest_entry_wins_when_a_duplicate_slips_through(env):
    lock, store, clock, tmp = env
    store.dupes = True
    store.seed(lock.LOCK_NAME, f"older|{clock[0] - 5:.0f}")
    lock.acquire()
    assert not holds(tmp)
    assert [a["StringValue"].split("|")[0] for a in store.assets] == ["older"]  # ours deleted


def test_list_failure_after_a_successful_create_leaves_no_orphan(env):
    lock, store, _, tmp = env
    store.fail_list = True
    lock.acquire()
    assert not holds(tmp)
    assert store.assets == []


def test_list_failure_without_a_key_in_the_create_response_is_logged(env, caplog):
    lock, store, _, tmp = env
    store.fail_list, store.key_in_create = True, False
    lock.acquire()
    assert not holds(tmp)
    assert "UNLOCKED" in caplog.text


def test_failed_stale_delete_backs_off_instead_of_spinning(env):
    lock, store, clock, tmp = env
    store.fail_delete = True
    store.seed(lock.LOCK_NAME, f"crashed|{clock[0] - lock.STALE_SECONDS - 100:.0f}")
    lock.acquire()  # FakeStore raises after 200 calls if the loop never sleeps
    assert not holds(tmp)


def test_release_deletes_only_this_runs_entry(env):
    lock, store, clock, tmp = env
    lock.acquire()
    store.seed(lock.LOCK_NAME, f"other|{clock[0]:.0f}")
    lock.release()
    assert [a["StringValue"].split("|")[0] for a in store.assets] == ["other"]


def test_release_without_holding_is_a_no_op(env):
    lock, store, clock, _ = env
    store.seed(lock.LOCK_NAME, f"other|{clock[0]:.0f}")
    lock.release()
    assert len(store.assets) == 1
    assert store.calls == 0


def test_stale_window_outlives_a_live_holder():
    # task_timeout 1200s + both 300s lock steps + cleanup/release: a live holder is ~2300s old at most.
    assert load_lock().STALE_SECONDS >= 2300


def test_a_live_but_slow_holder_is_not_broken(env):
    lock, store, clock, tmp = env
    store.seed(lock.LOCK_NAME, f"slow|{clock[0] - 2000:.0f}")
    lock.acquire()
    assert not holds(tmp)
    assert [a["StringValue"].split("|")[0] for a in store.assets] == ["slow"]


def test_step_two_reclaims_the_entry_of_a_killed_step_one(env):
    # Step 1 was killed after its create but before writing OWNER_FILE.
    lock, store, clock, tmp = env
    (tmp / ".compliance-lock-pending").write_text("step-one-owner")
    store.seed(lock.LOCK_NAME, f"step-one-owner|{clock[0] - 30:.0f}")
    lock.acquire()
    assert holds(tmp)
    assert (tmp / ".compliance-lock-owner").read_text() == "step-one-owner"
    assert len(store.assets) == 1


def test_wait_never_runs_past_its_deadline(env):
    lock, store, clock, tmp = env
    store.seed(lock.LOCK_NAME, f"holder|{clock[0]:.0f}")
    start = clock[0]
    lock.acquire()
    assert not holds(tmp)
    assert clock[0] <= start + lock.WAIT_SECONDS  # every sleep is capped by the time left
    assert max(store.timeouts) <= lock.CALL_SECONDS


def test_release_after_a_timed_out_acquire_cleans_up(env):
    lock, store, clock, tmp = env
    (tmp / ".compliance-lock-pending").write_text("me")
    store.seed(lock.LOCK_NAME, f"me|{clock[0]:.0f}")
    store.seed(lock.LOCK_NAME, f"other|{clock[0]:.0f}")
    lock.release()
    assert [a["StringValue"].split("|")[0] for a in store.assets] == ["other"]
    assert not (tmp / ".compliance-lock-pending").exists()

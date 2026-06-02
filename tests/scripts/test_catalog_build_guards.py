"""
Regression tests for scripts/build-uip-catalog.py integrity guards.

Guards added after #1203, where the nightly refresh regenerated the catalog
with the @uipath npm scope pointed at GitHub Packages, installed zero tool
plugins, and collapsed the snapshot from 1115 verbs to the 31 base-CLI verbs.

Run from repo root:
    pytest tests/scripts/test_catalog_build_guards.py
"""

import importlib.util
import subprocess
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = _load("build_uip_catalog", REPO_ROOT / "scripts" / "build-uip-catalog.py")


# --- absolute floor ---------------------------------------------------------

def test_below_absolute_floor_is_rejected():
    """A base-CLI-only catalog (31 verbs) trips the --min-verbs floor."""
    err = build.verb_count_error(31, None, min_verbs=500, max_drop_frac=None)
    assert err is not None
    assert "31" in err and "500" in err


def test_at_or_above_floor_passes():
    err = build.verb_count_error(500, None, min_verbs=500, max_drop_frac=None)
    assert err is None


def test_floor_zero_disables_absolute_check():
    err = build.verb_count_error(1, None, min_verbs=0, max_drop_frac=None)
    assert err is None


# --- relative drop ----------------------------------------------------------

def test_the_1203_collapse_is_rejected():
    """The exact regression: 1115 -> 31 with a 20% max drop."""
    err = build.verb_count_error(31, 1115, min_verbs=0, max_drop_frac=0.2)
    assert err is not None
    assert "1115" in err and "31" in err


def test_drop_within_tolerance_passes():
    """A normal refresh that adds/removes a handful of verbs is fine."""
    err = build.verb_count_error(1100, 1115, min_verbs=0, max_drop_frac=0.2)
    assert err is None


def test_drop_exactly_at_threshold_passes():
    """20% drop of 1000 -> floor 800; 800 is not below floor, so it passes."""
    err = build.verb_count_error(800, 1000, min_verbs=0, max_drop_frac=0.2)
    assert err is None


def test_drop_just_past_threshold_is_rejected():
    err = build.verb_count_error(799, 1000, min_verbs=0, max_drop_frac=0.2)
    assert err is not None


def test_growth_is_always_allowed():
    err = build.verb_count_error(1200, 1115, min_verbs=0, max_drop_frac=0.2)
    assert err is None


# --- no prior snapshot ------------------------------------------------------

def test_no_prior_snapshot_skips_relative_check():
    """First-ever build (prev_count None) can't compute a drop; only the
    absolute floor applies."""
    assert build.verb_count_error(31, None, min_verbs=0, max_drop_frac=0.2) is None
    assert build.verb_count_error(31, 0, min_verbs=0, max_drop_frac=0.2) is None


def test_no_guards_configured_is_noop():
    """Both guards off (defaults) never blocks — preserves prior behaviour for
    local/dev builds that pass no flags."""
    assert build.verb_count_error(0, 1115, min_verbs=0, max_drop_frac=None) is None


# --- --max-drop-frac range validation ---------------------------------------

@pytest.mark.parametrize("bad", ["1.5", "-0.1"])
def test_max_drop_frac_out_of_range_is_rejected(bad):
    """A misconfigured fraction must be rejected up front. >1 yields a negative
    floor that silently disables the relative guard (a collapse would slip
    through); <0 over-inflates the floor. Validate before any work."""
    script = REPO_ROOT / "scripts" / "build-uip-catalog.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--max-drop-frac", bad, "--stdout"],
        capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "between 0 and 1" in (proc.stderr + proc.stdout)


# --- install_all_tools all-fail fatal path (#1203 prevention) ----------------

def test_install_all_tools_exits_when_every_install_fails(monkeypatch):
    """Tools were found but every `uip tools install` failed → abort rather
    than build a base-CLI-only catalog (the #1203 collapse)."""
    def fake_run_uip(argv):
        if argv == ["tools", "list"]:
            return {"Data": []}
        if argv == ["tools", "search"]:
            return {"Data": [{"name": "@uipath/solution-tool"}]}
        return {}
    monkeypatch.setattr(build, "run_uip", fake_run_uip)
    monkeypatch.setattr(
        build.subprocess, "run",
        lambda *a, **k: types.SimpleNamespace(returncode=1, stdout="", stderr="boom"),
    )
    with pytest.raises(SystemExit) as exc:
        build.install_all_tools()
    assert "tool installs failed" in str(exc.value)


def test_install_all_tools_ok_when_nothing_to_install(monkeypatch):
    """Empty search (nothing to install) must NOT exit — distinguishes 'tried
    and all failed' from 'nothing to do'."""
    def fake_run_uip(argv):
        return {"Data": []}
    monkeypatch.setattr(build, "run_uip", fake_run_uip)

    def boom(*a, **k):
        raise AssertionError("subprocess.run should not be called")
    monkeypatch.setattr(build.subprocess, "run", boom)
    build.install_all_tools()  # no SystemExit

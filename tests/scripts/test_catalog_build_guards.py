"""
Regression tests for scripts/build-uip-catalog.py integrity guards.

Guards added after #1203, where the nightly refresh regenerated the catalog
with the @uipath npm scope pointed at GitHub Packages, installed zero tool
plugins, and collapsed the snapshot from 1115 verbs to the 31 base-CLI verbs.

Run from repo root:
    pytest tests/scripts/test_catalog_build_guards.py
"""

import importlib.util
from pathlib import Path

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

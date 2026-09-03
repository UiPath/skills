"""
Regression tests for scripts/check-skills-sh.py, specifically the
--baseline-ref scoping added after the 2026-08-04 blast-radius incident.

uipath-process-mining landed under skills/ on 2026-08-04 (#2252) with no
skills.sh.json entry. Because the check reads the WHOLE tree, the next 48 hours
produced 65 failed runs across ~20 unrelated branches — every PR that touched
any skills/*/SKILL.md — until an unrelated PR (#2498) happened to add the
missing entry. 65 of the check's 68 quarterly failures were that one incident.

The contract these tests pin:
  - drift already present at the baseline never fails the run;
  - drift the change introduces always fails it;
  - an unreadable baseline falls back to strict whole-tree behaviour.

Run from repo root:
    pytest tests/scripts/test_check_skills_sh.py
"""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check = _load("check_skills_sh", REPO_ROOT / "scripts" / "check-skills-sh.py")


def manifest(*groups):
    """A minimal valid manifest: one grouping per (title, *skills) tuple."""
    return {"$schema": check.SCHEMA_URL,
            "groupings": [{"title": title, "skills": list(skills)}
                          for title, *skills in groups]}


def split(head_manifest, head_disk, base_manifest, base_disk):
    """(new, preexisting) for a head state measured against a baseline state."""
    return check.split_by_baseline(check.validate(head_manifest, head_disk),
                                   (base_manifest, base_disk))


# --- the incident ----------------------------------------------------------


def test_preexisting_ungrouped_skill_does_not_fail_an_unrelated_change():
    """The 2026-08-04 case: drift is on the base branch, this PR edits an
    unrelated skill. Reported, but not blocking."""
    base_manifest = manifest(("Authoring", "uipath-rpa"))
    base_disk = {"uipath-rpa", "uipath-process-mining"}

    new, preexisting = split(base_manifest, base_disk, base_manifest, base_disk)

    assert new == []
    assert [f["key"] for f in preexisting] == ["uipath-process-mining"]


def test_newly_added_skill_without_a_grouping_fails():
    """The PR that introduces the drift is the one that must go red."""
    base_manifest = manifest(("Authoring", "uipath-rpa"))
    new, preexisting = split(base_manifest, {"uipath-rpa", "uipath-process-mining"},
                             base_manifest, {"uipath-rpa"})

    assert [f["key"] for f in new] == ["uipath-process-mining"]
    assert preexisting == []


def test_adding_the_missing_entry_clears_the_finding():
    """The fix PR passes even though the baseline was dirty."""
    new, preexisting = split(manifest(("Authoring", "uipath-rpa", "uipath-process-mining")),
                             {"uipath-rpa", "uipath-process-mining"},
                             manifest(("Authoring", "uipath-rpa")),
                             {"uipath-rpa", "uipath-process-mining"})

    assert new == []
    assert preexisting == []


def test_second_new_skill_still_fails_over_a_dirty_baseline():
    """Pre-existing drift must not become a shield for fresh drift."""
    base_manifest = manifest(("Authoring", "uipath-rpa"))
    base_disk = {"uipath-rpa", "uipath-process-mining"}
    new, preexisting = split(base_manifest, base_disk | {"uipath-aops"},
                             base_manifest, base_disk)

    assert [f["key"] for f in new] == ["uipath-aops"]
    assert [f["key"] for f in preexisting] == ["uipath-process-mining"]


# --- renames and removals --------------------------------------------------


def test_rename_fails_on_both_halves():
    """A rename leaves the old name grouped-but-gone and the new name
    ungrouped. Both are this change's fault."""
    new, preexisting = split(manifest(("Authoring", "uipath-old")), {"uipath-new"},
                             manifest(("Authoring", "uipath-old")), {"uipath-old"})

    assert sorted(f["key"] for f in new) == ["uipath-new", "uipath-old"]
    assert preexisting == []


def test_removing_a_skill_without_ungrouping_it_fails():
    new, preexisting = split(manifest(("Authoring", "uipath-rpa", "uipath-gone")),
                             {"uipath-rpa"},
                             manifest(("Authoring", "uipath-rpa", "uipath-gone")),
                             {"uipath-rpa", "uipath-gone"})

    assert [f["key"] for f in new] == ["uipath-gone"]


def test_duplicate_grouping_is_attributed_to_the_change_that_adds_it():
    new, _ = split(manifest(("Authoring", "uipath-rpa"), ("Platform", "uipath-rpa")),
                   {"uipath-rpa"},
                   manifest(("Authoring", "uipath-rpa")), {"uipath-rpa"})

    assert [f["key"] for f in new] == ["uipath-rpa"]


# --- baseline resolution ---------------------------------------------------


def test_unreadable_baseline_returns_none():
    """Fail closed: a shallow clone or missing base must not silently pass."""
    assert check.baseline_state("refs/heads/does-not-exist-abc123") is None


def test_baseline_state_reads_real_history():
    """The baseline is read from git, not the working tree."""
    state = check.baseline_state("HEAD")
    assert state is not None
    baseline_manifest, on_disk = state
    assert baseline_manifest["$schema"] == check.SCHEMA_URL
    assert "uipath-rpa" in on_disk
    assert on_disk == check.skills_on_disk()


def test_unparseable_baseline_manifest_returns_none(monkeypatch):
    monkeypatch.setattr(check, "_git", lambda *args: "{not json")
    assert check.baseline_state("HEAD") is None


# --- the tree is clean today ----------------------------------------------


def test_repo_currently_has_no_drift():
    """Guards the invariant the CI job exists to protect."""
    findings = check.validate(check.load_manifest(), check.skills_on_disk())
    assert findings == [], f"skills.sh.json has drifted: {findings}"


# --- end-to-end exit codes -------------------------------------------------


def run_cli(*args):
    return subprocess.run(["python3", str(REPO_ROOT / "scripts" / "check-skills-sh.py"), *args],
                          capture_output=True, text=True, cwd=REPO_ROOT)


def test_cli_passes_on_the_current_tree():
    assert run_cli().returncode == 0


def test_cli_baseline_ref_accepts_head():
    result = run_cli("--baseline-ref", "HEAD")
    assert result.returncode == 0


def test_cli_warns_and_stays_strict_on_a_bad_baseline():
    result = run_cli("--baseline-ref", "refs/heads/does-not-exist-abc123")
    assert result.returncode == 0  # tree is clean, so nothing to block on
    assert "cannot read baseline" in result.stderr


def test_cli_json_output_carries_the_preexisting_flag():
    result = run_cli("--json", "--baseline-ref", "HEAD")
    assert result.returncode == 0
    for line in result.stdout.splitlines():
        assert "preexisting" in json.loads(line)

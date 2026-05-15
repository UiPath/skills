"""
Regression tests for scripts/check-cli-verbs.py and scripts/check-skill-verbs.py.
Each test reproduces a specific bug surfaced by code review.

Run from repo root:
    pytest tests/scripts/test_verb_checkers.py
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cli = _load("check_cli_verbs", REPO_ROOT / "scripts" / "check-cli-verbs.py")
skill = _load("check_skill_verbs", REPO_ROOT / "scripts" / "check-skill-verbs.py")
build = _load("build_uip_catalog", REPO_ROOT / "scripts" / "build-uip-catalog.py")


# --- Issue 1 (High): mid-token partial truncation ---------------------------

def test_extract_verb_paths_rejects_mid_token_dynamic():
    """`uip\\s+solution\\w+\\s+list` must not produce verb `"solution"`.

    The regex matches things like `uip solutionFoo list`, which is not a real
    verb. The AST walker stops at `\\w+` and currently returns the literal
    prefix `"uip solution"`, so the extractor yields the verb `solution` and
    the classifier matches it (since `solution` is a catalog group). That's a
    false-positive reachable verdict.
    """
    paths = cli.extract_verb_paths(r"uip\s+solution\w+\s+list")
    # The pattern is dynamic mid-verb; the extractor should signal that by
    # returning None (treated as Info) rather than a concrete partial.
    assert paths is None, (
        f"Expected None for mid-token dynamic, got {paths!r}. "
        "This would produce a false 'reachable' verdict for a pattern that "
        "matches no real verb."
    )


def test_extract_verb_paths_rejects_dynamic_after_uip():
    """`uip\\s+\\w+\\s+list` is purely dynamic; must return None."""
    paths = cli.extract_verb_paths(r"uip\s+\w+\s+list")
    assert paths is None


# --- Issue 2 (High): duplicate verb paths ----------------------------------

def test_extract_verb_paths_deduplicates_alternations():
    """`(uip|$UIP)\\s+(maestro\\s+)?flow\\s+init` must yield each verb once."""
    paths = cli.extract_verb_paths(r"(uip|\$UIP)\s+(maestro\s+)?flow\s+init")
    assert paths is not None
    assert len(paths) == len(set(paths)), (
        f"Duplicate verb paths in extraction: {paths!r}. "
        "Inflates 'Top unmatched verbs' counts in the audit report."
    )
    assert set(paths) == {"flow init", "maestro flow init"}


# --- Issue 6 (Medium): redundant OR-clause in severity classification ------

def test_scan_classifies_unwalkable_via_prefix_loop():
    """An unwalkable group should classify a multi-token reference as
    Uncertain via the prefix-iteration loop alone, without needing the
    redundant `tokens[0] in unwalkable` short-circuit."""
    md = REPO_ROOT / "tests" / "scripts" / "_fixture_unwalkable.md"
    md.write_text("Run `uip codedagent init <name>` then deploy.\n")
    try:
        catalog = set()  # empty; we only care about Uncertain via unwalkable
        unwalkable = {"codedagent"}
        findings = skill.scan_file(md, catalog, unwalkable)
        # Exactly one finding for `codedagent init`, classified Uncertain.
        relevant = [f for f in findings if f["verb_path"] == "codedagent init"]
        assert len(relevant) == 1, f"Expected 1 finding, got {findings!r}"
        assert relevant[0]["severity"] == "Uncertain"
    finally:
        md.unlink(missing_ok=True)


# --- Issue 5 (Medium): missing uip → graceful failure ----------------------

def test_run_uip_handles_missing_binary(tmp_path, monkeypatch):
    """When `uip` is not on PATH, run_uip should not crash with
    FileNotFoundError; it should exit with a helpful message."""
    monkeypatch.setenv("PATH", str(tmp_path))  # empty PATH
    # The current implementation raises FileNotFoundError unhandled.
    # After the fix, it should sys.exit with a message.
    with pytest.raises(SystemExit):
        build.run_uip(["--help"])

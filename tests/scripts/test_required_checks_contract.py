"""
Contract guard for the required-status-check set.

A required context is a literal string GitHub waits for. Two edits silently
break it, and both block EVERY open PR until someone edits the ruleset:

  - renaming a job whose name is a required context (the context never
    reports again, so every PR stays pending);
  - re-adding an `on.pull_request.paths:` filter to a workflow that produces
    one (the workflow doesn't run on excluded PRs, so no check is reported).

Neither is visible from the repo: the ruleset lives in the GitHub API, and
nothing in the build reads docs/REQUIRED-CHECKS.md. These tests make the doc's
"Current target set" table the checked source of truth that
scripts/apply-required-checks.sh already parses.

Run from repo root:
    pytest tests/scripts/test_required_checks_contract.py
"""

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "REQUIRED-CHECKS.md"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

# Rows in the doc's table, as `| `Check name` | `workflow.yml` |`.
ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`")


def parse_target_set():
    """Return [(context, workflow_file), ...] from the doc's table."""
    rows, in_table = [], False
    for line in DOC.read_text(encoding="utf-8").splitlines():
        if line.startswith("## Current target set"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if in_table:
            m = ROW.match(line)
            if m:
                rows.append((m.group(1), m.group(2)))
    return rows


def load_workflow(name):
    data = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    # PyYAML parses the bare key `on:` as the boolean True.
    triggers = data.get("on", data.get(True))
    return data, triggers


TARGET_SET = parse_target_set()


def test_table_is_not_empty():
    """A parse failure must not silently pass every other test."""
    assert len(TARGET_SET) >= 15, f"parsed only {len(TARGET_SET)} rows from {DOC}"


def test_no_duplicate_contexts():
    contexts = [c for c, _ in TARGET_SET]
    dupes = {c for c in contexts if contexts.count(c) > 1}
    assert not dupes, f"duplicate contexts in the table: {sorted(dupes)}"


@pytest.mark.parametrize("context,workflow", TARGET_SET, ids=[c for c, _ in TARGET_SET])
def test_context_matches_a_job_name(context, workflow):
    """Every required context names a real job in the workflow the table cites."""
    data, _ = load_workflow(workflow)
    names = {job.get("name") for job in (data.get("jobs") or {}).values()}
    assert context in names, (
        f"{workflow} has no job named {context!r} (found: {sorted(n for n in names if n)}). "
        f"Renaming a job renames its check and breaks the required-status-check "
        f"ruleset — update docs/REQUIRED-CHECKS.md and the ruleset in the same PR."
    )


@pytest.mark.parametrize(
    "workflow", sorted({w for _, w in TARGET_SET}), ids=lambda w: w
)
def test_workflow_has_no_paths_filter(workflow):
    """A `paths:` filter on a required check blocks merge forever when it excludes a PR."""
    _, triggers = load_workflow(workflow)
    assert isinstance(triggers, dict), f"{workflow} has no parseable `on:` block"

    # path-to-ga-approval.yml runs on pull_request_target (it needs write
    # permissions on the PR); everything else on pull_request. Either reports a
    # check on the PR, and a `paths:` filter breaks either one the same way.
    pr_triggers = {
        name: triggers[name] or {}
        for name in ("pull_request", "pull_request_target")
        if name in triggers
    }
    assert pr_triggers, (
        f"{workflow} produces a required check but has no pull_request "
        f"or pull_request_target trigger"
    )

    filtered = [n for n, cfg in pr_triggers.items() if isinstance(cfg, dict) and "paths" in cfg]
    assert not filtered, (
        f"{workflow} produces a required check but filters {filtered} on `paths:`. "
        f"When the filter excludes a PR the workflow never runs, no check is "
        f"reported, and merge blocks forever. Always trigger and short-circuit "
        f"inside the job — a skipped job counts as a pass. "
        f"See docs/REQUIRED-CHECKS.md."
    )


@pytest.mark.parametrize("context,workflow", TARGET_SET, ids=[c for c, _ in TARGET_SET])
def test_required_job_needs_are_covered(context, workflow):
    """A required job must not go green because a job it `needs:` failed.

    `needs: detect` + `if: needs.detect.outputs.skip != 'true'` skips the gated
    job when detect FAILS (its outputs are empty) — and GitHub counts a skipped
    job as a pass. Either the needed job is required too, or the required job
    rolls the results up itself under `if: always()`.
    """
    data, _ = load_workflow(workflow)
    jobs = data.get("jobs") or {}
    job = next(j for j in jobs.values() if j.get("name") == context)

    needs = job.get("needs") or []
    if isinstance(needs, str):
        needs = [needs]
    if not needs:
        return

    if "always()" in str(job.get("if", "")):
        return  # rolls up needs.<job>.result itself

    required = {c for c, _ in TARGET_SET}
    uncovered = [
        key for key in needs
        if (jobs.get(key) or {}).get("name") not in required
    ]
    assert not uncovered, (
        f"{workflow}: required job {context!r} depends on {uncovered}, which "
        f"is not itself required and is not rolled up under `if: always()`. "
        f"If that job fails, {context!r} is skipped — which GitHub counts as a "
        f"pass. See docs/REQUIRED-CHECKS.md Rule 3."
    )


def test_no_two_jobs_share_a_required_context():
    """A context matching two jobs is ambiguous about which run satisfied it."""
    required = {c for c, _ in TARGET_SET}
    owners = {}
    for path in sorted(WORKFLOWS.glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for job in (data.get("jobs") or {}).values():
            name = job.get("name")
            if name in required:
                owners.setdefault(name, []).append(path.name)

    collisions = {n: f for n, f in owners.items() if len(f) > 1}
    assert not collisions, (
        f"required context(s) produced by more than one workflow: {collisions}. "
        f"Qualify one of the job names."
    )

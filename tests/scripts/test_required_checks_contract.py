"""
Contract guard for the required-status-check set.

A required context is a literal string GitHub waits for. Two edits silently
break it, and both block EVERY open PR until someone edits the ruleset:

  - renaming a job whose name is a required context (the context never
    reports again, so every PR stays pending);
  - narrowing a producing workflow's PR trigger — `paths:`, `paths-ignore:`,
    `branches:`, `branches-ignore:`, or a `types:` list missing `synchronize`
    (the workflow doesn't run on excluded PRs, so no check is reported).

A third breaks it loudly instead: a run cancelled by `cancel-in-progress` still
reports its jobs, and `cancelled` is not a pass — so a required context can go
red purely because its run was superseded on a SHA that also has a passing run.
Rule 3a covers keeping the two apart.

Neither of the first two is visible from the repo: the ruleset lives in the
GitHub API, and nothing in the build reads docs/REQUIRED-CHECKS.md. These
tests make the doc's "Current target set" table the checked source of truth. It is parsed by
scripts/parse-required-checks.py — the SAME parser scripts/apply-required-checks.sh
uses, so what is applied is by construction what was validated.

Run from repo root:
    pytest tests/scripts/test_required_checks_contract.py
"""

import importlib.util
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "REQUIRED-CHECKS.md"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
PARSER = REPO_ROOT / "scripts" / "parse-required-checks.py"

# The doc table has exactly ONE parser, shared with
# scripts/apply-required-checks.sh. Re-implementing it here is what let the two
# diverge: a row the script applied to the ruleset could be dropped by a laxer
# regex here and never validated against the workflows.
_spec = importlib.util.spec_from_file_location("parse_required_checks", PARSER)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
parse_target_set = _mod.parse

# The `pull_request` event types a required check must keep. `synchronize` is
# what re-reports the check on every push; without it a stale pass survives.
REQUIRED_PR_TYPES = {"opened", "synchronize", "reopened"}

# Trigger keys that stop a workflow from running on some PRs. Any of them
# starves a required context exactly the way `paths:` does.
NARROWING_KEYS = ("paths", "paths-ignore", "branches", "branches-ignore")


def load_workflow(name):
    data = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    # PyYAML parses the bare key `on:` as the boolean True.
    triggers = data.get("on", data.get(True))
    return data, triggers


TARGET_SET = parse_target_set()


def test_every_table_row_was_parsed():
    """A partial parse must fail loudly, not silently shrink the suite.

    A floor like `>= 15` on a 23-row table lets a parser regression drop 8 rows
    and stay green — and every parametrized test below would then simply not run
    for the dropped contexts. Count the rows independently and demand equality.
    """
    text = DOC.read_text(encoding="utf-8")
    section = text.split("## Current target set", 1)[1].split("\n## ", 1)[0]
    # Every `|`-row in the section except the header and the `|---|` separator.
    rows = [
        ln for ln in section.splitlines()
        if ln.startswith("|")
        and not re.match(r"^\|[\s:|-]+\|?\s*$", ln)
        and not ln.lower().replace(" ", "").startswith("|check|workflow|")
    ]
    assert len(TARGET_SET) == len(rows), (
        f"the table has {len(rows)} data rows but the parser returned "
        f"{len(TARGET_SET)}. A silently dropped row is a context that either "
        f"never reaches the ruleset or reaches it unvalidated."
    )
    assert TARGET_SET, f"parsed zero rows from {DOC}"


def test_no_duplicate_contexts():
    contexts = [c for c, _ in TARGET_SET]
    dupes = {c for c in contexts if contexts.count(c) > 1}
    assert not dupes, f"duplicate contexts in the table: {sorted(dupes)}"


@pytest.mark.parametrize("context,workflow", TARGET_SET, ids=[c for c, _ in TARGET_SET])
def test_context_is_not_an_unexpanded_expression(context, workflow):
    """Rule 1's second cause: an expression job name never matches a context."""
    assert "${{" not in context, (
        f"required context {context!r} is an unexpanded workflow expression. Its "
        f"rendered check name changes per PR, so the fixed context never reports "
        f"and merge blocks forever. Require a fixed-name aggregator job instead "
        f"(see the `gate-summary` jobs in activation-gate.yml / verb-gate.yml) — "
        f"docs/REQUIRED-CHECKS.md Rule 1."
    )


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
def test_workflow_has_no_trigger_filter(workflow):
    """A narrowed trigger on a required check blocks merge forever when it excludes a PR."""
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

    for name, cfg in pr_triggers.items():
        if not isinstance(cfg, dict):
            continue

        narrowed = [k for k in NARROWING_KEYS if k in cfg]
        assert not narrowed, (
            f"{workflow} produces a required check but narrows its `{name}:` "
            f"trigger with {narrowed}. When the filter excludes a PR the "
            f"workflow never runs, no check is reported, and merge blocks "
            f"forever. `paths-ignore`, `branches` and `branches-ignore` starve "
            f"a required context exactly the way `paths` does. Always trigger "
            f"and short-circuit inside the job — a skipped job counts as a "
            f"pass. See docs/REQUIRED-CHECKS.md Rule 1."
        )

        # A `types:` list is legitimate (activation-gate.yml and
        # path-to-ga-approval.yml both add `ready_for_review`), but it must
        # still cover the three events that open a PR and push to it —
        # dropping `synchronize` in particular leaves a stale pass standing.
        types = cfg.get("types")
        if types is not None:
            missing = REQUIRED_PR_TYPES - set(types)
            assert not missing, (
                f"{workflow}'s `{name}.types:` omits {sorted(missing)}, so the "
                f"required check {'/'.join(c for c, w in TARGET_SET if w == workflow)!r} "
                f"would not report on those events. Keep at least "
                f"{sorted(REQUIRED_PR_TYPES)}."
            )


@pytest.mark.parametrize("context,workflow", TARGET_SET, ids=[c for c, _ in TARGET_SET])
def test_required_job_needs_are_covered(context, workflow):
    """A required job must not go green because a job it `needs:` failed.

    `needs: detect` + `if: needs.detect.outputs.skip != 'true'` skips the gated
    job when detect FAILS (its outputs are empty) — and GitHub counts a skipped
    job as a pass. Either the needed job is required too, or the required job
    rolls the results up itself under `if: ${{ !cancelled() }}`.
    """
    data, _ = load_workflow(workflow)
    jobs = data.get("jobs") or {}
    job = next(j for j in jobs.values() if j.get("name") == context)

    needs = job.get("needs") or []
    if isinstance(needs, str):
        needs = [needs]
    if not needs:
        return

    condition = str(job.get("if", ""))

    if "always()" in condition:
        # `always()` also runs during RUN cancellation: the aggregator of a
        # superseded run executes, reads `needs.detect.result == "cancelled"`,
        # and reports the required context FAILED with an error message about a
        # gate that was never actually asked to decide anything.
        #
        # `${{ !cancelled() }}` does not make such a run PASS — GitHub reports
        # the skipped job as `cancelled`, which is non-passing too; keeping two
        # runs off one SHA is the concurrency block's job (Rule 3a). It does
        # resolve the aggregator immediately rather than after a runner
        # acquisition, and drops the misleading error.
        pytest.fail(
            f"{workflow}: required job {context!r} guards its rollup with "
            f"`always()`, which also runs during run cancellation. Use "
            f"`if: ${{{{ !cancelled() }}}}` instead — see "
            f"docs/REQUIRED-CHECKS.md Rule 3."
        )

    if "cancelled()" in condition:
        # `!cancelled()` alone proves nothing — a job that runs and never
        # inspects its needs reports green whatever they did, which is the exact
        # Rule 3 failure. Demand that the job actually reads each one's result.
        body = " ".join(
            str(step.get("run", "")) + " " + str(step.get("env", ""))
            for step in (job.get("steps") or [])
        )
        unread = [key for key in needs if f"needs.{key}.result" not in body]
        assert not unread, (
            f"{workflow}: required job {context!r} runs under "
            f"`if: ${{{{ !cancelled() }}}}` but never reads "
            f"{[f'needs.{k}.result' for k in unread]}. A job that runs "
            f"regardless and ignores its needs reports success no matter what "
            f"they did — the Rule 3 failure this test exists to catch. Either "
            f"roll each result up explicitly, or drop the condition and require "
            f"the needed job instead."
        )
        return

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


def test_every_test_helpers_job_is_required():
    """The reverse direction: a job added to test-helpers.yml must reach the table.

    Every other test here reads the doc and checks it against the workflows, so
    a job that exists but is missing from the table is invisible — the table
    stays internally consistent and the check simply never becomes required.

    That is not hypothetical. `maestro-bpmn checker unit tests` was added to
    this workflow on main, added to the table in a merge commit, and then
    silently dropped when that merge was rebased away: 24 contexts became 23,
    every test still passed.

    test-helpers.yml is the one workflow where the rule is unconditional —
    it exists to hold cheap, deterministic, always-run guards, and each is a
    checkout plus a sub-30s pytest. Anything nondeterministic or advisory
    belongs in another workflow (Rule 4), so there is no legitimate reason for
    a job here to sit outside the required set.
    """
    data, _ = load_workflow("test-helpers.yml")
    names = {job.get("name") for job in (data.get("jobs") or {}).values()}
    required = {c for c, _ in TARGET_SET}

    unregistered = sorted(n for n in names if n and n not in required)
    assert not unregistered, (
        f"test-helpers.yml defines job(s) {unregistered} that are absent from "
        f"docs/REQUIRED-CHECKS.md § Current target set. Every job in this "
        f"workflow is meant to be a required check; add the row in the same PR "
        f"that adds the job, or move the job to another workflow if it is "
        f"advisory (Rule 4)."
    )

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

# The one accepted rollup condition. Anchored so bare `cancelled()` — which
# inverts the guard — cannot satisfy a substring test.
NOT_CANCELLED_RE = re.compile(r"^\s*\$\{\{\s*!\s*cancelled\(\)\s*\}\}\s*$")

# Rule 3a. `synchronize` is the only `pull_request` event that arrives with a new
# head SHA; cancelling on any other one can kill a run on a commit that also has
# a passing run, and `cancelled` is not a pass.
CANCEL_ON_SYNCHRONIZE_RE = re.compile(
    r"^\s*\$\{\{\s*github\.event\.action\s*==\s*'synchronize'\s*\}\}\s*$"
)

# activation-gate.yml is the one required workflow that must fire on
# `ready_for_review`: its `gate` job is skipped on drafts, so a PR opened as a
# draft records a passing (skipped) `Skill activation gate` and, without this
# event, is never re-gated when it becomes ready. Activation changes would then
# merge unmeasured.
WORKFLOW_EXTRA_PR_TYPES = {"activation-gate.yml": {"ready_for_review"}}


def check_names(data):
    """The check name GitHub reports for every job in a workflow.

    A job with no `name:` still produces a context — GitHub falls back to the
    job id. Dropping unnamed jobs (`{j.get("name") for j in ...}` minus the
    falsy ones) is what let an unnamed job slip past the reverse-direction
    guard below.
    """
    return {job.get("name") or job_id for job_id, job in (data.get("jobs") or {}).items()}


def unconsumed_needs(job, needs):
    """Needed jobs whose `result` never reaches failure-producing shell logic.

    A result counts as consumed when a `run:` body references it — directly, or
    through an `env:` var bound to it. Checking the `env:` mapping alone accepts
    a gutted aggregator: keep `DETECT_RESULT: ${{ needs.detect.result }}`,
    replace the `run:` with `echo ok`, and every need looks read.
    """
    steps = job.get("steps") or []
    runs = "\n".join(str(step.get("run", "")) for step in steps)
    unread = []
    for key in needs:
        token = f"needs.{key}.result"
        if token in runs:
            continue
        bound = {
            var
            for step in steps
            for var, value in (step.get("env") or {}).items()
            if token in str(value)
        }
        if not any(re.search(rf"\${{?{re.escape(var)}\b", runs) for var in bound):
            unread.append(key)
    return unread


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
    names = check_names(data)
    assert context in names, (
        f"{workflow} has no job named {context!r} (found: {sorted(names)}). "
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
        expected = REQUIRED_PR_TYPES | WORKFLOW_EXTRA_PR_TYPES.get(workflow, set())
        if types is None:
            # The default set is `opened, synchronize, reopened` — fine unless
            # this workflow needs an event outside it, which it can only get by
            # listing `types:` explicitly.
            missing = expected - REQUIRED_PR_TYPES
        else:
            missing = expected - set(types)
        assert not missing, (
            f"{workflow}'s `{name}.types:` omits {sorted(missing)}, so the "
            f"required check {'/'.join(c for c, w in TARGET_SET if w == workflow)!r} "
            f"would not report on those events. Keep at least "
            f"{sorted(expected)}."
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
        # Match the documented expression exactly. A substring test also accepts
        # the INVERSE, `if: ${{ cancelled() }}` — an aggregator that skips every
        # normal and every failed run while reporting the required context as a
        # pass.
        assert NOT_CANCELLED_RE.search(condition), (
            f"{workflow}: required job {context!r} has `if: {condition}`, which is "
            f"not the documented `if: ${{{{ !cancelled() }}}}`. Bare `cancelled()` "
            f"inverts the guard: the job then skips on every normal run and "
            f"reports the required context as a pass. See "
            f"docs/REQUIRED-CHECKS.md Rule 3."
        )

        # `!cancelled()` alone proves nothing — a job that runs and never
        # inspects its needs reports green whatever they did, which is the exact
        # Rule 3 failure. Demand that each result reaches failure-producing
        # shell logic: mapped into `env:` AND read by a `run:` body.
        #
        # Testing the `env:` mapping alone is not enough. Keep
        # `DETECT_RESULT: ${{ needs.detect.result }}` and replace the `run:`
        # with `echo ok` and the gutted aggregator passes this guard while
        # reporting green whatever its needs did.
        unread = unconsumed_needs(job, needs)
        assert not unread, (
            f"{workflow}: required job {context!r} runs under "
            f"`if: ${{{{ !cancelled() }}}}` but no `run:` step consumes "
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
        f"is not itself required and is not rolled up under "
        f"`if: ${{{{ !cancelled() }}}}` with an explicit result check. "
        f"If that job fails, {context!r} is skipped — which GitHub counts as a "
        f"pass. See docs/REQUIRED-CHECKS.md Rule 3."
    )


@pytest.mark.parametrize(
    "workflow", sorted({w for _, w in TARGET_SET}), ids=lambda w: w
)
def test_concurrency_only_cancels_on_a_new_head_sha(workflow):
    """Rule 3a: a superseded run reports `cancelled`, which is not a pass.

    `cancel-in-progress: true` cancels on every event, including the ones that
    fire on a commit a run is already in flight for — `ready_for_review` (the
    measured PR #3100 case), `reopened` (close and reopen mid-run), `opened`
    (a `workflow_dispatch` run on the same ref). The required context then goes
    red beside a green one on the same SHA, and merge turns on which recorded
    last.
    """
    data, _ = load_workflow(workflow)
    concurrency = data.get("concurrency")
    if not isinstance(concurrency, dict):
        return

    cancel = concurrency.get("cancel-in-progress")
    if cancel is False:
        return

    assert isinstance(cancel, str) and CANCEL_ON_SYNCHRONIZE_RE.search(cancel), (
        f"{workflow} produces a required check and sets "
        f"`cancel-in-progress: {cancel!r}`. Cancelling on an event that does not "
        f"move the head SHA leaves a `cancelled` required context beside a "
        f"passing one on the same commit. Use "
        f"`cancel-in-progress: ${{{{ github.event.action == 'synchronize' }}}}` "
        f"— docs/REQUIRED-CHECKS.md Rule 3a."
    )


def test_no_two_jobs_share_a_required_context():
    """A context matching two jobs is ambiguous about which run satisfied it."""
    required = {c for c, _ in TARGET_SET}
    owners = {}
    # `*.y*ml`: GitHub reads `.yaml` too, and a colliding job in one would be
    # invisible to a `*.yml`-only sweep.
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for name in check_names(data):
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
    names = check_names(data)
    required = {c for c, _ in TARGET_SET}

    unregistered = sorted(n for n in names if n not in required)
    assert not unregistered, (
        f"test-helpers.yml defines job(s) {unregistered} that are absent from "
        f"docs/REQUIRED-CHECKS.md § Current target set. Every job in this "
        f"workflow is meant to be a required check; add the row in the same PR "
        f"that adds the job, or move the job to another workflow if it is "
        f"advisory (Rule 4)."
    )


# --- negative controls for the two guards above -----------------------------
#
# Both guards previously accepted the shape they exist to reject, and both
# rejections are invisible in a green suite unless the bad shape is exercised
# here. These build the aggregator by hand rather than mutating a workflow file.

_ROLLUP_STEPS = [
    {
        "env": {"DETECT_RESULT": "${{ needs.detect.result }}"},
        "run": 'if [ "$DETECT_RESULT" = "failure" ]; then exit 1; fi',
    }
]


def test_bare_cancelled_is_not_accepted_as_the_rollup_condition():
    """`if: ${{ cancelled() }}` is the inverse: it skips every normal run."""
    assert NOT_CANCELLED_RE.search("${{ !cancelled() }}")
    assert NOT_CANCELLED_RE.search("${{ ! cancelled() }}")
    assert not NOT_CANCELLED_RE.search("${{ cancelled() }}")
    assert not NOT_CANCELLED_RE.search("${{ cancelled() || failure() }}")


def test_gutted_rollup_is_reported_as_unconsumed():
    """Mapping a result into `env:` is not consuming it."""
    assert unconsumed_needs({"steps": _ROLLUP_STEPS}, ["detect"]) == []
    gutted = [{"env": _ROLLUP_STEPS[0]["env"], "run": "echo ok"}]
    assert unconsumed_needs({"steps": gutted}, ["detect"]) == ["detect"]
    assert unconsumed_needs({"steps": _ROLLUP_STEPS}, ["detect", "gate"]) == ["gate"]
    inline = [{"run": 'test "${{ needs.gate.result }}" != failure'}]
    assert unconsumed_needs({"steps": inline}, ["gate"]) == []


def test_unnamed_job_still_counts_as_a_check_name():
    """GitHub falls back to the job id, so an unnamed job is a real context."""
    data = {"jobs": {"sneaky-unnamed-job": {"steps": []}, "named": {"name": "Real name"}}}
    assert check_names(data) == {"sneaky-unnamed-job", "Real name"}


def test_cancel_on_synchronize_regex_rejects_the_unconditional_form():
    assert CANCEL_ON_SYNCHRONIZE_RE.search("${{ github.event.action == 'synchronize' }}")
    assert not CANCEL_ON_SYNCHRONIZE_RE.search("true")
    # The deny-list this replaced: correct for ready_for_review, silent on reopened.
    assert not CANCEL_ON_SYNCHRONIZE_RE.search(
        "${{ github.event.action != 'ready_for_review' }}"
    )

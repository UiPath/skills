# Inline Traces Fixture Process Key — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `$TRACES_SMOKE_PROCESS_KEY` with the literal fixture GUID in the two traces e2e task prompts and delete every trace of the env-var wiring, so the tasks pass on the ADO nightly where that variable does not exist.

**Architecture:** No code. Seven text edits across six files — two coder_eval task YAMLs get the GUID inlined plus a provenance comment; two GitHub workflows and two experiment configs lose their env plumbing; `tests/README.md` loses two now-false claims. Verification is a real local `coder-eval` run of both tasks with the variable explicitly unset, which reproduces the exact ADO condition that fails today.

**Tech Stack:** coder_eval task YAML, GitHub Actions YAML, `uip` CLI 1.197.1, Python 3 checker scripts, `tests/.venv/bin/coder-eval`.

## Global Constraints

- Fixture process key, used verbatim everywhere: `bf544b24-9133-41b5-9361-4f9f75c64467`
- Fixture location: `codereval` / `DefaultTenant` on `https://alpha.uipath.com`
- Fixture Orchestrator coordinates (documentation only, nothing reads them): process ID `893686`, folder ID `2824630`, tenant ID `801178`
- Do **not** touch `E2E_PROCESS_KEY` or `E2E_LONG_PROCESS_KEY` — both are wired on the ADO runner and are not broken. Out of scope.
- Do **not** touch the traces smoke tasks (`traces_fetch.yaml`, `traces_feedback_smoke.yaml`) — they already use placeholder GUIDs.
- Do **not** delete the `TRACES_SMOKE_PROCESS_KEY` GitHub secret. It becomes unused; removing org secrets is out of scope.
- Do **not** modify `check_traces_e2e.py` or `check_traces_feedback_e2e.py` — neither reads the env var.
- Repo commit convention: `<type>(<scope>): <imperative summary>`.
- Branch: `fix/move-process-key-traces` (already checked out, based on `main`).

## Deviation from the spec

The spec says only the parenthetical `TRACES_SMOKE_PROCESS_KEY` cross-reference in `tests/README.md` needs editing. That understated it. `tests/README.md:218` cites `traces_e2e.yaml` as the *exemplar* of the env-var shape — and `traces_e2e.yaml` is precisely the file that stops following that shape in Task 2. Task 3 therefore makes two README edits, repointing the exemplar at `orchestrator/job_run_logs_e2e.yaml`, which genuinely still uses `E2E_PROCESS_KEY` via `seed.py`. Total: 7 edits / 6 files, not 6 / 6.

## File Structure

| File | Change | Responsibility after change |
|---|---|---|
| `tests/tasks/uipath-platform/traces/traces_e2e.yaml` | Modify (comment block + prompt line) | Self-contained e2e task; no external env input |
| `tests/tasks/uipath-platform/traces/traces_feedback_e2e.yaml` | Modify (comment block + prompt line + description) | Self-contained e2e task; no external env input |
| `.github/workflows/run-coder-eval.yml` | Modify (`:242`) | Nightly/dispatch eval wiring, minus the dead var |
| `.github/workflows/smoke-skills.yml` | Modify (`:475`, `:485`) | PR-gate smoke wiring + report redaction, minus the dead var |
| `tests/experiments/smoke.yaml` | Modify (`:28`) | Docker passthrough list, minus the dead var |
| `tests/experiments/nightly.yaml` | Modify (`:26`) | Docker passthrough list, minus the dead var |
| `tests/README.md` | Modify (`:218`, `:239-240`) | Tenant-prerequisites docs describing only the two live env vars |

---

### Task 1: Prove the fixture is alive before editing anything

De-risks the whole plan. The spec's Risk section is explicit: if this process no longer emits LLM spans, `check_traces_e2e.py` (`span_count >= 1`) can never pass and the correct fix is a *different* key, not this change. Find that out for the cost of one CLI call, not a wasted agent run.

**Files:**
- Create: none (scratch output only, under `/private/tmp/claude-502/-Users-sakshar-thakkar-repos-skills/1848618d-f03a-4bcf-a369-c7cb9fec54ff/scratchpad/`)
- Modify: none

**Interfaces:**
- Consumes: nothing.
- Produces: a confirmed-live fixture key `bf544b24-9133-41b5-9361-4f9f75c64467` and its resolved `FolderPath`, used by Task 2's prompts and by the Task 4 local run.

- [ ] **Step 1: Switch the local session to the fixture's tenant**

The local session currently points at `joetest / ToBeDeleted`; the fixture lives in `codereval`. This opens a browser popup for approval.

```bash
uip login --organization codereval --tenant DefaultTenant
```

- [ ] **Step 2: Confirm the switch landed**

```bash
uip login status --output json
```

Expected: `"Organization": "codereval"`, `"Tenant": "DefaultTenant"`, `"BaseUrl": "https://alpha.uipath.com"`.

STOP if it still says `joetest` — re-run Step 1 rather than proceeding against the wrong tenant.

- [ ] **Step 3: Confirm the process exists and note its folder**

```bash
uip or processes list --all-folders --limit 200 --output json \
  --output-filter "[?Key=='bf544b24-9133-41b5-9361-4f9f75c64467'].{Name:Name,Key:Key,FolderPath:FolderPath}"
```

Expected: a one-element array. Record `Name` and `FolderPath` — they go in the PR body as fixture provenance.

If the array is empty, the key does not exist on this tenant. STOP and report — do not guess at a substitute key.

- [ ] **Step 4: Start a job and wait for it to finish**

```bash
SCRATCH=/private/tmp/claude-502/-Users-sakshar-thakkar-repos-skills/1848618d-f03a-4bcf-a369-c7cb9fec54ff/scratchpad
uip or jobs start bf544b24-9133-41b5-9361-4f9f75c64467 \
  --wait-for-completion --output json > "$SCRATCH/fixture-job.json"
python3 -c "
import json
d = json.load(open('$SCRATCH/fixture-job.json'))
print('Result:', d.get('Result'))
data = d.get('Data')
jobs = data if isinstance(data, list) else [data]
for j in jobs:
    print('JobKey:', j.get('Key'), '| State:', j.get('State'))
"
```

Expected: `Result: Success` and a job in a terminal state (`Successful`). Copy the `JobKey`.

- [ ] **Step 5: Confirm the job emitted LLM spans**

```bash
uip traces spans get --job-key "<JOB_KEY_FROM_STEP_4>" --output json --output-filter "length(@)"
```

Expected: an integer `>= 1`.

Trace ingestion lags job completion (see the note in `tests/tasks/uipath-platform/orchestrator/job_run_logs_e2e.yaml:6`). If this returns `0`, wait 45 seconds and retry — up to two retries. Only after the third `0` is the fixture genuinely stale.

STOP and report if it stays at `0`: the fixture cannot satisfy `check_traces_e2e.py` and this plan needs a different process key.

- [ ] **Step 6: No commit**

Nothing changed on disk. Proceed to Task 2.

---

### Task 2: Inline the GUID into both task prompts

**Files:**
- Modify: `tests/tasks/uipath-platform/traces/traces_e2e.yaml:14-18`
- Modify: `tests/tasks/uipath-platform/traces/traces_feedback_e2e.yaml:2-9`, `:18`

**Interfaces:**
- Consumes: the confirmed-live key from Task 1.
- Produces: two task YAMLs that read no environment variables. Task 3 asserts nothing in the repo still references `TRACES_SMOKE_PROCESS_KEY`; Task 4 runs these two files.

- [ ] **Step 1: Add the provenance comment and inline the key in `traces_e2e.yaml`**

Replace this exact block:

```yaml
run_limits:
  expected_turns: 21

initial_prompt: |
  Start a new job for the published agent at process key `$TRACES_SMOKE_PROCESS_KEY` and wait for it to finish. Then verify the run produced LLM trace spans and save the raw spans output to spans.json.
```

with:

```yaml
run_limits:
  expected_turns: 21

# Persistent traces fixture (codereval/DefaultTenant, alpha):
#   process key  bf544b24-9133-41b5-9361-4f9f75c64467  (inlined in the prompt below)
#   Orchestrator process ID 893686 · folder ID 2824630 · tenant ID 801178
# Inlined rather than read from TRACES_SMOKE_PROCESS_KEY: that var is wired in
# this repo's GitHub workflows but not in the ADO nightly, so the env-var form
# failed every ADO run. The key is a plain resource identifier, not a secret.
initial_prompt: |
  Start a new job for the published agent at process key `bf544b24-9133-41b5-9361-4f9f75c64467` and wait for it to finish. Then verify the run produced LLM trace spans and save the raw spans output to spans.json.
```

- [ ] **Step 2: Fix the now-false description in `traces_feedback_e2e.yaml`**

Replace this exact block:

```yaml
description: >
  E2E test: agent uses the uipath-platform skill to run a full feedback
  round-trip against a real trace. Starts a job from $TRACES_SMOKE_PROCESS_KEY,
  extracts FolderKey and TraceId from the job/spans output, creates positive
  feedback on that trace, then fetches the feedback by ID and verifies the
  round-trip. No hardcoded IDs — all values derived at runtime.
```

with:

```yaml
description: >
  E2E test: agent uses the uipath-platform skill to run a full feedback
  round-trip against a real trace. Starts a job from the persistent traces
  fixture process, extracts FolderKey and TraceId from the job/spans output,
  creates positive feedback on that trace, then fetches the feedback by ID and
  verifies the round-trip. FolderKey and TraceId are still derived at runtime —
  only the fixture process key is fixed.
```

The old text claimed "No hardcoded IDs — all values derived at runtime." That becomes false the moment the key is inlined. The replacement keeps the claim that is still true and still load-bearing (FolderKey and TraceId are derived), because that is what the task actually exercises.

- [ ] **Step 3: Add the provenance comment and inline the key in `traces_feedback_e2e.yaml`**

Replace this exact block:

```yaml
run_limits:
  expected_turns: 16

initial_prompt: |
  Run a feedback round-trip on a real trace:
  - Start a job for process `$TRACES_SMOKE_PROCESS_KEY` and save the result to job.json
```

with:

```yaml
run_limits:
  expected_turns: 16

# Persistent traces fixture (codereval/DefaultTenant, alpha):
#   process key  bf544b24-9133-41b5-9361-4f9f75c64467  (inlined in the prompt below)
#   Orchestrator process ID 893686 · folder ID 2824630 · tenant ID 801178
# Inlined rather than read from TRACES_SMOKE_PROCESS_KEY: that var is wired in
# this repo's GitHub workflows but not in the ADO nightly, so the env-var form
# failed every ADO run. The key is a plain resource identifier, not a secret.
initial_prompt: |
  Run a feedback round-trip on a real trace:
  - Start a job for process `bf544b24-9133-41b5-9361-4f9f75c64467` and save the result to job.json
```

- [ ] **Step 4: Verify both files still parse and contain the key**

```bash
cd /Users/sakshar.thakkar/repos/skills
python3 -c "
import yaml
for f in ('tests/tasks/uipath-platform/traces/traces_e2e.yaml',
          'tests/tasks/uipath-platform/traces/traces_feedback_e2e.yaml'):
    d = yaml.safe_load(open(f))
    p = d['initial_prompt']
    assert 'bf544b24-9133-41b5-9361-4f9f75c64467' in p, f'{f}: key missing from prompt'
    assert 'TRACES_SMOKE_PROCESS_KEY' not in p, f'{f}: env var still in prompt'
    assert 'TRACES_SMOKE_PROCESS_KEY' not in d['description'], f'{f}: env var still in description'
    print(f, 'OK —', d['task_id'])
"
```

Expected: two `OK` lines, no `AssertionError`.

- [ ] **Step 5: Commit**

```bash
git add tests/tasks/uipath-platform/traces/traces_e2e.yaml \
        tests/tasks/uipath-platform/traces/traces_feedback_e2e.yaml
git commit -m "$(cat <<'EOF'
test(traces): inline the fixture process key into both e2e prompts

TRACES_SMOKE_PROCESS_KEY is wired in this repo's GitHub workflows but absent
from the ADO nightly, so both traces e2e tasks failed every ADO run with an
empty process key. The key is a plain resource identifier on a shared QA
tenant, not a secret, so inline it rather than coordinate a new env var into
another team's pipeline — same call as #1946 for CODED_APPS_TEST_PROJECT_ID.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_015an4PSXw5WBjhBVgfUitkd
EOF
)"
```

---

### Task 3: Delete the wiring and correct the docs

**Files:**
- Modify: `.github/workflows/run-coder-eval.yml:242`
- Modify: `.github/workflows/smoke-skills.yml:475`, `:485`
- Modify: `tests/experiments/smoke.yaml:28`
- Modify: `tests/experiments/nightly.yaml:26`
- Modify: `tests/README.md:218`, `:239-240`

**Interfaces:**
- Consumes: Task 2's inlined prompts (nothing reads the var any more, so removing it is safe).
- Produces: a repo where `grep -rn TRACES_SMOKE_PROCESS_KEY` outside `docs/` returns nothing.

- [ ] **Step 1: Remove the eval-step env entry from `run-coder-eval.yml`**

Delete this line (`:242`) entirely:

```yaml
          TRACES_SMOKE_PROCESS_KEY: ${{ secrets.TRACES_SMOKE_PROCESS_KEY }}
```

Leave the surrounding `E2E_PROCESS_KEY` / `E2E_LONG_PROCESS_KEY` lines untouched. Their extra column padding was aligned to the longer name being deleted; do not realign them — it adds diff noise for zero behavior change.

- [ ] **Step 2: Remove the redact-step env entry from `smoke-skills.yml`**

Delete this line (`:475`) entirely:

```yaml
          TRACES_SMOKE_PROCESS_KEY: ${{ secrets.TRACES_SMOKE_PROCESS_KEY }}
```

- [ ] **Step 3: Remove the name from the redaction tuple in `smoke-skills.yml`**

Delete this line (`:485`) entirely:

```python
              "TRACES_SMOKE_PROCESS_KEY",
```

This is deliberate, not an oversight. Once the GUID is committed to the repo, masking it in eval reports hides nothing and only obscures debugging. The three remaining entries (`UIPATH_CLI_AUTH_TOKEN`, `AWS_BEARER_TOKEN_BEDROCK`, `ANTHROPIC_API_KEY`) are real secrets and stay.

- [ ] **Step 4: Remove the passthrough entry from `tests/experiments/smoke.yaml`**

Delete this line (`:28`) entirely:

```yaml
        - TRACES_SMOKE_PROCESS_KEY
```

- [ ] **Step 5: Remove the passthrough entry from `tests/experiments/nightly.yaml`**

Delete this line (`:26`) entirely:

```yaml
        - TRACES_SMOKE_PROCESS_KEY
```

Keep the `E2E_PROCESS_KEY` and `E2E_LONG_PROCESS_KEY` entries below it.

- [ ] **Step 6: Repoint the README exemplar (`tests/README.md:217-221`)**

`traces_e2e.yaml` no longer receives its process key via env var, so it can no longer be the exemplar of that shape. Replace:

```markdown
`tests/tasks/uipath-platform/{orchestrator,resources}/` and
`tests/tasks/uipath-solution/` follow the same shape as `traces_e2e.yaml`:
the agent receives a process key (and derived folder) via env var, exercises
the operational scenario, and a `check_*.py` script verifies tenant state
directly.
```

with:

```markdown
`tests/tasks/uipath-platform/{orchestrator,resources}/` and
`tests/tasks/uipath-solution/` follow the same shape as
`orchestrator/job_run_logs_e2e.yaml`: the agent receives a process key (and
derived folder) via env var, exercises the operational scenario, and a
`check_*.py` script verifies tenant state directly. The traces e2e tasks are
the exception — they inline their fixture key instead of reading an env var.
```

- [ ] **Step 7: Drop the dead cross-reference (`tests/README.md:239-240`)**

Replace:

```markdown
Two pre-existing processes on the tenant, referenced by their keys via CI
secrets (matches the existing `TRACES_SMOKE_PROCESS_KEY` pattern):
```

with:

```markdown
Two pre-existing processes on the tenant, referenced by their keys via CI
secrets:
```

- [ ] **Step 8: Verify the var is gone and every touched YAML still parses**

```bash
cd /Users/sakshar.thakkar/repos/skills
echo "--- grep gate (expect no output) ---"
grep -rn TRACES_SMOKE_PROCESS_KEY . --exclude-dir=.git --exclude-dir=docs --exclude-dir=.venv || echo "CLEAN"
echo "--- yaml parse gate ---"
python3 -c "
import yaml
for f in ('.github/workflows/run-coder-eval.yml',
          '.github/workflows/smoke-skills.yml',
          'tests/experiments/smoke.yaml',
          'tests/experiments/nightly.yaml'):
    yaml.safe_load(open(f))
    print(f, 'parses OK')
"
```

Expected: `CLEAN`, then four `parses OK` lines. `docs/` is excluded because the spec and this plan legitimately name the variable.

- [ ] **Step 9: Confirm the E2E vars survived untouched**

```bash
grep -rn "E2E_PROCESS_KEY\|E2E_LONG_PROCESS_KEY" \
  .github/workflows/run-coder-eval.yml tests/experiments/nightly.yaml
```

Expected: `run-coder-eval.yml` still shows both env entries; `nightly.yaml` still shows both passthrough entries. These are wired on ADO and must not be collateral damage.

- [ ] **Step 10: Commit**

```bash
git add .github/workflows/run-coder-eval.yml .github/workflows/smoke-skills.yml \
        tests/experiments/smoke.yaml tests/experiments/nightly.yaml tests/README.md
git commit -m "$(cat <<'EOF'
ci(traces): drop TRACES_SMOKE_PROCESS_KEY wiring

Nothing reads the variable now that both traces e2e prompts carry the fixture
key inline. Removes the env entries, the docker passthrough entries, and the
report-redaction entry — masking a GUID that is committed to the repo hides
nothing and only obscures debugging.

Also corrects two README claims the inlining falsified: traces_e2e.yaml is no
longer the exemplar of the env-var shape, and the TRACES_SMOKE_PROCESS_KEY
"pattern" the tenant-prerequisites section cited no longer exists.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_015an4PSXw5WBjhBVgfUitkd
EOF
)"
```

---

### Task 4: Prove it locally under the ADO failure condition

**Files:**
- Modify: none
- Test: `tests/tasks/uipath-platform/traces/traces_e2e.yaml`, `tests/tasks/uipath-platform/traces/traces_feedback_e2e.yaml` (executed, not edited)

**Interfaces:**
- Consumes: Task 2's prompts, Task 3's cleaned wiring, Task 1's confirmed-live fixture and `codereval` session.
- Produces: two task scores for the PR body.

- [ ] **Step 1: Confirm the preconditions the run depends on**

```bash
cd /Users/sakshar.thakkar/repos/skills
uip login status --output json --output-filter "{Org:Organization,Tenant:Tenant}"
test -x tests/.venv/bin/coder-eval && echo "coder-eval present"
test -n "$ANTHROPIC_API_KEY" && echo "ANTHROPIC_API_KEY set" || echo "MISSING ANTHROPIC_API_KEY"
```

Expected: `codereval` / `DefaultTenant`, `coder-eval present`, `ANTHROPIC_API_KEY set`.

`experiments/default.yaml` sets no `API_BACKEND`, so the agent uses the Anthropic direct route and needs that key. If it is missing, STOP and ask — do not fall back to a different experiment config, because `smoke.yaml` and `nightly.yaml` use the docker driver and would need an image build.

- [ ] **Step 2: Run both tasks with the variable explicitly unset**

`env -u` is the whole point: it reproduces the ADO runner's condition, where the variable simply does not exist. A run that inherits a stray `TRACES_SMOKE_PROCESS_KEY` from the shell proves nothing.

```bash
cd /Users/sakshar.thakkar/repos/skills/tests && env -u TRACES_SMOKE_PROCESS_KEY \
  SKILLS_REPO_PATH=/Users/sakshar.thakkar/repos/skills \
  ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  .venv/bin/coder-eval run \
    tasks/uipath-platform/traces/traces_e2e.yaml \
    tasks/uipath-platform/traces/traces_feedback_e2e.yaml \
    -e experiments/default.yaml -v
```

`SKILLS_REPO_PATH` must be the absolute path — `$(cd .. && pwd)` resolves one level too high depending on the invoking shell's working directory.

Expected: both tasks score `1.000`. The two gating checks are `check_traces_e2e.py` (`span_count >= 1`) and `check_traces_feedback_e2e.py` (create ID == get ID, `IsPositive=True`).

- [ ] **Step 3: Record the scores**

Capture, per task: `task_id`, score, and the passed/total criteria count from the run summary. These go verbatim into the PR body — `/lint-task` flags a missing passing-run claim as High severity.

- [ ] **Step 4: Triage honestly if anything failed**

Do not paper over a failure or loosen a success criterion to make it green.

- `span_count = 0` → trace ingestion lag or a stale fixture. Re-run once. If it fails again, the fixture is the problem, not the wiring: STOP and report, per the spec's Risk section.
- Agent never called `uip or jobs start` → the prompt edit likely broke the YAML block scalar. Re-read the prompt as parsed (`yaml.safe_load`) and fix.
- Auth error → the session drifted off `codereval`. Re-run Task 1 Step 1.

- [ ] **Step 5: No commit**

This task produces evidence, not changes.

---

### Task 5: Lint and open the PR

**Files:**
- Modify: none

**Interfaces:**
- Consumes: Task 4's scores.
- Produces: the PR.

- [ ] **Step 1: Lint both task YAMLs**

Run `/lint-task tests/tasks/uipath-platform/traces/traces_e2e.yaml`, then `/lint-task tests/tasks/uipath-platform/traces/traces_feedback_e2e.yaml`.

Fix any High findings. Only run `/audit-verbs` if the linter reports **CLI verb reachability** findings — skip it otherwise.

- [ ] **Step 2: Confirm the branch diff is exactly the intended six files**

```bash
cd /Users/sakshar.thakkar/repos/skills
git diff --stat main...HEAD
```

Expected: the six files from the File Structure table, plus the two `docs/superpowers/` spec and plan files. Anything else is scope creep — remove it.

- [ ] **Step 3: Push and open the PR**

```bash
git push -u origin fix/move-process-key-traces
gh pr create --base main --title "fix(traces): inline the fixture process key — drop TRACES_SMOKE_PROCESS_KEY wiring" --body "$(cat <<'EOF'
## Summary

Both traces e2e tasks (`traces_e2e`, `traces_feedback_e2e`) read the fixture
process key from `TRACES_SMOKE_PROCESS_KEY`. That variable is wired in this
repo's GitHub workflows but **absent from the ADO nightly**, so both tasks
failed every ADO run with an empty process key.

Confirmed by code search across the org:

| Key | `UiPath/skills` (GH) | `UiPath/coder_eval_uipath` (ADO) |
|---|---|---|
| `TRACES_SMOKE_PROCESS_KEY` | wired | **absent** |
| `E2E_PROCESS_KEY` | wired | wired |
| `E2E_LONG_PROCESS_KEY` | wired | wired |

That asymmetry also explains why the tasks passed on Claude runs: Claude fell
back to `E2E_PROCESS_KEY`, which *is* wired on ADO.

Adding the variable to the ADO pipeline means a change in another team's repo.
Per the recommendation in the [eval triage thread](https://uipath-product.slack.com/archives/C0A2T23NJ59/p1784851652554499?thread_ts=1784794186.635559&cid=C0A2T23NJ59),
the key is not a secret, so it is inlined here instead — same call as #1946
for `CODED_APPS_TEST_PROJECT_ID`.

## Changes

- **Both traces e2e prompts**: `bf544b24-…` inlined, with a provenance comment
  recording the fixture's org/tenant and Orchestrator coordinates.
- **`traces_feedback_e2e` description**: dropped the now-false claim "No
  hardcoded IDs — all values derived at runtime", narrowed to what is still
  true and load-bearing (FolderKey and TraceId are derived at runtime).
- **Wiring removed**: env entries in `run-coder-eval.yml` and
  `smoke-skills.yml`, passthrough entries in `smoke.yaml` / `nightly.yaml`, and
  the report-redaction entry. Masking a GUID that is committed to the repo
  hides nothing and only obscures debugging.
- **`tests/README.md`**: repointed the env-var-shape exemplar off
  `traces_e2e.yaml` (which no longer follows it) onto
  `orchestrator/job_run_logs_e2e.yaml`, and dropped the dead
  `TRACES_SMOKE_PROCESS_KEY` cross-reference.

`E2E_PROCESS_KEY` / `E2E_LONG_PROCESS_KEY` are untouched — both are wired on
ADO and not broken. The now-unused GitHub secret is left in place.

## Verification

Both tasks run locally with `env -u TRACES_SMOKE_PROCESS_KEY`, reproducing the
ADO condition that fails today:

- `skill-platform-traces-e2e` — **<SCORE from Task 4>**
- `skill-platform-traces-feedback-e2e` — **<SCORE from Task 4>**

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_015an4PSXw5WBjhBVgfUitkd
EOF
)"
```

Substitute the two real scores from Task 4 Step 3 before running. Do not open the PR with the placeholders in place.

---

## Self-Review

**Spec coverage:**

| Spec section | Task |
|---|---|
| Inline GUID in both prompts | Task 2 Steps 1, 3 |
| Fixture provenance comment | Task 2 Steps 1, 3 |
| `traces_feedback_e2e` description contradiction | Task 2 Step 2 |
| 6 wiring removals | Task 3 Steps 1-5, 7 |
| README exemplar correction (spec understated) | Task 3 Step 6 — flagged under "Deviation from the spec" |
| Verification steps 1-2 (login, fixture check) | Task 1 Steps 1-5 |
| Verification step 3 (local run, var unset) | Task 4 Step 2 |
| Verification step 4 (grep gate) | Task 3 Step 8 |
| Verification step 5 (lint + PR claims) | Task 5 Steps 1, 3 |
| Risk: stale fixture → stop, don't paper over | Task 1 Step 5, Task 4 Step 4 |
| Non-goal: `E2E_*` untouched | Task 3 Step 9 asserts it |
| Non-goal: secret not deleted | Global Constraints |
| Non-goal: smoke tasks untouched | Global Constraints; Task 5 Step 2 asserts diff scope |

No gaps.

**Placeholder scan:** The only bracketed tokens are `<JOB_KEY_FROM_STEP_4>` (Task 1 Step 5) and `<SCORE from Task 4>` (Task 5 Step 3). Both are runtime values that cannot exist at authoring time, and each has an explicit instruction naming the step that produces it. No "TBD", no "add appropriate error handling", no "similar to Task N" — the provenance comment block is repeated in full in Task 2 Steps 1 and 3 rather than cross-referenced.

**Type consistency:** The GUID `bf544b24-9133-41b5-9361-4f9f75c64467` is byte-identical in Global Constraints, both Task 2 edits, and Task 1's lookup and job-start commands. File paths and line numbers were read from the working tree, not recalled. `check_traces_e2e.py` / `check_traces_feedback_e2e.py` are named consistently and, per Global Constraints, unmodified.

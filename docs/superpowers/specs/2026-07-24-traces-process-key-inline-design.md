# Inline the traces fixture process key — drop `TRACES_SMOKE_PROCESS_KEY` wiring

**Date:** 2026-07-24
**Branch:** `fix/move-process-key-traces`
**Scope:** `tests/tasks/uipath-platform/traces/` + CI env wiring

## Problem

The two traces e2e tasks read the fixture process key from the
`TRACES_SMOKE_PROCESS_KEY` env var:

- `tests/tasks/uipath-platform/traces/traces_e2e.yaml`
- `tests/tasks/uipath-platform/traces/traces_feedback_e2e.yaml`

The var is wired in this repo's GitHub workflows but **not** in the Azure
DevOps nightly that produces the Slack scorecard. Confirmed by code search:

| Key | `UiPath/skills` (GH) | `UiPath/coder_eval_uipath` (ADO) |
|---|---|---|
| `TRACES_SMOKE_PROCESS_KEY` | wired | **absent** |
| `E2E_PROCESS_KEY` | wired | wired (`coder-eval-daily.yml`) |
| `E2E_LONG_PROCESS_KEY` | wired | wired (`coder-eval-daily.yml`) |

With the var empty, the agent has no process to start, so both traces tasks
fail every ADO nightly. The failures surfaced in the
[2026-07-23 codex run thread](https://uipath-product.slack.com/archives/C0A2T23NJ59/p1784851652554499?thread_ts=1784794186.635559&cid=C0A2T23NJ59).
They passed on Claude runs only incidentally: Claude fell back to
`E2E_PROCESS_KEY`, which *is* wired on ADO.

Adding the var to the ADO pipeline means a change in another repo owned by
another team. Bai Li's recommendation in the thread: the key is not a secret,
so inline it in this repo instead. Precedent —
[PR #1946](https://github.com/UiPath/skills/pull/1946) did exactly this for
`CODED_APPS_TEST_PROJECT_ID`.

This design follows that precedent.

## Non-goals

- `E2E_PROCESS_KEY` / `E2E_LONG_PROCESS_KEY` stay as env vars. They are wired
  on both runners, so they are not broken and are out of scope.
- The `TRACES_SMOKE_PROCESS_KEY` GitHub secret is not deleted. It becomes
  unused; removing org secrets is not part of this change.
- The traces smoke tasks (`traces_fetch.yaml`, `traces_feedback_smoke.yaml`)
  are untouched — they already use placeholder GUIDs and never read the var.

## The fixture

Persistent process on **alpha**, `codereval / DefaultTenant`:

| Field | Value |
|---|---|
| Process key (GUID) | `bf544b24-9133-41b5-9361-4f9f75c64467` |
| Orchestrator process ID | `893686` |
| Folder ID (`fid`) | `2824630` |
| Tenant ID (`tid`) | `801178` |

The GUID is a plain resource identifier on a shared QA tenant — no auth
value, safe to commit. The numeric IDs are recorded for fixture maintenance
only; nothing reads them.

## Changes

### 1. Task prompts — inline the GUID

Both files: replace `$TRACES_SMOKE_PROCESS_KEY` with the literal GUID, and add
a fixture-provenance comment above `initial_prompt` recording the table above
(PR #1946 comment style).

`traces_feedback_e2e.yaml` needs two extra description edits:

1. Its `description` interpolates `$TRACES_SMOKE_PROCESS_KEY` — replace with
   plain wording naming the fixture process.
2. Its `description` claims *"No hardcoded IDs — all values derived at
   runtime."* That becomes false. Narrow it to the claim that is still true
   and load-bearing: **FolderKey and TraceId** are derived at runtime; the
   process key is now fixed.

No success criteria change. No checker-script change — `check_traces_e2e.py`
and `check_traces_feedback_e2e.py` never read the env var.

### 2. Remove the wiring — 6 sites

| File | Removal |
|---|---|
| `.github/workflows/run-coder-eval.yml` | `TRACES_SMOKE_PROCESS_KEY:` env entry (eval step) |
| `.github/workflows/smoke-skills.yml` | env entry on the redact-secrets step |
| `.github/workflows/smoke-skills.yml` | the name inside the redaction `names` tuple |
| `tests/experiments/smoke.yaml` | `env_passthrough_extra` entry |
| `tests/experiments/nightly.yaml` | `env_passthrough_extra` entry |
| `tests/README.md` | the "matches the existing `TRACES_SMOKE_PROCESS_KEY` pattern" phrasing in § Tenant prerequisites — the pattern it cites stops existing |

Dropping the key from the redaction tuple is deliberate. Once the GUID is
committed, masking it in eval reports hides nothing and only obscures
debugging. The remaining redaction entries (auth token, Bedrock token,
Anthropic key) are unaffected.

`tests/README.md` § Lifecycle E2E tests also describes the env-var shape as
"the agent receives a process key ... via env var". That sentence describes
the `E2E_PROCESS_KEY` / `seed.py` pattern, which is unchanged — only the
parenthetical cross-reference to `TRACES_SMOKE_PROCESS_KEY` is edited.

## Verification

1. `uip login --organization codereval --tenant DefaultTenant` — local session
   currently points at `joetest / ToBeDeleted`; the fixture lives in
   `codereval`.
2. Confirm the fixture exists and note its folder:
   `uip or processes list --all-folders --output json` contains
   `bf544b24-9133-41b5-9361-4f9f75c64467`.
3. Run both tasks locally with the var **explicitly unset** — this reproduces
   the ADO condition that fails today:

   ```bash
   cd tests && env -u TRACES_SMOKE_PROCESS_KEY \
     SKILLS_REPO_PATH=/Users/sakshar.thakkar/repos/skills \
     .venv/bin/coder-eval run \
       tasks/uipath-platform/traces/traces_e2e.yaml \
       tasks/uipath-platform/traces/traces_feedback_e2e.yaml \
       -e experiments/default.yaml -v
   ```

   Both must score `1.000`.
4. Gate: `grep -rn TRACES_SMOKE_PROCESS_KEY .` returns no hits.
5. `/lint-task` on both task YAMLs.
6. PR body records the local passing-run scores (`/lint-task` flags a missing
   passing-run claim as High).

## Risk

Step 3 is the first real check that this process still emits LLM spans —
`check_traces_e2e.py` gates on `span_count >= 1`. If it returns 0, the fixture
is stale and the correct fix is a different process key, not this change. In
that case: stop, report, and pick a new fixture rather than ship a key that
cannot pass.

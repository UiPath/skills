# tests/tasks/uipath-troubleshoot — Test Scenario Generator

This directory contains regression tests for the `uipath-troubleshoot` skill. Each scenario replays a real troubleshooting investigation against a `uip` CLI mock so the agent's reasoning is exercised without hitting a real UiPath tenant.

This file tells you (Claude or a contributor) how to **add a new scenario** from a real session you just resolved.

## When to use this guide

Trigger:

- You ran the `uipath-troubleshoot` skill against a real failing job, reached a verified resolution, and want to lock the case in as a regression test.
- A user reports a new failure class not yet covered by an existing scenario.

Skip:

- Tweaking an existing scenario's manifest or fixtures — edit them directly, no generation pass needed.
- Adding tests for *other* skills — use `.claude/commands/generate-tasks.md` instead.

## Inputs

A new scenario needs four sources. Three are mandatory; the fourth is optional.

| Input | Required | Source |
|-------|----------|--------|
| `--investigation <dir>` | yes | The `.local/investigations/` directory written by the troubleshooting skill: `state.json`, `hypotheses.json`, `evidence/`, `raw/`, `depth-check.json`. |
| `--project <dir>` | no | The UiPath project source that was failing. Snapshotted into the new scenario's `process/`. Omit when the troubleshooting is purely CLI-driven (no project source available). |
| `--transcript <path>` | yes | A `.jsonl` file or a directory. Directory mode walks `*.jsonl` recursively and treats files under `subagents/` as sub-agent transcripts (their `uip` calls count, their final text is ignored). Source of truth for `uip` calls + presenter output. |
| `--resolution <file>` | no | Pre-written `RESOLUTION.md`. If omitted, the generator extracts the presenter's final assistant message from the transcript. |
| `--scenario-name <name>` | no | Folder name for the new scenario. If omitted, inferred from project name + failing job key. |

## Workflow — ask before writing

The generator runs in two passes. **Always preview before applying.**

### 1. Preview

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
  --investigation <path> \
  --project <path> \
  --transcript <path> \
  [--resolution <path>] \
  [--scenario-name <name>] \
  --dry-run
```

Output: a plan describing every file that would be written (paths + sizes + first lines), the inferred scenario name, the manifest rules extracted, and any scrub substitutions that would be applied.

### 2. Confirm with the user

Show the preview. Ask:

- Is the scenario name correct?
- Are the manifest rules complete (every `uip` arg signature the agent ran)?
- Does the extracted `RESOLUTION.md` match the agent's final answer? (Or should they supply one explicitly?)
- Are the scrub substitutions correct (placeholders mapped to the right real values)?

Do not proceed without explicit user confirmation.

### 3. Apply

```bash
python tests/tasks/uipath-troubleshoot/_shared/scripts/generate_scenario.py \
  ... same flags as preview ... \
  --apply
```

Writes the scenario folder. Prints the path. Exits.

### 4. Verify

After write:

1. Run the smoke test pattern to confirm the mock dispatcher resolves:
   ```bash
   cd tests
   .venv/bin/coder-eval run tasks/uipath-troubleshoot/<scenario>/task.yaml -e experiments/default.yaml -v
   ```
2. The first run should score 1.0 — the test was generated from a known-good resolution.
3. Open `mocks/.calls.jsonl` from the run artifact to confirm every expected call was hit.

## Mandatory scrub list

Before writing any file, the generator MUST replace:

| Pattern | Replacement |
|---------|-------------|
| Personal Windows paths (`D:\...`, `C:\Users\...`, etc.) | Strip prefix → relative path, OR generic description |
| Real internal email addresses (`<name>@uipath.com`) | `original_email@test.com` (resource owner), `replacement_email@test.com` (runner) |
| Real first names used as identifiers | `original_user`, `replacement_user` |
| Filenames containing real emails | Renamed to placeholder |
| Hostnames matching `DESKTOP-*`, `<surname>-*` | `MOCK-HOST` |

Scrub applies to: every fixture JSON, every Markdown body, every YAML field, every filename in the `process/` snapshot.

The generator MUST surface its scrub-substitution table during the dry-run preview so the user can verify mappings before write.

## Scenario folder layout

```
tests/tasks/uipath-troubleshoot/<scenario-name>/
├── task.yaml                    # tags, mock_path_dirs, llm_judge criteria
├── README.md                    # what the original session uncovered
├── RESOLUTION.md                # ground truth for the LLM judge
├── fixtures/
│   └── mocks/
│       └── responses/
│           ├── manifest.json    # rules (canned + passthrough) + unmocked_default
│           └── *.json           # canned stdout per rule with `file:`
└── process/                     # snapshot of the failing UiPath project (optional)
    └── ...
```

`task.yaml` MUST set `sandbox.mock_path_dirs: ["mocks"]` — without it, bare `uip` resolves to the real CLI and the test will try to authenticate.

## Mock dispatch precedence

The shared `mocks/uip` dispatcher walks the manifest's `rules` array (first match wins). Each rule has one of:

- `file: <path>` — return the canned response under `responses/<file>`.
- `passthrough: true` — proxy to the real `uip` CLI installed on the host. Use this for open-ended commands like `docsai ask` whose query strings vary between runs. Responses are cached to the sandbox's `responses/_cache/<key>.json` for in-run reuse; the cache is **not** persisted to the source — every run hits the live CLI on its first call for each unique query.

When no rule matches:

1. `unmocked_default` (if set) — return its `response` + `exit_code`.
2. Otherwise, error on stderr.

Test runs require valid `uip` auth on the host (set via `.env` or environment) for any rule with `passthrough: true` to succeed.

## Task YAML requirements

Every new scenario's `task.yaml` MUST satisfy the following.

### `run_limits`

```yaml
run_limits:
  task_timeout: 5400
  max_turns: 60
  turn_timeout: 3600
```

Troubleshooting investigations span many turns and produce large intermediate outputs. Use `task_timeout: 5400` (90 min) and `turn_timeout: 3600` (60 min) so the full triage → hypothesis → tester → depth-check → presenter chain has headroom — proxy-mode runs cluster around 25–55 min wall, so a 30-min `task_timeout` clips right before the presenter spawn on the slow end of the distribution.

`task_timeout`, `max_turns`, and `turn_timeout` belong inside the `run_limits:` block (the canonical location after the c/2026-05-12-unify-run-limits migration). Top-level placement still works via a grace shim but is deprecated; setting both top-level and `run_limits:` raises `ValueError` on the validator.

### `tags`

Tags MUST be lowercase kebab-case — the coder-eval schema rejects PascalCase or spaced names (e.g., `RPA` and `Integration Service` are invalid; use `rpa` and `integration-service`).

Must include `uipath-troubleshoot` AND at least one product/domain tag from this list:

| Tag | When to apply |
|-----|---------------|
| `rpa` | Anything touching an activity package or `.xaml` workflow. **Default for any activity-package-related failure.** Apply alongside other tags when the failure spans domains (e.g., a preflight that hits both System.Activities and IS connectors gets both `rpa` and `integration-service`). |
| `flow` | Maestro Flow / flow-graph artifacts |
| `bpmn`, `maestro` | BPMN-modelled processes (Maestro). Apply both. |
| `case-management` | Case Management product |
| `integration-service` | IS connectors, connections, connector activities |
| `hitl` | Human-in-the-loop / Action Center / Tasks |
| `agents` | Agent runtime, agent definitions |
| `ixp` | Intelligent Xtraction and Processing |
| `document-understanding` | Document Understanding (extraction models, classification, validation, projects) |
| `llm-gateway` | LLM Gateway (model routing, BYO connections, product LLM configurations) |
| `data-fabric` | Data Fabric tables, entities |
| `api-workflow` | API workflow artifacts |
| `orchestrator` | Orchestrator-only failures with no workflow execution involved (e.g., licensing, machine state, asset/queue admin) |

### Investigation output location

The skill writes investigation artifacts to `.local/investigations/` — NOT `.investigations/`. Every `file_exists` criterion path and every post-run script path MUST use `.local/investigations/...`.

### `docsai` mocking

Any rule matching `uip docsai ask ...` in `manifest.json` MUST be `passthrough: true`. Query strings vary between runs and canned responses go stale immediately; the dispatcher caches passthrough responses per query for in-run reuse.

```json
{
  "match": "docsai ask",
  "passthrough": true
}
```

### `success_criteria`

Every scenario MUST include exactly TWO criteria, and ONLY these two:

1. **`skill_triggered`** — verify `uipath-troubleshoot` activated. Without this, the agent can fake an answer by reading fixture files directly and bypassing the skill entirely (we have seen this happen).
2. **`llm_judge`** — grade whether the agent reached the correct conclusion against `RESOLUTION.md`.

**Do NOT add any other criterion type.** Specifically forbidden across the whole troubleshoot suite:

- ❌ `file_exists` — testing whether `.local/investigations/state.json` (or any internal file) was written grades bookkeeping, not the deliverable. `skill_triggered` already verifies the skill ran.
- ❌ `file_contains` — grading the shape of `state.json` / `hypotheses.json` punishes correct skill behavior (multiple playbooks legitimately match; hypotheses legitimately stay `pending` after early-stop).
- ❌ `command_executed` — encodes one investigation path; an agent reaching the right answer via a different (still valid) CLI route gets false-failed.

Concrete failure mode this rule prevents: an agent that reaches the correct root cause via `jobs logs` (skipping `jobs get`) is graded FAILURE solely because a `command_executed` rule required `jobs get d5fed611`. The conclusion was right; the path was different. Brittle.

Anything task-specific the test needs to verify goes in `RESOLUTION.md`. The judge reads it via `include_reference` and compares.

#### Judge configuration — single canonical shape for every task

Every `llm_judge` criterion across all troubleshoot tasks uses the **same** prompt, the same flags, and the same description. Per-task customization lives in `RESOLUTION.md`, never in `task.yaml`.

**Canonical `llm_judge` block** (copy verbatim into every new scenario):

```yaml
- type: llm_judge
  description: "Agent's diagnosis matches RESOLUTION.md"
  weight: 3.0
  pass_threshold: 0.7
  include_reference: true
  include_agent_output: true
  prompt: |
    Grade the agent's final answer against the attached RESOLUTION.md.

    Score on whether the agent identifies the same root cause and
    recommends the same fix as RESOLUTION.md:

      1.0  Same root cause AND same fix (or equivalent).
      0.8  Same root cause; fix is right area but vague.
      0.5  Adjacent cause, missing a key specific.
      0.2  Wrong direction; recognized surface only.
      0.0  Misdiagnosed or blocked.

    Return JSON: {"score": <float>, "rationale": "<one sentence>"}
```

**What the judge sees** (both flags MUST be `true`):

- `include_reference: true` — passes `RESOLUTION.md` (the file named under `reference:` at the task root)
- `include_agent_output: true` — passes the agent's final user-facing response

That is **all** the context the judge gets. The contract: agent's final answer vs. RESOLUTION.md → score. Tool calls are deliberately excluded — the judge grades the presented diagnosis, not how it was reached.

**Forbidden on `llm_judge`:**

- ❌ `files:` array (passing `state.json`, `hypotheses.json`, or any internal artifact). The judge grades presentation, not bookkeeping.
- ❌ Custom prompt language per task — no `DIMENSION A / DIMENSION B`, no `SCORING RUBRIC` clauses citing specific playbook names, no "Evidence sources" enumerations referencing `matched_playbooks` / `is_root_cause` / etc.
- ❌ Per-task hedging notes ("Be substance-focused", "multiple playbooks may match", etc.). The lean rubric already encodes this.

**Why:** the skill's internal state (`state.json`, `hypotheses.json`) is bookkeeping for the next conversation, not a deliverable. Multiple playbooks may legitimately appear in `matched_playbooks`; hypotheses legitimately stay `pending` after early-stop (see SKILL.md "When to stop testing"). Grading on internal-state shape punishes correct skill behavior. What the agent **presents** is the contract.

**Where task-specific guidance lives:** `RESOLUTION.md`. If the judge needs to know that a specific fix must name "AlterIfDisabled = True" or that "Test Heals pool" is wrong — that goes in `RESOLUTION.md` as the authoritative root cause + fix. The judge reads it via `include_reference` and grades against it.

**Lean default for every new scenario:**

```yaml
success_criteria:
  - type: skill_triggered
    description: "Agent invoked the uipath-troubleshoot skill"
    skill_name: "uipath-troubleshoot"
    expected_skill: "uipath-troubleshoot"
    weight: 1.0

  - type: llm_judge
    description: "Agent's diagnosis matches RESOLUTION.md"
    weight: 3.0
    pass_threshold: 0.7
    include_reference: true
    include_agent_output: true
    prompt: |
      Grade the agent's final answer against the attached RESOLUTION.md.

      Score on whether the agent identifies the same root cause and
      recommends the same fix as RESOLUTION.md:

        1.0  Same root cause AND same fix (or equivalent).
        0.8  Same root cause; fix is right area but vague.
        0.5  Adjacent cause, missing a key specific.
        0.2  Wrong direction; recognized surface only.
        0.0  Misdiagnosed or blocked.

      Return JSON: {"score": <float>, "rationale": "<one sentence>"}
```

## Anti-patterns

- **Do not** add `command_executed` criteria. The lean contract is `skill_triggered + llm_judge` only — no `command_executed`, no `file_exists`, no `file_contains`. Asserting a specific CLI command was run encodes one investigation path and false-fails agents that reach the correct conclusion via a different (still valid) route. If a test needs to verify a specific CLI fact, put the fact in `RESOLUTION.md` and let the judge grade it. See the `success_criteria` section above for the full forbidden list.
- **Do not** hand-edit a generated scenario's `manifest.json` to "make tests pass." If the agent calls a command not in the manifest, that's a coverage gap — add a rule with the verbatim recorded response.
- **Do not** include the original `.local/investigations/` outputs in the committed scenario. The fresh run produces its own.
- **Do not** ship real email addresses, real personal Windows paths, or real machine hostnames. The scrub pass is mandatory.
- **Do not** use `git add -A` after generation — the generator drops scratch files in `_tmp/`. Stage explicitly: `git add tests/tasks/uipath-troubleshoot/<scenario>/`.
- **Do not** create a scenario without a verified resolution. The LLM judge needs an authoritative ground truth; a half-baked `RESOLUTION.md` produces flaky scores.

## Scripts

| Script | Purpose |
|--------|---------|
| `_shared/scripts/extract_session.py` | Parse a Claude Code JSONL transcript → `{uip_calls, presenter_output, inferred_scenario_name}`. Pure parser, no file writes. Stdout JSON. |
| `_shared/scripts/generate_scenario.py` | Orchestrate inputs → scenario folder. Two modes: `--dry-run` (default, prints plan) and `--apply` (writes files). Calls `extract_session.py`. Runs the scrub pass. |
| `_shared/scripts/coverage_report.py` | (Existing.) Compare expected vs performed `uip` calls per replicate after a test run. |

## When the user just asks "capture this as a test"

If a user says "save this as a regression test" mid-session and provides no flags, infer:

- `--investigation` → `.local/investigations/` in the cwd
- `--project` → walk up from cwd looking for the nearest `project.json`
- `--transcript` → most-recent JSONL under `~/.claude/projects/<slug>/sessions/`
- `--resolution` → omit, extract from transcript
- `--scenario-name` → infer from the failing job's `ReleaseName` + a short slug

Then run `--dry-run`, show the plan, confirm.

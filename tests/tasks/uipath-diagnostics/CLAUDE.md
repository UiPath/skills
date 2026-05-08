# tests/tasks/uipath-diagnostics — Test Scenario Generator

This directory contains regression tests for the `uipath-diagnostics` skill. Each scenario replays a real diagnostic investigation against a `uip` CLI mock so the agent's reasoning is exercised without hitting a real UiPath tenant.

This file tells you (Claude or a contributor) how to **add a new scenario** from a real session you just resolved.

## When to use this guide

Trigger:

- You ran the `uipath-diagnostics` skill against a real failing job, reached a verified resolution, and want to lock the case in as a regression test.
- A user reports a new failure class not yet covered by an existing scenario.

Skip:

- Tweaking an existing scenario's manifest or fixtures — edit them directly, no generation pass needed.
- Adding tests for *other* skills — use `.claude/commands/generate-tasks.md` instead.

## Inputs

A new scenario needs four sources. Three are mandatory; the fourth is optional.

| Input | Required | Source |
|-------|----------|--------|
| `--investigation <dir>` | yes | The `.investigation/` directory written by the diagnostics skill: `state.json`, `hypotheses.json`, `evidence/`, `raw/`, `depth-check.json`. |
| `--project <dir>` | no | The UiPath project source that was failing. Snapshotted into the new scenario's `process/`. Omit when the diagnosis is purely CLI-driven (no project source available). |
| `--transcript <path>` | yes | A `.jsonl` file or a directory. Directory mode walks `*.jsonl` recursively and treats files under `subagents/` as sub-agent transcripts (their `uip` calls count, their final text is ignored). Source of truth for `uip` calls + presenter output. |
| `--resolution <file>` | no | Pre-written `RESOLUTION.md`. If omitted, the generator extracts the presenter's final assistant message from the transcript. |
| `--scenario-name <name>` | no | Folder name for the new scenario. If omitted, inferred from project name + failing job key. |

## Workflow — ask before writing

The generator runs in two passes. **Always preview before applying.**

### 1. Preview

```bash
python tests/tasks/uipath-diagnostics/_shared/scripts/generate_scenario.py \
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
python tests/tasks/uipath-diagnostics/_shared/scripts/generate_scenario.py \
  ... same flags as preview ... \
  --apply
```

Writes the scenario folder. Prints the path. Exits.

### 4. Verify

After write:

1. Run the smoke test pattern to confirm the mock dispatcher resolves:
   ```bash
   cd tests
   .venv/bin/coder-eval run tasks/uipath-diagnostics/<scenario>/task.yaml -e experiments/default.yaml -v
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
tests/tasks/uipath-diagnostics/<scenario-name>/
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

## Anti-patterns

- **Do not** hand-edit a generated scenario's `manifest.json` to "make tests pass." If the agent calls a command not in the manifest, that's a coverage gap — add a rule with the verbatim recorded response.
- **Do not** include the original `.investigation/` outputs in the committed scenario. The fresh run produces its own.
- **Do not** ship real email addresses, real personal Windows paths, or real machine hostnames. The scrub pass is mandatory.
- **Do not** use `git add -A` after generation — the generator drops scratch files in `_tmp/`. Stage explicitly: `git add tests/tasks/uipath-diagnostics/<scenario>/`.
- **Do not** create a scenario without a verified resolution. The LLM judge needs an authoritative ground truth; a half-baked `RESOLUTION.md` produces flaky scores.

## Scripts

| Script | Purpose |
|--------|---------|
| `_shared/scripts/extract_session.py` | Parse a Claude Code JSONL transcript → `{uip_calls, presenter_output, inferred_scenario_name}`. Pure parser, no file writes. Stdout JSON. |
| `_shared/scripts/generate_scenario.py` | Orchestrate inputs → scenario folder. Two modes: `--dry-run` (default, prints plan) and `--apply` (writes files). Calls `extract_session.py`. Runs the scrub pass. |
| `_shared/scripts/coverage_report.py` | (Existing.) Compare expected vs performed `uip` calls per replicate after a test run. |

## When the user just asks "capture this as a test"

If a user says "save this as a regression test" mid-session and provides no flags, infer:

- `--investigation` → `.investigation/` in the cwd
- `--project` → walk up from cwd looking for the nearest `project.json`
- `--transcript` → most-recent JSONL under `~/.claude/projects/<slug>/sessions/`
- `--resolution` → omit, extract from transcript
- `--scenario-name` → infer from the failing job's `ReleaseName` + a short slug

Then run `--dry-run`, show the plan, confirm.

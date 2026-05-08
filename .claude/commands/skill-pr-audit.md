# Skill PR Audit

Audit a pull request against the eval suite under `tests/tasks/`. Answer two questions:

1. **What evals must run** for the changed files? (folder map → eval commands)
2. **What changed surface has no eval coverage?** (diff vs YAML-declared scope → gap list + stub task YAMLs)

Read-only against `skills/` and `tests/`; the only file writes are stub eval task YAMLs the user explicitly accepts.

**Input:** `$ARGUMENTS`
- Empty → diff `HEAD` against `origin/main`. Default mode.
- A PR number (e.g. `667`) → fetch via `gh pr diff <N>` and `gh pr view <N> --json files`.
- A space-separated list of file paths → audit those paths directly (skip diff fetch).

**Output:** Single markdown report printed to chat, then an optional Phase 6 that dispatches one parallel agent per affected skill (each running its evals in its own tmux window so the user can `tmux attach` and watch live). No PR comment. No file writes unless the user accepts a stub.

---

## Phase 1 — Resolve the changed file set

### 1a. Build the file list

| Invocation | Command |
|---|---|
| Empty | `git diff --name-only origin/main...HEAD` |
| PR number | `gh pr view <N> --json files --jq '.files[].path'` |
| Explicit paths | use args verbatim |

Filter to paths under `skills/` and `tests/tasks/`. Ignore everything else (CI, README, plugin.json, hooks).

If the file list is empty after filtering, print `No skill or test changes — nothing to audit.` and stop.

### 1b. Group by skill

For each path under `skills/<name>/...`, the affected skill is `<name>`. For paths under `tests/tasks/<name>/...`, the affected skill is also `<name>` — but tag the file as a **test change**, not a skill change.

Output an internal map:

```
skill -> { skill_files: [...], test_files: [...] }
```

---

## Phase 2 — Map skill changes to evals (folder map)

For every skill in the map with `skill_files` non-empty:

1. Check if `tests/tasks/<skill>/` exists.
2. If yes → list every `*.yaml` recursively under it, excluding `_shared/`. These are the **candidate evals**.
3. If no → emit a **High-priority gap**: the skill has no eval directory at all.

Emit candidate evals as concrete commands. Use whatever runner the repo uses; check `tests/README.md` and `package.json` once per audit to find it. The current convention is:

```bash
bun run eval <path-to-yaml>
```

If the repo uses a different runner (check `package.json` scripts: `eval`, `test:eval`, `tasks`), use that. Always include `--output json` flags if the runner accepts them. State the runner you picked at the top of the report.

---

## Phase 3 — YAML-parse for fine-grained gap detection

For every changed file under `skills/<name>/`, decide whether any candidate eval **actually exercises** that file's content.

### 3a. Extract the change surface

For each changed skill file, extract:

- **File path** (relative to repo root)
- **Section headings** added or modified (parse markdown `##`/`###` from the diff hunks)
- **Code blocks** added or modified — note the language identifier and any CLI commands inside (lines starting with `uip ` or `gh ` or `bun `)
- **`requestFields` / `parameters` / `node:` keys** added in any reference YAML/JSON

If a file is deleted, skip it for gap detection (it's not new surface).

### 3b. Read each candidate eval YAML

For each `*.yaml` under `tests/tasks/<skill>/`:

- `task_id`
- `tags` (lifecycle, shape, node, feature, connector, resource)
- `initial_prompt` (full text)
- `success_criteria` — flatten every `command_pattern`, `path`, `includes`, `command`

### 3c. Match diff surface against eval surface

A changed file is **covered** by an eval if **any one** holds:

| Match type | Rule |
|---|---|
| **Path mention** | The eval's `initial_prompt` or `success_criteria.command` mentions the file's relative path or basename |
| **CLI overlap** | A CLI command added in the diff appears in the eval's `command_pattern` or `success_criteria.command` |
| **Section/feature overlap** | A new `feature:X` heading or `node:X` plugin matches the eval's `tags` |
| **Plugin folder match** | The diff is under `references/.../plugins/<plugin-name>/` and an eval task carries `node:<plugin-name>` or its `initial_prompt` names that node type |

A changed file is **uncovered** if no eval matches under any of the four rules. Uncovered files become **gap entries**.

### 3d. Rank gaps

| Priority | Condition |
|---|---|
| **High** | Changed file is `SKILL.md`, or a Critical Rules section, or a new plugin's `impl.md`, or any new node type in registry, or the skill has no `tests/tasks/<skill>/` directory |
| **Medium** | New section under an existing `references/` file with no matching eval; new CLI command added with no `command_pattern` match in any eval |
| **Low** | Prose-only edits to existing reference files; typo fixes; link-only changes; comment-only changes in templates |

Skip Low gaps from the gap list — they don't need new evals.

---

## Phase 4 — Suggest stub task YAMLs

For each High and Medium gap, generate a **skeleton** task YAML the user can accept and fill in. Use the existing repo conventions (look at `tests/tasks/<skill>/` for the closest sibling task and copy its shape — `agent` block, `sandbox` block, `success_criteria` skeleton).

Stub naming:

- `task_id`: `skill-<short-skill>-<short-gap-slug>` (e.g. `skill-flow-pagination-loop`)
- File path: `tests/tasks/<skill>/<tier>/<gap-slug>.yaml` where tier defaults to `integration` unless the gap is plainly smoke-level (one CLI invocation, no flow building).

Stub content:

```yaml
task_id: <suggested>
description: >
  TODO — describe what behavior this test verifies. Auto-generated stub for
  uncovered surface: <file:section>.
tags: [<skill>, <tier>, lifecycle:<best-guess>, <other-relevant-tags>]

task_timeout: 1500
agent:
  type: claude-code
  permission_mode: acceptEdits
  allowed_tools: ["Skill", "Bash", "Read", "Write", "Edit", "Glob", "Grep"]
  max_turns: 120
  turn_timeout: 1200

sandbox:
  driver: tempdir
  python: {}
  node:
    env_packages:
      - "@uipath/cli"

initial_prompt: |
  TODO — write the prompt that exercises <gap surface>. Reference the changed
  file: <path>.

success_criteria:
  - type: command_executed
    description: "TODO — assert the CLI invocation the changed surface introduces"
    tool_name: "Bash"
    command_pattern: "<TODO regex>"
    min_count: 1
    weight: 2.0
    pass_threshold: 1.0

max_iterations: 1
```

Print stubs in the report under a `## Suggested new evals` section. **Do NOT write these to disk** unless the user explicitly says "write the stubs" or accepts them.

---

## Phase 5 — Report format

Print one markdown report. No file writes.

```markdown
# Skill PR Audit

**Input:** <PR #N | current branch vs main | explicit paths>
**Runner:** <bun run eval | npm run … | as detected>
**Skills affected:** <count> | **Files changed:** <count> | **Gaps:** <count high>H / <count med>M

## Evals to run

| Skill | Eval task | Why |
|---|---|---|
| uipath-maestro-flow | `tests/tasks/uipath-maestro-flow/connector_features/path_params.yaml` | Touches `references/plugins/connector/impl.md` |
| ... | ... | ... |

Concrete commands:

```bash
bun run eval tests/tasks/uipath-maestro-flow/connector_features/path_params.yaml
bun run eval tests/tasks/uipath-platform/integration-service/...yaml
```

## Coverage gaps

### High
1. **<short title>** — `<changed file>` introduces `<what>`. No eval under `tests/tasks/<skill>/` matches by path, CLI, or tag. *Suggested:* `skill-<...>` (tier, lifecycle, …).

### Medium
1. ...

## Suggested new evals

### `<task_id>` → `tests/tasks/<skill>/<tier>/<slug>.yaml`
```yaml
<full stub>
```

(Repeat per stub.)

## What's already covered

Brief one-line per changed file that DID match an eval, naming the eval. Helps the reviewer trust the gap list.
```

---

## Phase 6 — Optionally dispatch the recommended evals

After printing the report, **ask the user**:

> Run the recommended evals now? Each affected skill gets its own parallel agent + tmux window so you can attach and watch.

Use `AskUserQuestion` with options `Yes — dispatch all`, `Pick specific skills`, `No — done`.

If the user picks **No**, stop. The report is the deliverable.

If the user picks **Yes** or **Pick specific**, dispatch one Agent **per affected skill**, in **parallel** (single message, multiple `Agent` tool uses). Do NOT spawn one agent per YAML — one per skill keeps blast radius bounded and matches the folder-map model.

### 6a. tmux session setup

Once per audit, before dispatch:

```bash
SESSION="skill-pr-audit-$(date +%s)"
tmux new-session -d -s "$SESSION" -n "overview" 'echo "Audit dispatch $(date)"; bash -i'
echo "Attach with: tmux attach -t $SESSION"
```

Print the attach command to the user **immediately** so they can open another terminal and watch while agents run.

### 6b. Per-skill window

For each affected skill, create a tmux window named after the skill **before** spawning its agent. The agent is told to run its commands inside that window so the user sees live output:

```bash
tmux new-window -t "$SESSION" -n "<skill>" "cd $(git rev-parse --show-toplevel) && bash -i"
```

### 6c. Per-skill agent prompt (template)

Spawn one `Agent` call per skill with `subagent_type: general-purpose` and `run_in_background: true`. Each agent's prompt is **self-contained** (it doesn't see the conversation), so include:

- The skill name
- The exact list of YAMLs to run (from Phase 2's "Evals to run" table — only the ones in this skill)
- The `make` / `coder-eval` command to invoke
- The tmux session and window name
- The expected output format

Template:

```
You are running the eval suite for the UiPath skill `<skill>` as part of a PR audit.

Repo root: <absolute path to repo>
tmux session: <SESSION>
tmux window: <skill>

Tasks to run (in this window):
<bulleted list of yaml paths>

Run them via:
  tmux send-keys -t <SESSION>:<skill> 'cd <repo root> && make tags TAGS="<skill> <relevant-tier>"' C-m

Or, for individual tasks:
  tmux send-keys -t <SESSION>:<skill> '.venv/bin/coder-eval run tasks/<skill>/<...>.yaml --output-dir runs/audit-<timestamp>' C-m

Then poll the window output (tmux capture-pane -t <SESSION>:<skill> -p) every ~30s until the run completes
or 30 minutes elapses, whichever comes first. Do not sleep-poll faster than 30s.

Report back, in <300 words:
- Total tasks run, passed, failed
- For each failure: task_id, the failing success_criterion, and a 1-line cause hypothesis
- Whether any failure plausibly traces to the diff in this PR vs being an unrelated flake

Do NOT modify skill or eval files. Read-only.
```

### 6d. Aggregate and report

When all skill agents finish, print a final summary table:

| Skill | Tasks run | Passed | Failed | Likely PR-related? |
|---|---|---|---|---|
| uipath-maestro-flow | … | … | … | … |
| uipath-platform | … | … | … | … |

Then print the tmux attach command again so the user can inspect any window:

```
tmux attach -t <SESSION>          # then Ctrl-b w to switch windows
```

If the user picked **Pick specific skills**, ask which subset via `AskUserQuestion` and dispatch only those.

### 6e. Cleanup

Do NOT kill the tmux session automatically. The user may want to inspect output afterward. Mention in the final summary:

```
When done: tmux kill-session -t <SESSION>
```

---

## Rules

1. **Read-only by default.** Stubs are printed, not written. Only write if the user explicitly accepts.
2. **Be conservative on coverage claims.** "Covered" requires one of the four match rules in 3c. When in doubt, list as a Medium gap and let the reviewer decide.
3. **Skip prose-only diffs.** Typo fixes, link standardization, and comment edits to existing reference files do not need new evals. Surface them in the report's "What's already covered" section instead.
4. **Use the existing tag taxonomy.** Stub `tags` must use values from `tests/README.md` (lifecycle, shape, node, feature, connector, resource). Do not invent new dimensions.
5. **Do NOT modify skill or eval files.** This command audits; it does not refactor or fix.
6. **Match recommendation tags to the closest sibling eval.** Read the nearest existing task YAML under the same `tests/tasks/<skill>/` directory and reuse its `agent`/`sandbox` blocks verbatim in stubs — don't invent new shapes.
7. **Stop early if there are no skill or test changes.** A diff that touches only CI, docs outside `skills/`, or `plugin.json` produces a one-line "nothing to audit" report.
8. **Run independent steps in parallel.** Phase 1 file-list, Phase 2 candidate-eval listing, and Phase 3a diff-surface extraction are independent — fan them out as parallel `Bash` / `Read` calls when the diff spans multiple skills.
9. **One agent per skill, not per YAML.** Phase 6 dispatches at most one Agent per affected skill. Spawning one agent per individual eval YAML is forbidden — it doesn't add signal and explodes cost.
10. **Always confirm before dispatch.** Phase 6 must ask via `AskUserQuestion` after the report prints. Never auto-run evals.
11. **Never kill the tmux session.** The user attaches after the run to inspect failures. Print the `tmux kill-session` command in the summary instead.
12. **Background, don't block.** Phase 6 agents run with `run_in_background: true`. The dispatching turn prints the attach command and the summary table when agents return; it does not block on a foreground agent.

# Test Writing Rules

Tests live in `tests/tasks/<skill-name>/` as coder_eval task YAMLs. Authoritative reference: [tests/README.md](../../tests/README.md) — read it before authoring or editing a task.

## Workflow

1. **`/test-coverage <skill-name>`** — identify coverage gaps before writing anything. Report lands in `tests/reports/<skill-name>.md` with priority-ranked gaps.
2. **`/generate-task <description>`** — scaffold a task YAML for the chosen gap. Do not pass a skill name; the command infers it. Output is an unverified scaffold.
3. **`/lint-task <path>`** — lint the generated YAML before committing.
4. **`/audit-verbs` (conditional)** — run only when `/lint-task` surfaces **CLI verb reachability** findings. Produces `tests/reports/cli-verb-audit.md` and `tests/reports/skill-verb-audit.md` so you can tell whether a stale verb shows up elsewhere. Skip when `/lint-task` is clean.
5. Run the task with `coder-eval` and add a passing-run claim to the PR (lint flags missing claims as High).

## Must-Do

1. **Required tags on every task:** `skill` (`uipath-<name>`) + `tier` (`smoke`|`integration`|`e2e`) + `mode:*` (`build`|`operate`|`diagnose`).
2. **One task YAML per leaf directory.** Tier is a tag, not a folder.
3. **Inherit `agent:` from the experiment.** Override only fields that differ (e.g. `max_turns`).
4. **New skill PRs:** ≥1 smoke + ≥1 e2e task.
5. **Use only the closed tag vocabularies** in tests/README.md §Tag Taxonomy. Propose new values in the PR — never invent inline.
6. **Base new tasks on `tests/templates/test-task-template.yaml`.**

## Sandbox Configuration

### Never install `@uipath/cli` via `env_packages`

The GH smoke runner (`smoke-skills.yml`) installs `@uipath/cli@latest` globally before any task runs. Do **not** list it under `sandbox.node.env_packages`.

**Forbidden:**
```yaml
sandbox:
  node:
    env_packages:
      - "@uipath/cli"          # redundant
      - "@uipath/cli@0.1.21"   # pinned — version skew
      - "@uipath/cli@latest"   # redundant
```

**Correct:**
```yaml
sandbox:
  node: {}
```

Or omit `node:` entirely if no other Node packages are needed.

**Why:** Re-installing the CLI installs a second copy into `node_modules`, potentially shadowing the global binary. A pinned version freezes the CLI at a specific release and silently diverges from the runner's `@latest` install, causing version skew between local runs and CI.

The template at `tests/templates/test-task-template.yaml` does not include `env_packages` — do not add it unless installing a package other than `@uipath/cli`.

## Success Criteria — Grade Behavior, Not Self-Reports

Use side effects (`command_executed`, `file_exists`, `file_contains`, `json_check`, `run_command`, `skill_triggered`, `command_not_executed`). Never grade on agent monologue.

Weight: `1.0` supporting · `1.5` core command/artifact · `2.0` artifact content · `3.0` primary validation · `5.0–6.0` e2e execution. `pass_threshold: 1.0` unless the criterion has multiple sub-assertions.

When criteria parse CLI output, steer the prompt toward `--output json`, but grade the **outcome** (the parsed value, via `run_command` / `file_check`), NOT the literal flag. Never add a gating `command_executed` check on `(uip|\$UIP)\s+.*--output\s+json`: the flag is outcome-invisible (often the CLI default), so gating on it docks agents that reach the same result without typing it. To record convention adherence, use an advisory check (`pass_threshold: 0`).

Never gate on `command_executed` with `min_count: 2+` to mean "did this N times". `min_count` counts matching **tool calls**, not command occurrences — the regex yields at most one match per call, so an agent that batches N invocations into one `bash -lc "cmd1; cmd2; …"` scores 1/N and fails despite correct behavior. Gate `min_count: 1` (the command was used), prove the N operations with behavioral criteria (one `file_exists`/`json_check`/`run_command` per expected outcome), and make any `min_count: N` shape check advisory (`weight: 0`, `pass_threshold: 0`). See tests/README.md §`command_executed`.

## Prompts

Minimal. State the goal and the success bar ("not complete until `uip ... validate` passes"). Do not enumerate CLI flags — the skill teaches those.

## Anti-patterns

- Pinning `@uipath/cli` in `sandbox.node.env_packages` (see Sandbox Configuration above)
- Gating a `command_executed` criterion on `min_count: 2+` (counts tool calls, not occurrences — batching agents fail; see Success Criteria above)
- Grading a multi-step task *only* on `command_executed` counters with no behavioral criterion proving the outcome
- Copying the full `agent:` block instead of inheriting
- Tagging `connector:slack` / `resource:rpa` — `connector` and `resource` are flat boolean markers; the specific value is in the path/`task_id`/body
- Inventing `feature:` leaf names that duplicate the file path
- Hand-holding prompts that list every CLI flag

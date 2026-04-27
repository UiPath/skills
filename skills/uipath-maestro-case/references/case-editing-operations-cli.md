# Case Editing Operations — CLI Strategy

All mutations to `caseplan.json` performed via `uip maestro case` CLI commands. This is the default strategy for any plugin not yet migrated to direct JSON (see [case-editing-operations.md](case-editing-operations.md) for the matrix).

> **When to use this strategy:** For plugins marked `Strategy = CLI` in the matrix. The plugin's own `impl-cli.md` is authoritative for the required flags.

---

## Prerequisites

1. **`uip` binary on PATH.** If not resolvable:
   ```bash
   UIP=$(command -v uip 2>/dev/null || echo "$(npm root -g 2>/dev/null | sed 's|/node_modules$||')/bin/uip")
   $UIP --version
   ```
2. **Logged in.** `uip login status --output json` — if not logged in, ask the user to `uip login` and stop.
3. **Registry pulled.** `uip maestro case registry pull` once per session — caches registry resources locally at `~/.uipcli/case-resources/`.

---

## Execution Principles

1. **Sequential only.** CLI mutations depend on IDs returned by previous calls. Never parallelize.
2. **Always `--output json`** when output is parsed programmatically.
3. **Capture generated IDs.** Every `*add*` command returns a `StageId` / `TaskId` / `EdgeId` under `Data`. Keep a capture map — it's referenced by downstream edges, tasks, conditions, SLA, and bindings.
4. **Validate at plugin boundaries, not per-command.** Intermediate states are expected to be invalid. Run `uip maestro case validate <file>` after each plugin's batch.
5. **Retry policy.** Up to 3 validation retries per session. After the 3rd failure, AskUserQuestion: `Retry with fix`, `Pause for manual edit`, `Abort`.

---

## Standard Execution Flow

The flow documented in [implementation.md](implementation.md) applies. CLI commands per node type live in each plugin's `impl-cli.md`.

In summary, the order is:

1. **Create the project structure** (Step 6) — scaffolding commands (solution new → case init → project add → cases add).
2. **Declare global variables and arguments** (Step 6.1) — plugin: `variables/global-vars`.
3. **Add stages** (Step 7) — plugin: `stages`.
4. **Add edges** (Step 8) — plugin: `edges`.
5. **Add tasks + bind inputs/outputs** (Step 9) — per-task-type plugins; skeleton tasks for unresolved resources.
6. **Add conditions** (Step 10) — per-scope plugins.
7. **Configure SLA and escalation** (Step 11) — plugin: `sla`.
8. **Validate** (Step 12) — `uip maestro case validate <file>`.
9. **Post-build prompt** (Step 13) — AskUserQuestion for debug / upload / done.

Per-command detail lives in each plugin's `impl-cli.md`. This file is a cross-cutting reference for when/why/how the CLI is invoked; the plugin docs are the source of truth for each specific command.

---

## Output Format Reference

All `uip maestro case` commands return one of:

```json
{ "Result": "Success", "Code": "...", "Data": { ... } }
{ "Result": "Failure", "Message": "...", "Instructions": "..." }
```

Agents parse `Result` first; on `Success`, the relevant IDs are under `Data`. On `Failure`, `Message` is the root cause; `Instructions` is the suggested fix.

---

## When to Switch to JSON Strategy

If a plugin's row in [case-editing-operations.md](case-editing-operations.md) reads `Strategy = JSON`, do NOT use CLI commands for that plugin's operations — use the plugin's `impl-json.md` + [case-editing-operations-json.md](case-editing-operations-json.md).

Mixing strategies within a single skill run is expected during the migration — CLI for non-migrated plugins, JSON for migrated ones. They coexist on the same `caseplan.json` safely because direct JSON writes conform to the same spec the CLI produces.

---

## Anti-Patterns

- **Do NOT execute CLI commands in parallel.** Each may depend on IDs from the previous one.
- **Do NOT validate after every individual command.** Intermediate states are expected to be invalid.
- **Do NOT pass `--type trigger` to `stages add` manually.** The trigger node is auto-created by `cases add`.
- **Do NOT skip `--output json`** on any command whose output is parsed.
- **Do NOT use CLI commands for a plugin that has migrated to JSON.** The strategy matrix is authoritative.

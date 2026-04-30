---
name: uipath-maestro-case
description: "UiPath Case Management authoring (caseplan.json) from sdd.md. Produces tasks.md plan, writes caseplan.json via per-plugin JSON recipes. For .xaml→uipath-rpa, .flow→uipath-maestro-flow."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Case Management Authoring Assistant

> **Preview** — skill is under active development; surface and behavior may change.

Builds UiPath Case Management definitions from `sdd.md`. Generates `tasks.md` plan, then writes `caseplan.json` directly via per-plugin JSON recipes. CLI is reserved for read-only metadata fetches (registry, validate, debug, tasks describe, is describe) and solution boundary operations (`uip solution new` / `project add` / `upload`).

**Scope:** new case from `sdd.md` only. Modifying existing case not supported (no remote fetch tooling).

## When to Use This Skill

- User provides `sdd.md` and wants Case Management project built
- User asks to create new case management project or definition
- User asks to generate implementation tasks from `sdd.md` or convert spec to plan
- User asks about case management JSON schema — nodes, edges, tasks, rules, SLA
- User wants to manage runtime case instances (list, pause, resume, cancel) — see [references/case-commands.md](references/case-commands.md)

**Do not use for:** `.xaml` → `uipath-rpa`. `.flow` → `uipath-maestro-flow`. Standalone agents/APIs/processes outside case context → corresponding UiPath skill.

## Critical Rules

1. **sdd.md is sole input.** Trust as written. Skill does not validate or gap-fill. If ambiguous, use AskUserQuestion — never infer silently.
2. **Run `uip maestro case registry pull` before planning.** Discovery reads cache files at `~/.uipcli/case-resources/<type>-index.json` directly. `registry search` has known gaps (esp. action-apps). See [references/registry-discovery.md](references/registry-discovery.md).
3. **`--output json` on every parsed read.**
4. **Follow plugin per node type.** Open matching `planning.md` during planning + `impl-json.md` during execution. Never guess JSON shapes from memory.
5. **`tasks.md` declarative only.** No shell commands inside. Field names use plain identifiers (e.g., `type:`, `displayName:`, `lane:`), not CLI flag syntax. One T-entry per sdd.md declaration — every stage, edge, task, trigger, condition, SLA rule gets own T-number, even when value looks like default (`current-stage-entered`, `case-entered`, `exit-only`, `is-interrupting: false`, `runOnlyOnce: true`, `marks-stage-complete: true`). Never group, never silently omit. Always regenerate from scratch. See [`references/planning.md` §4.0](references/planning.md).
6. **HARD STOP after `tasks.md`.** AskUserQuestion: `Approve and proceed` / `Request changes`. Re-read `tasks.md` before executing.
7. **Unresolved resource → skeleton task. Never fabricate IDs.** Keep `<UNRESOLVED: ...>` on `taskTypeId` / `typeId` / `connectionId`. Omit `inputs:` / `outputs:`. Execute by writing the task JSON node with `type` + `displayName` + structural fields, `data: {}`, no `taskTypeId` / `connectionId` keys. Conditions still reference skeleton's TaskId. See [references/skeleton-tasks.md](references/skeleton-tasks.md).
8. **Persist every registry resolution to `registry-resolved.json`** — search query, all matches, selected result, rationale.
9. **Cross-task refs:** `"Stage Name"."Task Name".output_name` in planning, resolve to `=vars.<outputVarId>` at execution by reading source's `var` field. Discover output names via `uip maestro case tasks describe` — never fabricate. See [references/bindings-and-expressions.md](references/bindings-and-expressions.md) and [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md).
10. **HARD STOP between Phase 2a and Phase 2b — unconditional, every run.** Run informational `validate` (no `--mode`), surface counts, present AskUserQuestion: `Publish for review` / `Skip publish and continue` / `Abort`. Do NOT halt on Phase 2a validate errors — unbound inputs/missing conditions/missing SLA expected. Never skip prompt for auto mode, non-interactive mode, prior approval. If harness forbids prompts, halt with error. **On `Publish for review`: print `DesignerUrl` as plain-text output BEFORE invoking the second AskUserQuestion — never embed URL only inside the question body.** Full contract in [`references/phased-execution.md`](references/phased-execution.md).
11. **Never run `uip maestro case debug` automatically.** Executes case for real — emails, messages, API calls. Explicit user consent only.
12. **`caseplan.json` mutations: Read + Write/Edit only.** No `python`, `node`, `jq`, `sed`, `awk`, or scripts that open/parse/modify/save the file. Bash subprocesses OK for stdout-only helpers (e.g., id generation), CLI metadata fetches, validate, debug, and solution scaffold/upload. See [references/case-editing-operations.md § Tool usage](references/case-editing-operations.md#tool-usage--mandatory).
13. **Always run `uip solution resource refresh` before `uip solution upload` or `uip maestro case debug`** — syncs resources from `bindings_v2.json` so Studio Web can resolve connector dependencies.

## Workflow

Three hard stops: **Planning** (sdd.md → tasks.md) → approve → **Phase 2a** (skeleton) → publish-for-review stop → **Phase 2b** (detail) → post-build.

### Phase 1 — Planning

Read [references/planning.md](references/planning.md). Produces:

- `tasks/tasks.md` — T-numbered entries (stages → edges → tasks → conditions → SLA)
- `tasks/registry-resolved.json` — audit trail

HARD STOP: AskUserQuestion approval. Loop on `Request changes`.

### Phase 2a — Skeleton build

Read [references/implementation.md](references/implementation.md) + [references/phased-execution.md](references/phased-execution.md). Builds structural shape only:

1. Solution + project + root case (Step 6)
2. Global variables + arguments (Step 6.1)
3. Stages (Step 7), edges (Step 8), triggers
4. Tasks — shape only (Step 9): non-connector with full `data.inputs[]` schema + empty values; connector with `typeId` + `connectionId` only (no `is describe`); unresolved as skeletons per Rule 7
5. Informational validate (Step 9.5.1) — do NOT halt on errors/warnings
6. **HARD STOP** (Step 9.5.2–9.5.5): `Publish for review` / `Skip publish and continue` / `Abort`. On `Publish`: `uip solution resource refresh <SolutionDir> --output json` then `uip solution upload`, print DesignerUrl, AskUserQuestion: `Continue to phase 2b` / `Abort`. On `Abort`: dump `build-issues.md`, exit (no cleanup).

### Phase 2b — Detail build

Re-read `tasks.md` AND `caseplan.json` (Step 9.6). Then:

1. Connector schema + defaults (Step 9.7) — `is resources/triggers describe`
2. I/O binding all task classes (Step 9.8) — per [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md)
3. Conditions all 4 scopes (Step 10)
4. SLA + escalation (Step 11)
5. Full validate (Step 12). Retry up to 3×; on 3rd failure AskUserQuestion: `Retry with fix` / `Pause for manual edit` / `Abort`
6. Dump `build-issues.md` (Step 12.1)
7. Post-build loop (Step 13) — AskUserQuestion until `Done`

## Reference Navigation

| I need to... | Read |
|---|---|
| Plan tasks from sdd.md | [references/planning.md](references/planning.md) |
| Execute tasks.md into a case | [references/implementation.md](references/implementation.md) |
| Phase 2a/2b split + hard stop contract | [references/phased-execution.md](references/phased-execution.md) |
| Edit caseplan.json directly | [references/case-editing-operations.md](references/case-editing-operations.md) |
| Case JSON schema | [references/case-schema.md](references/case-schema.md) |
| Surviving CLI commands (registry, validate, debug, runtime) | [references/case-commands.md](references/case-commands.md) |
| Troubleshoot a failed case | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Resolve task types from registry | [references/registry-discovery.md](references/registry-discovery.md) |
| Wire inputs/outputs + cross-task refs + expression prefixes | [references/bindings-and-expressions.md](references/bindings-and-expressions.md) |
| Configure connector activity / trigger / event | [references/connector-integration.md](references/connector-integration.md) |
| Skeleton tasks for unresolved resources | [references/skeleton-tasks.md](references/skeleton-tasks.md) |
| Sync bindings_v2.json + connection resources | [references/bindings-v2-sync.md](references/bindings-v2-sync.md) |

### Plugin Index

**Structural:**

| Plugin | Scope |
|--------|-------|
| [case](references/plugins/case/planning.md) | Root case (T01) |
| [stages](references/plugins/stages/planning.md) | Regular and exception stages |
| [edges](references/plugins/edges/planning.md) | Edges between Trigger/Stage nodes |
| [sla](references/plugins/sla/planning.md) | Default SLA, conditional rules, escalation |
| [global-vars](references/plugins/variables/global-vars/planning.md) | Case variables and arguments |
| [io-binding](references/plugins/variables/io-binding/planning.md) | Task I/O wiring, cross-task refs |
| [logging](references/plugins/logging/impl-json.md) | Shared issue log |

**Tasks** (`references/plugins/tasks/`):

| Plugin | sdd.md component type |
|--------|-----------------------|
| [process](references/plugins/tasks/process/planning.md) | PROCESS, AGENTIC_PROCESS |
| [agent](references/plugins/tasks/agent/planning.md) | AGENT |
| [rpa](references/plugins/tasks/rpa/planning.md) | RPA |
| [action](references/plugins/tasks/action/planning.md) | HITL |
| [api-workflow](references/plugins/tasks/api-workflow/planning.md) | API_WORKFLOW |
| [case-management](references/plugins/tasks/case-management/planning.md) | CASE_MANAGEMENT |
| [connector-activity](references/plugins/tasks/connector-activity/planning.md) | CONNECTOR_ACTIVITY |
| [connector-trigger](references/plugins/tasks/connector-trigger/planning.md) | CONNECTOR_TRIGGER |
| [wait-for-timer](references/plugins/tasks/wait-for-timer/planning.md) | TIMER (in-stage) |

**Triggers** (`references/plugins/triggers/`):

| Plugin | When |
|--------|------|
| [manual](references/plugins/triggers/manual/planning.md) | User-initiated start |
| [timer](references/plugins/triggers/timer/planning.md) | Scheduled start |
| [event](references/plugins/triggers/event/planning.md) | External connector event |

**Conditions** (`references/plugins/conditions/`):

| Plugin | Scope |
|--------|-------|
| [stage-entry-conditions](references/plugins/conditions/stage-entry-conditions/planning.md) | Stage entered |
| [stage-exit-conditions](references/plugins/conditions/stage-exit-conditions/planning.md) | Stage exits |
| [task-entry-conditions](references/plugins/conditions/task-entry-conditions/planning.md) | Task starts |
| [case-exit-conditions](references/plugins/conditions/case-exit-conditions/planning.md) | Case completes/exits |

## Anti-patterns

- **Do NOT leave stages without an inbound edge.** Orphaned and unreachable. Every stage needs ≥1 inbound edge from Trigger or another stage.
- **Do NOT validate after each T-entry.** Intermediate states expected invalid. Run `validate` once at end of Phase 2a (informational) and once at end of Phase 2b (authoritative).
- **Do NOT batch multiple T-entries into one JSON write.** Each T-entry: own Read → mutate → Write cycle. Composing large in-memory JSON across stages/edges/tasks hides intermediate state, breaks review.
- **Do NOT place multiple tasks in same lane.** FE renders same-lane tasks stacked — unreadable. Each task own `lane` index in `stageNode.data.tasks[laneIndex][]`. Lane is layout only, no execution semantics.
- **Do NOT edit `content/*.bpmn`.** Auto-generated, will be overwritten. Edit `content/*.json` only.
- **Do NOT fabricate expression syntax for conditional SLA rules.** Describe condition in natural language; execution phase determines exact form.
- **Do NOT invoke other skills automatically.** If case needs process/agent/action that doesn't exist, emit skeleton task (Rule 7) and list missing resources in completion report. On-demand resource creation is future milestone.

> **Trouble?** Use `/uipath-feedback` to send report.

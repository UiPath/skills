# Phased Execution: Phase 2a → Hard Stop → Phase 2b

Authoritative reference for the two-phase implementation flow. Read before executing any T-entry from an approved `tasks.md`.

> **Relationship to other docs.** This document defines the phase boundary. Per-plugin execution detail still lives in `plugins/<name>/impl-json.md` (or `impl-cli.md` per the strategy matrix in [case-editing-operations.md](case-editing-operations.md)). Per-step ordering and file-system mutations live in [implementation.md](implementation.md).

## Why two phases

After `tasks.md` is approved, the skill does **not** build the full case in one pass. It first builds a **skeleton** — enough structure for the user to review the case graph visually in Studio Web — then hard-stops for approval before wiring the detail (I/O values, conditions, SLA).

This gives the user a review checkpoint on the shape of the case before the agent commits to detail work that is costly to redo.

## Phase boundaries

| Phase | What gets built | Output |
|---|---|---|
| **2a — Skeleton build** | Solution + project, root case, global variables, stages, edges, triggers (full), tasks (name + type, no value binding), skeleton tasks for unresolved | `caseplan.json` emitted; validate run for info only (expected to report unbound inputs / missing conditions / missing SLA) |
| **Hard stop** | User reviews via Studio Web (optional), then approves / aborts | User choice captured via AskUserQuestion |
| **2b — Detail build** | Connector task schemas, task I/O value binding, conditions (all 4 scopes), SLA + escalation | `caseplan.json` passes full validation |

## Phase 2a — What gets written

### Structural nodes (full detail)

- Solution + project scaffolding (`uip solution new`, `uip solution project add`, plus the JSON scaffolding from `plugins/case/impl-json.md`).
- Root case — `caseplan.json` with `root` block populated (name, caseIdentifier, empty `nodes[]`, empty `edges[]`, empty `caseExitConditions[]`).
- Global variables and arguments — `root.data.uipath.variables` (`inputs`, `outputs`, `inputOutputs`) fully declared.
- Stages — all StageIds generated and captured.
- Edges — all edges written; sources and targets resolve.
- Triggers — fully built. Trigger output mappings written (they reference global variables, which already exist).

### Tasks (shape depends on resolution state + task class)

| Task class | Resolved resources | Phase 2a shape |
|---|---|---|
| Non-connector (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `wait-for-timer`) | `task-type-id` resolved | Full `data.inputs[]` schema written (from `uip maestro case tasks describe`). Each input's `value` field is empty (`""`). Outputs populated per plugin. |
| Connector (`connector-activity`, `connector-trigger`) | `type-id` + `connection-id` resolved | `data` contains `type-id` and `connection-id` only. `data.inputs` omitted or empty. **No `is resources describe` / `is triggers describe` call in 2a** — schema discovery is deferred to 2b. |
| Any task | Unresolved (`<UNRESOLVED: …>` in `tasks.md`) | Skeleton task per Rule 7 of `SKILL.md` — empty `data: {}` (plus `data.taskTitle` / `data.priority` / `data.recipient` for `action`). Marker preserved. See [skeleton-tasks.md](skeleton-tasks.md). |

### What does NOT get written in Phase 2a

- Task input `value` bindings (literals, expressions, cross-task references).
- Connector task input/output schemas.
- Conditions of any scope (stage-entry, stage-exit, task-entry, case-exit).
- SLA rules (default, conditional) and escalation rules.

## Phase 2a informational validate

At the end of Phase 2a, run regular validate:

```bash
uip maestro case validate "<caseplan.json path>" --output json
```

**This call is informational only — do NOT halt on errors or warnings.** Phase 2a state is expected to be invalid: unbound required input values, missing condition rules, missing terminal exit, missing secondary-stage exit conditions, missing SLA. All of those are resolved in Phase 2b.

Capture the error and warning counts (and optionally the first few messages) and include them in the hard-stop summary. The user decides whether the skeleton is worth publishing/continuing, or whether something looks off and they want to `Abort` for inspection.

**Do not parse the validate output for "expected" vs "unexpected" errors.** The skill does not try to classify validation errors at this boundary — if the user sees something that looks like a true structural bug (dangling edge, missing trigger, duplicate names), they choose `Abort` and fix it before re-running. Simpler, no false negatives from misclassification.

## Hard stop

**Unconditional.** Present a summary, then prompt the user via AskUserQuestion. The prompt is MANDATORY on every run — auto mode, non-interactive mode, and prior blanket approval do NOT bypass it. The only valid transition from Phase 2a to Phase 2b is a user response to this AskUserQuestion. If the harness refuses interactive prompts, halt with an explicit error rather than proceeding silently.

### Summary content

Print before the prompt:

1. Counts: stages / primary stages / exception stages / edges / triggers / tasks total / skeleton tasks / unresolved resources.
2. Validate result (informational): `<N> errors, <M> warnings` — call out that Phase 2a state is expected invalid (unbound inputs / missing conditions / missing SLA are all filled in Phase 2b). Surfacing the counts is enough; do not dump the full error list unless the user asks.
3. Paths: `caseplan.json`, `tasks.md`, `registry-resolved.json`.

Do not enumerate every task. Studio Web visualization fills that role after publish.

### Prompt

Use **AskUserQuestion** with three options:

- `Publish for review` — upload skeleton to Studio Web for visual review.
- `Skip publish and continue` — proceed directly to Phase 2b.
- `Abort` — stop the skill; leave artifacts in place.

### On `Publish for review`

1. Run `uip solution upload "<SolutionDir>" --output json`.
2. Print `DesignerUrl` from the response.
3. **AskUserQuestion** (second prompt): `Continue to phase 2b` / `Abort`.

Do not warn the user about Studio Web edits being overwritten. Phase 2b's final Step 13 prompt re-publishes the completed case, which overwrites any volatile review-time edits with the final local state. The user can compare Studio Web state before and after Phase 2b to spot any edits they want to preserve.

### On `Skip publish and continue`

Proceed directly to Phase 2b.

### On `Abort`

1. Dump in-memory issue list to `tasks/build-issues.md` per [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md).
2. Print paths of `caseplan.json`, `tasks.md`, `registry-resolved.json`, and the solution directory.
3. Exit the skill.

Do **not** delete any artifacts. The user may want to inspect them, or re-run the skill later (which regenerates `tasks.md` from scratch per Rule 5).

## Phase 2b re-entry protocol

Phase 2b begins after the user selects `Continue to phase 2b` (or `Skip publish and continue`). Before executing any 2b step:

1. **Re-read `tasks.md`** — per Rule 6. The declarative plan is the handoff.
2. **Re-read `caseplan.json`** — the authoritative source of all IDs generated in Phase 2a:
   - Stage name → StageId (from `schema.nodes[]` where `type === "case-management:Stage"` or `"case-management:ExceptionStage"`, keyed on `data.label`).
   - Trigger ID (from `schema.nodes[]` where `type === "case-management:Trigger"`).
   - Task name → TaskId per stage (from `schema.nodes[<stage>].data.tasks[][]`).
   - Variable name → `var` ID (from `root.data.uipath.variables.{inputs,outputs,inputOutputs}`).
3. Optionally cross-check against `id-map.json` if the JSON-strategy plugins wrote one. `caseplan.json` is the source of truth; `id-map.json` is a speed-up.

Never trust in-memory maps from Phase 2a without re-reading `caseplan.json` — context may be compacted across the hard stop.

## Phase 2b — Execution order

After re-entry:

1. **Connector task detail** — for each connector task in `tasks.md`, run the plugin's `impl-json.md` detail steps: `is resources describe` (or `is triggers describe`), write `data.inputs[]` / `data.outputs[]` schema + resolved values.
2. **Task I/O value binding (all task classes)** — per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md). Applies to both non-connector and connector tasks. For each task's inputs in `tasks.md` order, write the literal, expression, or cross-task reference (resolved to `=vars.<var>`) into `task.data.inputs[i].value`. Connector tasks have their `data.inputs[]` schema written in step 1 above; value binding happens here in step 2, the same as non-connector tasks.
3. **Conditions** — per-scope plugin `impl-json.md`:
   - Stage entry conditions
   - Stage exit conditions
   - Task entry conditions (depends on TaskIds from Phase 2a)
   - Case exit conditions
4. **SLA + escalation** — per [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md). Group `tasks.md §4.8` by target (root or stage); write full `slaRules[]` in one mutation per target.
5. **Full validate** — `uip maestro case validate "<file>" --output json` (no `--mode` flag; defaults to full). Retry policy per `SKILL.md` Anti-patterns ("Do NOT validate after each command"): validate once after full Phase 2b build; up to 3 retries.
6. **Dump `build-issues.md`** per [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md).
7. **Post-build prompt** — existing Step 13 from [implementation.md](implementation.md): `Run debug session` / `Publish to Studio Web` / `Done` / `Something else`.

## Skeleton tasks — unchanged semantics

Skeleton tasks (empty `data: {}` for unresolved resources) behave the same in both phases. Phase 2a creates them; Phase 2b does **not** upgrade them to typed tasks — upgrading requires the user to register the missing resource externally. See [skeleton-tasks.md](skeleton-tasks.md).

Phase 2b still wires skeleton TaskIds into:
- Task-entry conditions that reference the skeleton.
- Stage-exit `selected-tasks-completed` rules that include the skeleton.

It does **not** write `data.inputs` / `data.outputs` for skeletons. Input binding is deferred to the user's post-build upgrade pass.

## Abort semantics

Abort can occur at either hard-stop prompt:

- `Abort` at the first prompt (`Publish for review` / `Skip` / `Abort`).
- `Abort` at the second prompt (`Continue to phase 2b` / `Abort`) after publishing.

Both follow the same cleanup:

1. Dump `build-issues.md`.
2. Print paths.
3. Exit.

No artifact deletion. No rollback. The user owns the partial state.

## Out of scope

- **Re-ingesting Studio Web edits.** If the user edits the published skeleton in Studio Web during review, those edits are not round-tripped back into local `caseplan.json`. Phase 2b writes on top of local state; the final Step 13 re-publish overwrites Studio Web with the completed local build.
- **Resuming an aborted session.** Re-running the skill regenerates `tasks.md` from scratch (Rule 5) and re-executes both phases from Phase 2a Step 1.
- **A dedicated skeleton validation mode.** The skill does not depend on a `--mode skeleton` CLI flag. Regular `uip maestro case validate` runs at end of Phase 2a for informational output only; expected Phase 2a errors are not filtered or classified here.

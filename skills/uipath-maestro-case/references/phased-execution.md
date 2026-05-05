# Phased Execution: Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6

Authoritative reference for the post-planning execution flow. Read before executing any T-entry from an approved `tasks.md`.

> **Relationship to other docs.** This document defines phase boundaries and hard-stop contracts. Per-plugin execution detail lives in `plugins/<name>/impl-json.md`. Per-step ordering and file-system mutations live in [implementation.md](implementation.md).

## v20 mode (Rule 17 softening)

When `Schema: v20` is set in `tasks.md`, the following phase modifications apply. v19 mode is unchanged.

| Phase | v19 behavior | v20 behavior |
|---|---|---|
| 2 — Prototyping | Informational validate, no halt on errors | Identical (already informational) |
| 4 — Validate | Authoritative validate, 3-retry cap, hard stop on 3rd failure | **Informational only** — capture errors to `build-issues.md`, no retry loop, no hard stop. Reason: CLI may not yet accept v20 top-level shape. |
| 5 — Debug | `Run debug session` runs `uip maestro case debug` | Same prompt + behavior, BUT print plain-text warning BEFORE AskUserQuestion: `> v20 mode: uip maestro case debug may reject. Failure does not invalidate caseplan.json.` On failure, note `caveat: CLI may reject v20 schema — failure may be schema-related not case-bug-related` in build-issues.md. |
| 6 — Publish | `Publish to Studio Web` runs `uip solution upload` | Same prompt + behavior, BUT print plain-text warning BEFORE AskUserQuestion: `> v20 mode: uip solution upload may reject top-level shape until CLI catches up. Failure non-fatal — caseplan.json still valid v20.` On failure, dump response to `tasks/upload-response.json`, re-show Phase 6 prompt. |

Skill stays emit-honest in v20 mode: JSON-shape correctness is the skill's job, downstream CLI accept-correctness is outside scope (Rule 17).

## Why phased

After `tasks.md` is approved, skill does **not** build full case in one pass. It builds **skeleton** first (Phase 2 Prototyping) — enough structure for user to review case graph visually in Studio Web — then hard-stops for approval before wiring detail (Phase 3 Implementation). Validate (Phase 4), Debug (Phase 5), and Publish (Phase 6) each follow as separate gated phases. Debug runs before Publish so the user only publishes a build they've verified end-to-end.

Each hard stop gives user review checkpoint before agent commits to costly downstream work.

## Phase summary

| Phase | What gets built | Output | Hard stop on exit |
|---|---|---|---|
| **2 — Prototyping** | Solution + project, root case, global variables, stages, edges, triggers (full), tasks (name + type, no value binding), skeleton tasks for unresolved | `caseplan.json` emitted; informational validate run (expected to report unbound inputs / missing conditions / missing SLA) | `Publish for review` / `Skip publish and continue` / `Abort` |
| **3 — Implementation** | Connector task schemas, task I/O value binding, conditions (all 4 scopes), SLA + escalation | `caseplan.json` ready for authoritative validation | None — proceeds to Phase 4 |
| **4 — Validate** | Run authoritative `uip maestro case validate`, dump `build-issues.md` | `caseplan.json` passes full validation | On 3rd validate failure: `Retry with fix` / `Pause for manual edit` / `Abort` |
| **5 — Debug** | Optional CLI debug run (real execution — emails, API calls, etc.) | Debug output streamed | `Run debug session` / `Skip to Publish` |
| **6 — Publish** | Optional Studio Web upload | `DesignerUrl` printed | `Publish to Studio Web` / `Done` |

## Phase 2 — Prototyping

### Structural nodes (full detail)

- Solution + project scaffolding (`uip solution new`, `uip solution project add`, plus JSON scaffolding from `plugins/case/impl-json.md`).
- Root case — `caseplan.json` with `root` block populated (name, caseIdentifier, empty `nodes[]`, empty `edges[]`, empty `caseExitConditions[]`).
- Global variables and arguments — variables block (`inputs`, `outputs`, `inputOutputs`) fully declared. Path is schema-dependent: `root.data.uipath.variables` in v19, top-level `variables` in v20 (Rule 17).
- Stages — all StageIds generated and captured.
- Edges — all edges written; sources and targets resolve.
- Triggers — fully built. Trigger output mappings written (they reference global variables, which already exist).

### Tasks (shape depends on resolution state + task class)

| Task class | Resolved resources | Phase 2 shape |
|---|---|---|
| Non-connector (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `wait-for-timer`) | `task-type-id` resolved | Full `data.inputs[]` schema written (from `uip maestro case tasks describe`). Each input's `value` field is empty (`""`). Outputs populated per plugin. |
| Connector (`connector-activity`, `connector-trigger`) | `type-id` + `connection-id` resolved | `data` contains `type-id` and `connection-id` only. `data.inputs` omitted or empty. **No `is resources describe` / `is triggers describe` call in Phase 2** — schema discovery is deferred to Phase 3. |
| Any task | Unresolved (`<UNRESOLVED: …>` in `tasks.md`) | Skeleton task per Rule 8 of `SKILL.md` — empty `data: {}` (plus `data.taskTitle` / `data.priority` / `data.recipient` for `action`). Marker preserved. See [skeleton-tasks.md](skeleton-tasks.md). |

### What does NOT get written in Phase 2

- Task input `value` bindings (literals, expressions, cross-task references).
- Connector task input/output schemas.
- Conditions of any scope (stage-entry, stage-exit, task-entry, case-exit).
- SLA rules (default, conditional) and escalation rules.

### Phase 2 informational validate

End of Phase 2 mutations, run skeleton-profile validate:

```bash
uip maestro case validate "<caseplan.json path>" --skeleton --output json
```

`--skeleton` runs structural checks only (nodes, edges, identity, types, topology). Skips tasks, SLAs, escalations, and entry/exit rules — all unbound at this gate, filled in Phase 3.

**Informational — do NOT halt on errors or warnings.** Capture error and warning counts (and optionally first few messages); include in hard-stop summary. Errors that remain are structural (dangling edge, missing trigger, duplicate names) and meaningful — user inspects via the existing `Abort` option before continuing.

### Phase 2 hard stop

**Unconditional.** Present summary, then prompt via AskUserQuestion. Prompt is MANDATORY on every run — auto mode, non-interactive mode, prior blanket approval do NOT bypass. Only valid transition out of Phase 2 is user response. If harness refuses interactive prompts, halt with explicit error rather than proceeding silently.

#### Summary content

Print before prompt:

1. Counts: stages / primary stages / exception stages / edges / triggers / tasks total / skeleton tasks / unresolved resources.
2. Validate result (informational): `<N> errors, <M> warnings` — call out that Phase 2 state is expected invalid (unbound inputs / missing conditions / missing SLA all filled in Phase 3). Surfacing counts is enough; do not dump full error list unless user asks.
3. Paths: `caseplan.json`, `tasks.md`, `registry-resolved.json`.

Do not enumerate every task. Studio Web visualization fills that role after publish.

#### Prompt

Use **AskUserQuestion** with three options:

- `Publish for review` — upload skeleton to Studio Web for visual review.
- `Skip publish and continue` — proceed directly to Phase 3.
- `Abort` — stop the skill; leave artifacts in place.

#### On `Publish for review`

1. Run `uip solution resource refresh --solution-folder "<SolutionDir>" --output json` then `uip solution upload "<SolutionDir>" --output json`. Capture full upload response.
2. Parse `DesignerUrl` from response.
3. **MUST emit DesignerUrl as plain-text output to user BEFORE invoking AskUserQuestion**, on its own line:
   `Skeleton published. Review at: <DesignerUrl>`
   Never bundle URL only into question body — some renderers display question before surrounding prose, leaving user without URL until after they answer.
4. Only after URL line emitted, invoke **AskUserQuestion** (second prompt): `Continue to phase 3` / `Abort`.

If `DesignerUrl` missing from response, dump full upload response to `tasks/upload-response.json`, print path, continue to prompt — user can recover URL from file.

Do not warn user about Studio Web edits being overwritten. Phase 6's re-publish (when chosen) overwrites volatile review-time edits with final local state. User can compare Studio Web state before and after Phase 3 to spot edits they want to preserve.

#### On `Skip publish and continue`

Proceed directly to Phase 3.

#### On `Abort`

1. Dump in-memory issue list to `tasks/build-issues.md` per [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md).
2. Print paths of `caseplan.json`, `tasks.md`, `registry-resolved.json`, and solution directory.
3. Exit skill.

Do **not** delete artifacts. User may want to inspect them, or re-run skill later (regenerates `tasks.md` from scratch per Rule 6).

## Phase 3 — Implementation

### Re-entry protocol

Phase 3 begins after user selects `Continue to phase 3` (or `Skip publish and continue`). Before executing any Phase 3 step:

1. **Re-read `tasks.md`** — per Rule 7. Declarative plan is the handoff.
2. **Re-read `caseplan.json`** — authoritative source of all IDs generated in Phase 2:
   - Stage name → StageId (from `schema.nodes[]` where `type === "case-management:Stage"` or `"case-management:ExceptionStage"`, keyed on `data.label`).
   - Trigger ID (from `schema.nodes[]` where `type === "case-management:Trigger"`).
   - Task name → TaskId per stage (from `schema.nodes[<stage>].data.tasks[][]`).
   - Variable name → `var` ID (path schema-dependent: v19 from `root.data.uipath.variables.{inputs,outputs,inputOutputs}`; v20 from top-level `variables.{inputs,outputs,inputOutputs}`).
3. Optionally cross-check against `id-map.json` if JSON-strategy plugins wrote one. `caseplan.json` is source of truth; `id-map.json` is speed-up.

Never trust in-memory maps from Phase 2 without re-reading `caseplan.json` — context may be compacted across hard stop.

### Phase 3 — Execution order

After re-entry:

1. **Connector task detail** — for each connector task in `tasks.md`, run plugin's `impl-json.md` detail steps: `is resources describe` (or `is triggers describe`), write `data.inputs[]` / `data.outputs[]` schema + resolved values.
2. **Task I/O value binding (all task classes)** — per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md). Applies to both non-connector and connector tasks. For each task's inputs in `tasks.md` order, write literal, expression, or cross-task reference (resolved to `=vars.<var>`) into `task.data.inputs[i].value`. Connector tasks have `data.inputs[]` schema written in step 1; value binding happens here in step 2, same as non-connector tasks.
3. **Conditions** — per-scope plugin `impl-json.md`:
   - Stage entry conditions
   - Stage exit conditions
   - Task entry conditions (depends on TaskIds from Phase 2)
   - Case exit conditions
4. **SLA + escalation** — per [`plugins/sla/impl-json.md`](plugins/sla/impl-json.md). Group `tasks.md §4.8` by target (root or stage); write full `slaRules[]` in one mutation per target.

Phase 3 produces a `caseplan.json` that should pass authoritative validation. No hard stop on Phase 3 exit — agent proceeds directly to Phase 4.

## Phase 4 — Validate

End of detail mutations. Run full-mode validate (no `--mode` flag; defaults to full):

```bash
uip maestro case validate "<caseplan.json path>" --output json
```

On success: `{ Result: "Success", Code: "CaseValidate", Data: { File, Status: "Valid" } }` — proceed to Phase 4 dump step.

On failure: output lists `[error]` and `[warning]` entries with path and message. Fix reported issues (usually via targeted re-run of earlier step) and re-run `validate`.

### Retry policy

> **v20 mode override.** When `tasks.md` carries `Schema: v20`, Phase 4 runs **informational** — capture errors and warnings to `build-issues.md`, do NOT retry, do NOT hard-stop on counter exhaustion. Proceed to Phase 5 regardless. Reason: CLI may not yet accept v20 top-level shape; failure does not invalidate the caseplan.json that the skill emitted (Rule 17). v19 retry policy below applies only when `Schema: v19`.

**v19 retry policy.** Up to **3 validation retries** per session. After 3rd failure, halt and ask user with **AskUserQuestion**: show remaining errors and options:

- `Retry with fix` — agent attempts fix, re-runs validate (counter does not reset).
- `Pause for manual edit` — exit skill mid-flight; user edits `caseplan.json` directly and re-runs skill.
- `Abort` — exit; dump `build-issues.md`; leave artifacts in place.

### Dump issue log

After successful validate, write issue list to `tasks/build-issues.md` per [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md), grouped by plugin with summary index. Source of truth for completion report. Write even if zero issues logged (confirms clean build).

On Phase 4 success → proceed to Phase 5.

## Phase 5 — Debug

After Phase 4 success, report results then ask user via **AskUserQuestion**:

- `Run debug session` — run `uip solution resource refresh --solution-folder "<SolutionDir>" --output json` then `uip maestro case debug "<directory>/<solutionName>/<projectName>" --log-level debug --output json`. Streams results.
- `Skip to Publish` — proceed to Phase 6 without debugging.

> **Debug executes case for real — sends emails, posts messages, calls APIs, writes to databases. Only run when user explicitly asks. Never auto-run** (Rule 12).

Requires `uip login`. Uploads to Studio Web, runs in Orchestrator, streams results.

After debug completes, return to Phase 5 prompt so user can re-run or move on. Proceed to Phase 6 only on `Skip to Publish`.

> **v20 mode.** When `tasks.md` carries `Schema: v20`, print this plain-text warning line BEFORE the AskUserQuestion:
> ```
> > v20 mode: uip maestro case debug may reject top-level shape until CLI catches up. Failure does not invalidate caseplan.json.
> ```
> On debug failure in v20 mode, append `caveat: CLI may reject v20 schema — failure may be schema-related not case-bug-related` to the troubleshoot context in `build-issues.md` so the user does not chase a bogus root cause.

### Report fields (printed before prompt)

1. File path of `caseplan.json`.
2. What was built — summary of stages, edges, tasks, conditions, SLA.
3. Validation status — `validate` pass / remaining warnings.
4. Skeleton tasks + unresolved resources — list every skeleton (TaskId, type, display-name, stage) + external resource user must register (task-type-id / connection-id) + wiring-notes from `tasks.md`. See [skeleton-tasks.md](skeleton-tasks.md).
5. Missing connections — connector tasks needing IS connections that don't exist yet.

### Debug notes

- `uip solution resource refresh` MUST run before debug — syncs resources from `bindings_v2.json` so Studio Web can resolve connector dependencies (Rule 14).
- Debug verifies the build actually runs end-to-end before the user commits to a publish. If debug surfaces a fixable issue, see [Step 13a — Troubleshoot failed case](implementation.md#step-13a--troubleshoot-failed-case) and re-run.

## Phase 6 — Publish

After Phase 5 (whether debugged or skipped), prompt via **AskUserQuestion**:

- `Publish to Studio Web` — run `uip solution resource refresh --solution-folder "<SolutionDir>" --output json` then `uip solution upload "<SolutionDir>" --output json`. Print returned `DesignerUrl` on its own line. Exit skill.
- `Done` — exit skill without publishing.

> **v20 mode.** When `tasks.md` carries `Schema: v20`, print this plain-text warning line BEFORE the AskUserQuestion:
> ```
> > v20 mode: uip solution upload may reject top-level shape until CLI catches up. Failure non-fatal — caseplan.json still valid v20.
> ```
> If `Publish to Studio Web` is picked and upload fails, dump full response to `tasks/upload-response.json`, print the path, then re-show this Phase 6 AskUserQuestion. Do not auto-exit on upload failure — let user decide whether to retry or `Done`.

### Publish notes

- `uip solution upload` accepts solution directory (folder containing `.uipx`) directly — no intermediate bundling step.
- `uip solution resource refresh` MUST run before upload — syncs resources from `bindings_v2.json` so Studio Web can resolve connector dependencies (Rule 14).
- Do **NOT** run `uip maestro case pack` + `uip solution publish` unless user explicitly asks for Orchestrator deployment. That path puts case directly into Orchestrator, bypassing Studio Web. Default is always Studio Web.

For further authoring changes (add task, tweak condition, etc.), user updates `sdd.md` and re-runs skill from Phase 1 — skill does not offer in-place incremental edits.

## Skeleton tasks — unchanged semantics

Skeleton tasks (empty `data: {}` for unresolved resources) behave the same in all phases. Phase 2 creates them; Phase 3 does **not** upgrade them to typed tasks — upgrading requires user to register missing resource externally. See [skeleton-tasks.md](skeleton-tasks.md).

Phase 3 still wires skeleton TaskIds into:
- Task-entry conditions that reference the skeleton.
- Stage-exit `selected-tasks-completed` rules that include the skeleton.

It does **not** write `data.inputs` / `data.outputs` for skeletons. Input binding deferred to user's post-build upgrade pass.

## Abort semantics

Abort can occur at any hard stop:

- Phase 2 first prompt (`Publish for review` / `Skip` / `Abort`).
- Phase 2 second prompt (`Continue to phase 3` / `Abort`) after publishing.
- Phase 4 retry-cap prompt (`Retry with fix` / `Pause for manual edit` / `Abort`).

All follow same cleanup:

1. Dump `build-issues.md`.
2. Print paths.
3. Exit.

No artifact deletion. No rollback. User owns partial state.

## Out of scope

- **Re-ingesting Studio Web edits.** If user edits published skeleton in Studio Web during review, edits are not round-tripped back into local `caseplan.json`. Phase 3 writes on top of local state; Phase 6 re-publish overwrites Studio Web with completed local build.
- **Resuming aborted session.** Re-running skill regenerates `tasks.md` from scratch (Rule 6) and re-executes Phase 2 onwards.

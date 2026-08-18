# Phased Execution: Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7

Authoritative reference for the post-planning execution flow. Read before executing any T-entry from `tasks.md`.

> **Editing an existing case?** Targeted edits to an existing `caseplan.json` skip these phases — see [brownfield.md](brownfield.md).

> **Relationship to other docs.** This document defines phase boundaries and hard-stop contracts. Per-plugin execution detail lives in `plugins/<name>/impl-json.md`. Per-step ordering and file-system mutations live in [implementation.md](implementation.md).

## Downstream CLI compatibility

The skill emits the `27.0.0` top-level shape (`{ id, version, name, metadata, bindings, variables, nodes, edges, layout }`). Phase-specific downstream caveats:

| Phase | Behavior |
|---|---|
| 2 — Prototyping | Informational validate, no halt on errors. |
| 4 — Validate | Authoritative — `uip maestro case validate` accepts the top-level shape. Retry-and-fix on failure, 3-retry cap, hard stop on 3rd failure. |
| 5 — Publish | Before the AskUserQuestion, print plain-text warning: `> uip solution upload may reject the top-level shape until the CLI catches up. Failure non-fatal — caseplan.json still valid.` On failure, re-run the upload once without `--output-filter` and dump that unfiltered response to `tasks/upload-response.json`, re-show Phase 5 prompt. |
| 6 — Debug | Before the AskUserQuestion, print plain-text warning: `> uip maestro case debug may reject the top-level shape. Failure does not invalidate caseplan.json.` On failure, note `caveat: CLI may reject schema — failure may be schema-related not case-bug-related` in build-issues.md. |
| 7 — Publish to Orchestrator | Packs and publishes the whole solution, so the case's top-level shape is carried through unvalidated by this step. On `pack`/`publish` failure, report the CLI error verbatim, note it in build-issues.md, and re-show the Phase 7 prompt. |

Skill stays emit-honest: JSON-shape correctness is the skill's job, downstream CLI accept-correctness is outside scope.

## Why phased

Once `tasks.md` is generated, skill does **not** build the full case in one pass. Phase 2 produces a reviewable preview containing structure, conditions, SLA, and escalation; Phase 3 adds the detail that depends on connector `case spec` calls and task value binding. Whether the boundary pauses is the user's up-front build-review preference (SKILL.md Rule 11): pause-at-preview stops for visual review; straight-through narrates the milestone and continues. Validate (Phase 4), Publish (Phase 5), Debug (Phase 6), and Publish to Orchestrator (Phase 7) follow; the publish, debug, and Orchestrator-publish gates are unconditional. Publish runs before Debug so the debug session exercises the same build the user just shipped to Studio Web (debug uploads there anyway). Publish to Orchestrator runs last so only an exercised build reaches the tenant solution feed.

Decisions are front-loaded so the build can run unattended; the gates that remain protect real-world side effects (publish ships the case to Studio Web, debug executes it, publish to Orchestrator ships it to the tenant solution feed).

## Phase summary

| Phase | What gets built | Output | Hard stop on exit |
|---|---|---|---|
| **2 — Prototyping** | Solution/project, structure, triggers, task shapes, conditions in all 4 scopes, SLA + escalation; connector-bound rules use canonical stubs | `caseplan.json` emitted; `--skeleton-v2` preview validate attempted, with unsupported-flag fallback to `--skeleton` | Pause-at-preview runs: `Publish for review` / `Skip publish and continue` / `Abort`. Straight-through runs: none — counts line, continue (Rule 11) |
| **3 — Implementation** | Connector task schemas, task I/O value binding, resolved connector-rule stub upgrades | `caseplan.json` ready for authoritative validation | None — proceeds to Phase 4 |
| **4 — Validate** | Run authoritative `uip maestro case validate`, summarize `build-issues.md` (journal already on disk) | `caseplan.json` passes full validation | On 3rd validate failure: `Retry with fix` / `Pause for manual edit` / `Abort` |
| **5 — Publish** | Optional Studio Web upload | `DesignerUrl` printed | `Publish to Studio Web` / `Skip to Debug` |
| **6 — Debug** | Optional CLI debug run (real execution — emails, API calls, etc.) | Debug output streamed | `Run debug session` / `Continue to publish` |
| **7 — Publish to Orchestrator** | Optional `case pack` + `solution pack` + `solution publish` to the tenant solution feed | `.zip` packed; publish result printed | `Publish to Orchestrator` / `Done` |

## Phase 2 — Prototyping

### Structural nodes (full detail)

- Solution + project scaffolding (`uip solution init`, `uip solution projects add`, plus JSON scaffolding from `plugins/case/impl-json.md`).
- Root case — `caseplan.json` with top-level fields + `metadata` block populated (name, `metadata.caseIdentifier`, empty `nodes[]`, empty `edges[]`).
- Global variables and arguments — variables block (`inputs`, `outputs`, `inputOutputs`) fully declared at top-level `variables`.
- Stages — all StageIds generated and captured.
- Edges — none authored (Rule 20); `schema.edges` stays `[]`. Stage transitions are condition-driven (written in Phase 2).
- Triggers — fully built. Trigger output mappings written (they reference global variables, which already exist).
- Entry-points input/output — `entry-points.json` `input`/`output` schemas refreshed from the declared In/Out arguments (Step 6.3, per [entry-points-sync.md](entry-points-sync.md)). Makes the Phase-2 publish-for-review contract correct; idempotent.

### Tasks (shape depends on resolution state + task class)

| Task class | Resolved resources | Phase 2 shape |
|---|---|---|
| Non-connector (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `wait-for-timer`) | `task-type-id` resolved | Full `data.inputs[]` schema written (from `uip maestro case tasks describe`). Each input's `value` field is empty (`""`). Outputs and task-specific scalar fields (e.g. `action`'s `taskTitle`/`priority`/`recipient`/`labels`) populated per plugin — these are final at Step 2; only input `value`s defer to Phase 3. |
| Connector (`connector-activity`, `connector-trigger`) | `type-id` + `connection-id` resolved | `data.typeId` + `data.connectionId` set. `data.inputs` omitted or empty. **No `case spec` call in Phase 2** — schema discovery is deferred to Phase 3. |
| Any task | Unresolved (`<UNRESOLVED: …>` in `tasks.md`) | Placeholder task per Rule 8 of `SKILL.md` — empty `data: {}` (plus `data.taskTitle` / `data.priority` / `data.recipient` for `action`). Marker preserved. See [placeholder-tasks.md](placeholder-tasks.md). |
| `agent` / `api-workflow` built inline | Built + bound in Phase 1 at the Rule 17 gate | **Not a placeholder** — fully resolved task (name+folder binding, `resourceKey="solution_folder.<name>"`, **`folderPath` binding `default` = `""`** — co-located runtime folder; `solution_folder` stays only in `resourceKey`). Phase 2 treats it like any resolved resource. See [registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery). |

### Rules, SLA, and connector-rule stubs

- Write SLA and escalation objects first, minting their stable `sla_*` / `esc_*` IDs with the objects. Conditions that use `sla-status-change` resolve those existing IDs; there is no separate Phase 3 preallocation step.
- Write stage-entry, stage-exit, task-entry, and case-exit conditions in their final scope and position.
- Every `wait-for-connector` condition rule gets the canonical stub `uipath` in Phase 2, even when its connector resolved. Phase 3 replaces only `rule.uipath` for resolved connectors. A truly unresolved connector keeps the stub and is reported.

### What does NOT get written in Phase 2

- Task input `value` bindings (literals, expressions, cross-task references).
- Connector task input/output schemas.
- Final `uipath.context` / inputs / outputs and Connection bindings for connector-bound condition rules.

### Phase 2 informational validate

End of Phase 2 mutations, try the richer preview profile first:

```bash
uip maestro case validate "<caseplan.json path>" --skeleton-v2 --output json
```

If the parser response names `--skeleton-v2` as unknown or unsupported (typically `ErrorCode: "invalid_argument"` and exit 3), re-run once with legacy `--skeleton`. Exit 3 without that flag-specific message is not sufficient. Do not fall back when v2 ran and returned genuine validation findings. Legacy `--skeleton` checks structure only and skips the conditions/SLA present in the preview; Phase 4 full validation remains authoritative.

**Informational — do NOT halt on errors or warnings.** Capture the selected profile plus error/warning counts (and optionally the first few messages) for the boundary summary.

### Phase 2 hard stop

**Gated by the up-front build-review preference (SKILL.md Rule 11) — never a mid-build surprise.** The preference was captured at journey start: the design-handoff Case Review Build options on the greenfield journey, the single post-roadmap question on the provided-SDD journey. Always print the §Summary content below, then branch:

- **Straight-through** → continue directly into Phase 3 with no prompt; the summary doubles as the milestone narration line.
- **Pause-at-preview** → present the §Prompt below; only a user response transitions out of Phase 2.
- **No recorded preference** (resumed or legacy run): interactive → ask the §Prompt now; non-interactive → straight-through (no publish — Phase 5 remains the only, still-gated, publish point) and say so in one line.

The Phase 4 retry-cap, Phase 5 publish, Phase 6 debug-consent, and Phase 7 publish-consent stops below are independent of this preference and are never bypassed.

**Next-step rule.** Every user-visible stop or handoff after build progress must include a short `Suggested next steps` line before the prompt or final exit. Do this after straight-through completion reports, pause-at-preview summaries, published preview URLs, publish completion, debug results, and abort/done exits. Keep it concrete: inspect the preview, continue implementation, publish, run debug, fix listed placeholders/connections, or edit the named artifact and re-run.

#### Summary content

Print (before the prompt on the pause branch; as the continuation line otherwise):

1. Counts: stages / primary stages / secondary stages / triggers / tasks total / placeholder tasks / unresolved resources.
2. Validate result and profile: `skeleton-v2: <N> errors, <M> warnings` or `skeleton (fallback; rules/SLA deferred to Phase 4): <N> errors, <M> warnings`. Surfacing counts is enough; do not dump the full list unless the user asks.
3. Paths: `caseplan.json`, `tasks.md`, `registry-resolved.json`.
4. Suggested next steps:
   - Straight-through: `Suggested next steps: I'll continue wiring the implementation now; say stop if you want to inspect the skeleton first.`
   - Pause-at-preview: `Suggested next steps: publish the skeleton for visual review, continue locally without preview, or abort and inspect the files.`

Do not enumerate every task. Studio Web visualization fills that role after publish.

#### Prompt (pause-at-preview branch only)

Use **AskUserQuestion** with three options:

- `Publish for review` — upload skeleton to Studio Web for visual review.
- `Skip publish and continue` — proceed directly to Phase 3.
- `Abort` — stop the skill; leave artifacts in place.

#### On `Publish for review`

1. Run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json` then `uip solution upload "<SolutionDir>" --output json --output-filter "{Status: Status, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"`. `--output-filter` is mandatory (see [case-commands.md § uip solution upload](case-commands.md#uip-solution-upload)).
2. Parse `DesignerUrl` from response.
3. **MUST emit DesignerUrl as plain-text output to user BEFORE invoking AskUserQuestion**, on its own line:
   `Skeleton published. Review at: <DesignerUrl>`
   Never bundle URL only into question body — some renderers display question before surrounding prose, leaving user without URL until after they answer.
4. Print `Suggested next steps: inspect the skeleton in Studio Web, then continue implementation here or abort and keep the artifacts for manual review.`
5. Only after URL line and suggested next steps are emitted, invoke **AskUserQuestion** (second prompt): `Continue to implementation` / `Abort`.

If `DesignerUrl` missing from the filtered response, re-run the upload once **without** `--output-filter`, dump that unfiltered response to `tasks/upload-response.json`, print path, continue to prompt — user can recover URL from file.

Do not warn user about Studio Web edits being overwritten. Phase 5's re-publish (when chosen) overwrites volatile review-time edits with final local state. User can compare Studio Web state before and after Phase 3 to spot edits they want to preserve.

#### On `Skip publish and continue`

Proceed directly to Phase 3.

#### On `Abort`

1. **Append** the current section's buffered issues to the existing `tasks/build-issues.md` journal, then fill the summary block, per [`plugins/logging/impl-json.md` § Flush](plugins/logging/impl-json.md). **Never whole-file dump here** — the journal already holds rows from every completed section and the per-section buffer has been cleared, so replacing the file would destroy that history. If the file does not exist (abort before the first section boundary), create it per § Flush.
2. Print paths of `caseplan.json`, `tasks.md`, `registry-resolved.json`, and solution directory.
3. Print `Suggested next steps: inspect tasks/build-issues.md and the generated artifacts, then rerun after editing the design or plan.`
4. Exit skill.

Do **not** delete artifacts. User may want to inspect them, or re-run skill later (regenerates `tasks.md` from scratch per Rule 6).

## Phase 3 — Implementation

### Re-entry protocol

Phase 3 begins after the straight-through continuation, or after the user selects `Continue to implementation` / `Skip publish and continue` on a pause-at-preview run. Before executing any Phase 3 step:

1. **Re-read `tasks.md`** — per Rule 7. Declarative plan is the handoff.
2. **Re-read `caseplan.json`** — authoritative source of all IDs generated in Phase 2:
   - Stage name → StageId (from `schema.nodes[]` where `type === "case-management:Stage"`, keyed on `data.label`; secondary stages are the same type with `data.stageType === "secondary"`).
   - Trigger ID (from `schema.nodes[]` where `type === "uipath.case.trigger"`).
   - Task name → TaskId per stage (from `schema.nodes[<stage>].data.tasks[][]`).
   - Variable name → `var` ID (from top-level `variables.{inputs,outputs,inputOutputs}`).
   - SLA/escalation IDs and all condition/rule IDs, including connector rules whose `uipath` still carries the canonical stub.
3. Optionally cross-check against `id-map.json` if JSON-strategy plugins wrote one. `caseplan.json` is source of truth; `id-map.json` is speed-up.

Never trust in-memory maps from Phase 2 without re-reading `caseplan.json` — context may be compacted across hard stop.

### Phase 3 — Execution order

> **In-session schema memo.** `tasks describe` / `case spec` results fetched this session are carried forward — in memory and in their persisted artifacts (`tasks/registry-resolved.json`, `tasks/spec-cache.<elementId>.json`, `tasks/trigger-spec-cache.json`). NEVER re-run an identical describe/spec call this session (same type + id): re-read the persisted artifact instead. Observed failure: the same 5-type `tasks describe` set re-ran verbatim 12m45s later, costing ~2–4 minutes and redundant turns per build.

After re-entry:

1. **Connector task detail** — for each connector task in `tasks.md`, run plugin's `impl-json.md` detail steps: `case spec --type {activity,trigger} --input-details`, then mint `data.context[]` / `data.inputs[]` / `data.outputs[]` from the populated `caseShape` (placeholder substitution + var/id minting).
2. **Task I/O value binding (all task classes)** — per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md). Applies to both non-connector and connector tasks. For each task's inputs in `tasks.md` order, write literal, expression, or cross-task reference (resolved to `=vars.<outputReferenceId>` through the common `.id`-based resolver) into `task.data.inputs[i].value`. Connector tasks have `data.inputs[]` schema written in step 1; value binding happens here in step 2, same as non-connector tasks.
3. **Connector-bound condition-rule upgrade** — scan all four scopes for canonical stubs. For each resolved connector, run `case spec --type trigger --input-details` and replace only `rule.uipath`, preserving rule/condition IDs, expressions, scope, and placement. Unresolved connectors keep the stub and are reported.
4. **In-expression marker resolution** — per [`plugins/variables/io-binding/impl-json.md § In-Expression Marker Resolution`](plugins/variables/io-binding/impl-json.md). After all outputs are minted/deduped, resolve every `vars.$xref('Stage','Task','output')` marker in `caseplan.json` to bare `vars.<outputReferenceId>` in one sink-blind whole-file pass (input payloads, conditions, SLA, connector bodies). Unresolved triple or reference ID → ERROR.
5. **End-of-Phase-3 validator pass** — per [`implementation.md § Step 12`](implementation.md). Run Checks 1-11 (=vars.X resolution, Out-arg producer presence, type mismatch, surviving `$xref` markers, resolved-resource I/O completeness, entry-point schema parity, bindings sidecar parity, output-ID uniqueness, resolved-resource emission and repair preservation, formal-arg slot ID format, resourceKey self-consistency). AskUserQuestion for unresolved references (incl. `$xref` markers), pure orphan Out-args, and unbound required inputs / phantom output fields; option (c)/(d) "continue with best-effort emit" preserves forward progress. Checks 6-11 are non-interactive: on mismatch auto re-run/regenerate/re-mint once where the check permits it; Check 6 logs if still divergent, while Checks 7, 9, 10, and 11 halt before Phase 4 if still divergent. Never HALT otherwise.

Phase 3 produces a `caseplan.json` that should pass authoritative validation. No hard stop (no AskUserQuestion gate) on Phase 3 exit — agent proceeds directly to Phase 4. Sole blockers: Check 7 parity still divergent after regeneration, any Check 9 resolved-resource emission/preservation failure, any Check 10 formal-arg slot id still malformed after the repair pass, any Check 11 resourceKey still self-inconsistent after the repair pass, or any Check 12 resolved connector node whose `context` / root bindings are still missing after the repair pass (halt per [`implementation.md § Step 12`](implementation.md)).

## Phase 4 — Validate

End of detail mutations. Run full-mode validate (omit `--skeleton`; defaults to full):

```bash
uip maestro case validate "<caseplan.json path>" --output json
```

On success: `{ Result: "Success", Code: "CaseValidate", Data: { File, Status: "Valid" } }` — proceed to the Phase 4 issue-log summary step.

On failure: output lists `[error]` and `[warning]` entries with path and message. Fix reported issues (usually via targeted re-run of earlier step) and re-run `validate`.

### Validate-loop guard — no re-validate without an intervening edit

**Never re-run `uip maestro case validate` unless `caseplan.json` (or a sidecar it validates) changed since the last run.** A validate that follows another validate with zero edits in between is a no-op that costs a full CLI round-trip and a turn — observed worst case: 20 validates in one session, 14 of 19 re-runs with no intervening edit, 36% of wall clock. The guard applies in every phase: Phase 2's informational validate runs once, Phase 4's authoritative validate runs once per fix. Fix → edit → validate is the only legal loop shape; validate → validate is a defect.

### Retry policy

Up to **3 validation retries** per session — each retry MUST be preceded by a fix edit (validate-loop guard above). After 3rd failure, halt and ask user with **AskUserQuestion**: show remaining errors and options:

- `Retry with fix` — agent attempts fix, re-runs validate (counter does not reset).
- `Pause for manual edit` — exit skill mid-flight; user edits `caseplan.json` directly and re-runs skill.
- `Abort` — exit; append the current buffer to the `build-issues.md` journal and summarize (never replace it); leave artifacts in place.

### Summarize the issue log

`tasks/build-issues.md` already exists — it is flushed at every section boundary from Phase 2 onward per [`plugins/logging/impl-json.md` § Flush](plugins/logging/impl-json.md). After successful validate, flush the final section's buffer, then read the journal back and fill the grouped summary block. Source of truth for the completion report; the counts come from the file, not from reasoning.

If the file is absent here the incremental flush was skipped — reconstruct from on-disk artifacts and stamp the `NOTE:` line per [§ Recovery](plugins/logging/impl-json.md).

On Phase 4 success → proceed to Phase 5.

## Phase 5 — Publish

After Phase 4 success, report results then ask user via **AskUserQuestion**:

- `Publish to Studio Web` — run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json` then `uip solution upload "<SolutionDir>" --output json --output-filter "{Status: Status, SolutionId: SolutionId, DesignerUrl: DesignerUrl}"`. Print returned `DesignerUrl` on its own line. Proceed to Phase 6.
- `Skip to Debug` — proceed to Phase 6 without publishing.

Before this prompt, include `Suggested next steps: publish to Studio Web when you want a designer-visible version, or skip to debug if the local artifacts are enough for now.` After a successful publish, print `Suggested next steps: open the Designer URL, verify resources and connections, then run a debug session to exercise the case.`

### Report fields (printed before prompt)

1. File path of `caseplan.json`.
2. What was built — summary of stages, tasks, conditions, SLA.
3. Validation status — `validate` pass / remaining warnings.
4. Placeholder tasks + unresolved resources — list every placeholder (TaskId, type, display-name, stage) + external resource user must register (task-type-id / connection-id) + wiring-notes from `tasks.md`. Also list **agents / API workflows built inline** (built as in-solution siblings, already bound) and any **built but unreferenced** (reject case) separately — they need no user action. See [placeholder-tasks.md § Completion-Report Shape](placeholder-tasks.md#completion-report-shape).
5. Missing connections — connector tasks needing IS connections that don't exist yet.
6. Suggested next steps — one short line before the prompt (the publish/skip-to-debug line above). If placeholders or missing connections exist, mention fixing/registering those before publish.

### Publish notes

- `uip solution upload` accepts solution directory (folder containing `.uipx`) directly — no intermediate bundling step.
- **`--output-filter` is mandatory on every `uip solution upload` call** — see [case-commands.md § uip solution upload](case-commands.md#uip-solution-upload) for the projection and fallback procedure.
- `uip solution resources refresh` MUST run before upload — syncs resources from `bindings_v2.json` so Studio Web can resolve connector dependencies (Rule 14).
- Do **NOT** run `uip solution pack` + `uip solution publish` in this phase. That chain is Phase 7 and has its own consent gate — see [§ Phase 7](#phase-7--publish-to-orchestrator). Studio Web (`uip solution upload`) is always the Phase 5 path.
- Publish ships a build that has not been exercised — the debug gate follows (Phase 6). If a Phase 6 debug run leads to a fix, re-run this phase's `resources refresh` + `solution upload` so Studio Web holds the fixed build.

## Phase 6 — Debug

After Phase 5 (whether published or skipped), prompt via **AskUserQuestion**:

- `Run debug session` — run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json` then `uip maestro case debug "<directory>/<solutionName>/<projectName>" --log-level debug --output json`. Streams results.
- `Continue to publish` — proceed to Phase 7 without debugging.

> **Debug executes case for real — sends emails, posts messages, calls APIs, writes to databases. Only run when user explicitly asks. Never auto-run** (Rule 12).

Requires `uip login`. Uploads to Studio Web, runs in Orchestrator, streams results.

After debug completes, return to Phase 6 prompt so user can re-run or move on. Leave the phase only on `Continue to publish`.

Before this prompt, include `Suggested next steps: run a debug session if you are ready to exercise the case, or continue to the Orchestrator publish gate if validation (and publish) is enough for now.` After debug results, print `Suggested next steps: inspect the debug output, fix and re-run, re-publish with the Phase 5 commands if a fix changed the build, or continue to the Orchestrator publish gate.`

### Debug notes

- `uip solution resources refresh` MUST run before debug — syncs resources from `bindings_v2.json` so Studio Web can resolve connector dependencies (Rule 14).
- Debug verifies the build actually runs end-to-end. If debug surfaces a fixable issue, see [Step 15a — Troubleshoot failed case](implementation.md#step-15a--troubleshoot-failed-case) and re-run; if the case was already published, re-publish afterwards so the published build carries the fix.
- **Inline-built api-workflow siblings are NOT provisioned by `case debug`** — that task faults with incident `170007` ("job's associated process could not be found") by design; agent siblings do resolve in debug. Verifying that task's runtime needs a full solution deploy (`uip maestro case pack` → `uip solution pack` → `uip solution publish` → `uip solution deploy run` — `case pack` first, always, per [§ Phase 7](#why-case-pack-is-mandatory)) — an Orchestrator install that goes beyond [§ Phase 7](#phase-7--publish-to-orchestrator) (which stops at publish), so **offer it via AskUserQuestion, never run it unprompted** (options — `Run full solution deploy` / `Skip (mark debug-unverifiable)`); if declined, report the task as debug-unverifiable and continue. See [api-workflow/planning.md § Creating an API workflow inline](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline).

## Phase 7 — Publish to Orchestrator

After Phase 6 (whether debug ran or was skipped), prompt via **AskUserQuestion**:

- `Publish to Orchestrator` — run the four commands below in order.
- `Done` — exit skill without publishing.

> **Publish to Orchestrator ships the case to the tenant solution feed — a real, outward-facing publish. Only run when user explicitly selects it. Never auto-run** (Rule 12).

Requires `uip login`.

### Publish commands

```bash
uip solution resources refresh --solution-folder "<SolutionDir>" --output json
uip maestro case pack "<SolutionDir>/<ProjectName>" "<SolutionDir>/dist" --output json
uip solution pack "<SolutionDir>" "<SolutionDir>/dist" --output json
uip solution publish "<packagePath>" --wait --output json
```

1. **`resources refresh`** — same Rule 14 requirement as publish and debug: syncs artefact files and debug overwrites from `bindings_v2.json` before they are bundled into the package.
2. **`case pack`** — recompiles `caseplan.json` into `caseplan.json.bpmn` inside the **case project directory**. **Mandatory, in every run, no exceptions** — see § Why `case pack` is mandatory below. Its `.nupkg` output is a throwaway; only the regenerated `.bpmn` matters. Point the output at `<SolutionDir>/dist` (a sibling of the project dir — stray folders under the solution root are not bundled). Never point it inside the case project directory.
3. **`solution pack`** — packs the **solution directory** (the folder containing the `.uipx`), not the case project. It packs each contained project into a `.nupkg` and bundles them into a single `.zip` under `<SolutionDir>/dist`. Add `--version <version>` when the user names one; default is `1.0.0`. Republishing an existing `name+version` pair is rejected by the feed — bump `--version` on a re-deploy.
4. **`solution publish`** — uploads the packed `.zip` to the tenant solution feed. `--wait` blocks until the package reaches `Ready`/`Active`. Add `--personal-workspace` only when the user asks for their Personal Workspace feed instead of the tenant feed. Flags: [case-commands.md § uip solution publish](case-commands.md#uip-solution-publish).

**Read `<packagePath>` from the `solution pack` response `Data.Packages`, or list `<SolutionDir>/dist` — never guess the filename.** The name is `<name>_<version>.zip` — underscore, not dot. `solution pack` writes `<SolutionName>_<version>.zip`; `case pack` writes `<Name>.case.Case.<version>.nupkg` — never confuse the two, and never hand the `.nupkg` to `publish`.

### Why `case pack` is mandatory

`uip solution pack` **bundles the `.bpmn` it finds on disk — it never compiles one.** `uip maestro case validate` does not generate it either. Only `uip maestro case pack` compiles `caseplan.json` → `caseplan.json.bpmn`. So:

- Run it **on every Phase 7 pass**, whether or not Phase 5 / Phase 6 ran, and whether or not a `.bpmn` already exists. Prior phases are optional and skippable; a run that goes Phase 4 → Phase 7 has never compiled a `.bpmn` at all.
- Skipping it publishes a package whose `content/` holds `caseplan.json` with **no** `caseplan.json.bpmn`, or — worse — a **stale** `.bpmn` compiled before the latest edits. Both pack and publish succeed; the defect only surfaces at deploy/run time.
- `case pack` requires `package-descriptor.json` in the case project directory (written at scaffold, [plugins/case/impl-json.md](plugins/case/impl-json.md)). If it fails with `Missing package-descriptor.json`, restore that file — do not skip the step.

> `uip maestro case pack` is **not** the publish artifact. It emits a single project `.nupkg`, which `solution publish` does not accept — `solution pack` produces its own project `.nupkg` internally and wraps it in the `.zip`. Run `case pack` for the BPMN recompile only; always publish the `solution pack` `.zip`.

Phase 7 stops at publish. `uip solution deploy run` (the step that installs the solution into an Orchestrator folder) is out of scope — report the published package and tell the user to deploy it from Orchestrator.

### On failure

If `case pack`, `solution pack`, or `publish` fails, print the CLI error verbatim, note it in `build-issues.md`, and re-show the Phase 7 prompt. Do not retry with a different pack command, and never work around a `case pack` failure by going straight to `solution pack` — that ships a package with a missing or stale `.bpmn`. A `processKey` collision on publish means the `name+version` pair already exists on the feed — re-run with a bumped `--version`.

### Suggested next steps

Before the prompt: `Suggested next steps: publish to Orchestrator when you want the case on the tenant solution feed, or stop here if Studio Web and debug are enough.` After a successful publish: `Suggested next steps: verify the package with 'uip solution packages list', then deploy it to an Orchestrator folder.` On `Done`: `Suggested next steps: review caseplan.json/tasks.md locally or update sdd.md and re-run when you want changes.`

### Publish-to-Orchestrator notes

- Phase 7 is the last phase. Nothing re-enters the build pipeline after it.
- A Phase 7 publish does **not** replace Phase 5 — Studio Web (`uip solution upload`) and the solution feed are separate destinations. A case can go to both, neither, or one.
- If a Phase 6 fix changed the build after a Phase 7 publish, re-run Phase 7 with a bumped `--version`; the feed rejects duplicate `name+version` pairs.

Deployment and activation are platform lifecycle concerns. Use the platform workflow for `uip solution deploy ...` commands and keep this case skill focused on the case project/package boundary.

For further authoring changes (add task, tweak condition, etc.), user updates `sdd.md` and re-runs skill from Phase 1 — skill does not offer in-place incremental edits.

## Placeholder tasks — unchanged semantics

Placeholder tasks (empty `data: {}` for unresolved resources) behave the same in all phases. Phase 2 creates them; Phase 3 does **not** upgrade them to typed tasks — upgrading requires user to register missing resource externally. See [placeholder-tasks.md](placeholder-tasks.md).

> **Agents / API workflows built inline are not placeholders.** When the user picks **Create** at the Rule 17 gate, Phase 1 builds the resource (a side effect — spawns a sub-agent invoking `uipath-agents` / `uipath-api-workflow`, registers the sibling, binds it) so it enters Phase 2 as a fully resolved task. Phase 3 never upgrades it (nothing to upgrade). Only resources the user declined/skipped or whose build failed become placeholders. See [registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery).

Phase 3 still wires placeholder TaskIds into:
- Task-entry conditions that reference the placeholder.
- Stage-exit `selected-tasks-completed` rules that include the placeholder.

It does **not** write `data.inputs` / `data.outputs` for placeholders. Input binding deferred to user's post-build upgrade pass.

## Abort semantics

Abort can occur at any hard stop:

- Phase 2 first prompt (`Publish for review` / `Skip` / `Abort`) — pause-at-preview runs only.
- Phase 2 second prompt (`Continue to implementation` / `Abort`) after publishing.
- Phase 4 retry-cap prompt (`Retry with fix` / `Pause for manual edit` / `Abort`).

All follow same cleanup:

1. Append the current buffer to the `build-issues.md` journal and fill the summary — append-only, never a whole-file replace.
2. Print paths.
3. Exit.

No artifact deletion. No rollback. User owns partial state.

## Out of scope

- **Re-ingesting Studio Web edits.** If user edits published placeholder in Studio Web during review, edits are not round-tripped back into local `caseplan.json`. Phase 3 writes on top of local state; Phase 5 re-publish overwrites Studio Web with completed local build.
- **Resuming aborted session.** Re-running skill regenerates `tasks.md` from scratch (Rule 6) and re-executes Phase 2 onwards.

<!-- END: phased-execution.md -->

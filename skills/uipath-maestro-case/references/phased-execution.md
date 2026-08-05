# Phased Execution: Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6

Authoritative reference for the post-planning execution flow. Read before executing any T-entry from `tasks.md`.

> **Editing an existing case?** Targeted edits to an existing `caseplan.json` skip these phases — see [brownfield.md](brownfield.md).

> **Relationship to other docs.** This document defines phase boundaries and hard-stop contracts. Per-plugin execution detail lives in `plugins/<name>/impl-json.md`. Per-step ordering and file-system mutations live in [implementation.md](implementation.md).

## Downstream CLI compatibility

The skill emits the `23.0.0` top-level shape (`{ id, version, name, metadata, bindings, variables, nodes, edges, layout }`). Phase-specific downstream caveats:

| Phase | Behavior |
|---|---|
| 2 — Prototyping | Informational gate validate — `--skeleton-v2`, falling back to **full mode** ([case-commands.md § Phase 2 gate profile](case-commands.md#phase-2-gate-profile--probe-once-cache-fall-back-to-full-mode)), no halt on errors. |
| 4 — Validate | Authoritative — `uip maestro case validate` accepts the top-level shape. Retry-and-fix on failure, 3-retry cap, hard stop on 3rd failure. |
| 5 — Debug | Before the AskUserQuestion, print plain-text warning: `> uip maestro case debug may reject the top-level shape. Failure does not invalidate caseplan.json.` On failure, note `caveat: CLI may reject schema — failure may be schema-related not case-bug-related` in build-issues.md. |
| 6 — Publish | Before the AskUserQuestion, print plain-text warning: `> uip solution upload may reject the top-level shape until the CLI catches up. Failure non-fatal — caseplan.json still valid.` On failure, dump response to `tasks/upload-response.json`, re-show Phase 6 prompt. |

Skill stays emit-honest: JSON-shape correctness is the skill's job, downstream CLI accept-correctness is outside scope.

## Why phased

Once `tasks.md` is generated, skill does **not** build full case in one pass. It builds the reviewable shape first (Phase 2 Prototyping) — stages, tasks, triggers, variables, **and the conditions and SLA that make the graph a flow** — then wires the connector detail and value bindings (Phase 3 Implementation). Whether the boundary pauses is the user's up-front build-review preference (SKILL.md Rule 11): pause-at-preview stops for the visual review; straight-through narrates the milestone and continues. Validate (Phase 4), Debug (Phase 5), and Publish (Phase 6) follow; the debug and publish gates are unconditional. Debug runs before Publish so the user only publishes a build they've verified end-to-end.

**The boundary sits at the CLI-gather line, not at a complexity line.** Phase 2 holds what the agent can write from data already in hand; Phase 3 holds the connector gathers — connector task schemas, task input `value`s, and connector rule `uipath` blocks — and the IDs those `uip maestro case spec` round-trips mint. The line is not absolute: a resolved event trigger runs its own `case spec` at Phase 2 Step 6.1, since the TriggerId it produces is a Step 6.2 prerequisite. Conditions and SLA/escalation reference only StageIds, TaskIds, and variable IDs — all minted in Phase 2 — so they are authored in Phase 2. This matters for the preview: edges are retired (Rule 20), so **conditions *are* the flow**. A preview without them shows disconnected boxes. The one exception is the `wait-for-connector` rule, whose `uipath` block requires `case spec`; Phase 2 writes it with a stub `uipath` and Phase 3 upgrades the stub in place.

Decisions are front-loaded so the build can run unattended; the gates that remain protect real-world side effects (debug executes the case, publish ships it).

## Phase summary

| Phase | What gets built | Output | Hard stop on exit |
|---|---|---|---|
| **2 — Prototyping** | Solution + project, root case, global variables, stages, triggers (full), tasks (name + type, no value binding), placeholder tasks for unresolved, **conditions (all 4 scopes; `wait-for-connector` rules as stub `uipath`)**, **SLA + escalation** | `caseplan.json` emitted; gate validate run | Pause-at-preview runs: `Publish for review` / `Skip publish and continue` / `Abort`. Straight-through runs: none — counts line, continue (Rule 11) |
| **3 — Implementation** | Connector task schemas, task I/O value binding, connector-bound condition rule upgrade (stub → real `uipath`), `$xref` marker resolution | `caseplan.json` ready for authoritative validation | None — proceeds to Phase 4 |
| **4 — Validate** | Run authoritative `uip maestro case validate`, dump `build-issues.md` | `caseplan.json` passes full validation | On 3rd validate failure: `Retry with fix` / `Pause for manual edit` / `Abort` |
| **5 — Debug** | Optional CLI debug run (real execution — emails, API calls, etc.) | Debug output streamed | `Run debug session` / `Skip to Publish` |
| **6 — Publish** | Optional Studio Web upload | `DesignerUrl` printed | `Publish to Studio Web` / `Done` |

## Phase 2 — Prototyping

### Structural nodes (full detail)

- Solution + project scaffolding (`uip solution init`, `uip solution projects add`, plus JSON scaffolding from `plugins/case/impl-json.md`).
- Root case — `caseplan.json` with top-level fields + `metadata` block populated (name, `metadata.caseIdentifier`, empty `nodes[]`, empty `edges[]`).
- Global variables and arguments — variables block (`inputs`, `outputs`, `inputOutputs`) fully declared at top-level `variables`.
- Stages — all StageIds generated and captured.
- Edges — none authored (Rule 20); `schema.edges` stays `[]`. Stage transitions are condition-driven (written at Step 10, below).
- Triggers — fully built. Trigger output mappings written (they reference global variables, which already exist).
- Entry-points input/output — `entry-points.json` `input`/`output` schemas refreshed from the declared In/Out arguments (Step 6.3, per [entry-points-sync.md](entry-points-sync.md)). Makes the Phase-2 publish-for-review contract correct; idempotent.

### Conditions and SLA (full detail)

Authored in Phase 2 — every reference they need exists by the time it is needed: StageIds (Step 7), TaskIds (Step 9), variable IDs (Step 6.2), and SLA/escalation IDs (Step 9.9, immediately below).

- **SLA / escalation ID preallocation** (Step 9.9) — every `sla_` / `esc_` ID allocated into `id-map.json` so a `sla-status-change` condition can name the exact object Step 11 emits. Touches `id-map.json` only.
- **Conditions, all 4 scopes** (Step 10) — stage-entry, stage-exit, task-entry, case-exit. Written per the matching `plugins/conditions/<scope>/impl-json.md`.
- **SLA + escalation** (Step 11) — full `slaRules[]` per target (root or stage), reusing the Step 9.9 IDs.

**`wait-for-connector` rules are the one exception.** Their `uipath` block needs a `case spec --type trigger` round-trip, so Phase 2 writes the rule with the **stub `uipath`** — `serviceType` plus the two `"placeholder"` context entries (`connectorKey`, `operation`), empty `inputs` / `outputs` / `bindings` — per [connector-trigger-common.md § Placeholder fallback](connector-trigger-common.md#placeholder-fallback). The rule is present, positioned, and validates; Phase 3 Step 10.5 replaces the stub with the spec-minted block. This is the same stub shape an unresolved connector keeps permanently, so there is one code path, not two.

Consequences of writing rules before connector detail:

- **Expressions referencing a connector task's output** must use the in-expression marker `vars.$xref('Stage','Task','output')`, not a bare `=vars.<id>` — those output IDs are minted at Step 9.7. Step 11.5 resolves every marker after all outputs exist. This is already the required form inside any `=js:` sink ([bindings-and-expressions.md](bindings-and-expressions.md)); nothing new is needed for it.
- **Output-ID uniqueness ordering is unchanged.** Only `wait-for-connector` rules mint outputs, and those stay in Phase 3 Step 10.5 — after Step 9.7. The Check 8 dedup pool is still filled in the order triggers → non-connector tasks → connector tasks → rules.

### Tasks (shape depends on resolution state + task class)

| Task class | Resolved resources | Phase 2 shape |
|---|---|---|
| Non-connector (`process`, `agent`, `rpa`, `action`, `api-workflow`, `case-management`, `wait-for-timer`) | `task-type-id` resolved | Full `data.inputs[]` schema written (from `uip maestro case tasks describe`). Each input's `value` field is empty (`""`). Outputs and task-specific scalar fields (e.g. `action`'s `taskTitle`/`priority`/`recipient`/`labels`) populated per plugin — these are final at Step 2; only input `value`s defer to Phase 3. |
| Connector (`connector-activity`, `connector-trigger`) | `type-id` + `connection-id` resolved | `data.typeId` + `data.connectionId` set. `data.inputs` omitted or empty. **No `case spec` call for connector TASKS in Phase 2** — task schema discovery is deferred to Step 9.7. (`wait-for-connector` condition rules are also spec-free in Phase 2 — stubbed at Step 10, upgraded at Step 10.5.) |
| Any task | Unresolved (`<UNRESOLVED: …>` in `tasks.md`) | Placeholder task per Rule 8 of `SKILL.md` — empty `data: {}` (plus `data.taskTitle` / `data.priority` / `data.recipient` for `action`). Marker preserved. See [placeholder-tasks.md](placeholder-tasks.md). |
| `agent` / `api-workflow` built inline | Built + bound in Phase 1 at the Rule 17 gate | **Not a placeholder** — fully resolved task (name+folder binding, `resourceKey="solution_folder.<name>"`, **`folderPath` binding `default` = `""`** — co-located runtime folder; `solution_folder` stays only in `resourceKey`). Phase 2 treats it like any resolved resource. See [registry-discovery.md § Create-on-Missing](registry-discovery.md#create-on-missing-build-and-rediscovery). |

### What does NOT get written in Phase 2

- Task input `value` bindings (literals, expressions, cross-task references).
- Connector task input/output schemas.
- The real `uipath` block on a `wait-for-connector` condition rule — the rule itself IS written, carrying a stub `uipath`.
- Resolved `vars.$xref(...)` markers — written literally, resolved at Step 11.5.

### Phase 2 informational validate

End of Phase 2 mutations, run the gate validate. Resolve the profile per [case-commands.md § Phase 2 gate profile](case-commands.md#phase-2-gate-profile--probe-once-cache-fall-back-to-full-mode) — `--skeleton-v2` preferred, **full mode** as the fallback:

```bash
uip maestro case validate "<caseplan.json path>" --skeleton-v2 --output json
```

`--skeleton-v2` is specified to run structural checks (nodes, edges, identity, types) **plus** entry/exit rules, SLAs, and escalations — what Phase 2 now writes — while skipping task input `value` binding and connector task schemas. **It ships in no released CLI yet, so full mode is the live path today**; the probe exists so the gate adopts the narrower profile automatically once it lands.

On a CLI that rejects the flag, fall back once to **full mode** (no profile flag) — never to legacy `--skeleton`, which omits exactly the rules and SLA this gate exists to check. Full mode does not false-positive on Phase 2 state: a complete Phase-2 caseplan validates clean with unbound task inputs, connector tasks lacking `data.inputs`, and stub `wait-for-connector` rules. The fallback costs a little extra validation work and loses no coverage.

**Informational — do NOT halt on errors or warnings.** Capture error and warning counts (and optionally first few messages); include in hard-stop summary. Remaining errors are structural or rule-level (unreachable/orphan stage, missing trigger, duplicate names, a stage with no completing exit, a case with no completion rule) and meaningful — user inspects via the existing `Abort` option before continuing.

### Phase 2 hard stop

**Gated by the up-front build-review preference (SKILL.md Rule 11) — never a mid-build surprise.** The preference was captured at journey start: the final design confirmation on the interview journey, the single post-roadmap question on the provided-SDD journey. Always print the §Summary content below, then branch:

- **Straight-through** → continue directly into Phase 3 with no prompt; the summary doubles as the milestone narration line.
- **Pause-at-preview** → present the §Prompt below; only a user response transitions out of Phase 2.
- **No recorded preference** (resumed or legacy run): interactive → ask the §Prompt now; non-interactive → straight-through (no publish — Phase 6 remains the only, still-gated, publish point) and say so in one line.

The Phase 4 retry-cap, Phase 5 debug-consent, and Phase 6 publish stops below are independent of this preference and are never bypassed.

**Next-step rule.** Every user-visible stop or handoff after build progress must include a short `Suggested next steps` line before the prompt or final exit. Do this after straight-through completion reports, pause-at-preview summaries, published preview URLs, debug results, publish completion, and abort/done exits. Keep it concrete: inspect the preview, continue implementation, run debug, publish, fix listed placeholders/connections, or edit the named artifact and re-run.

#### Summary content

Print (before the prompt on the pause branch; as the continuation line otherwise):

1. Counts: stages / primary stages / secondary stages / triggers / tasks total / placeholder tasks / unresolved resources / condition rules / SLA rules / escalations / stub `wait-for-connector` rules awaiting Phase 3.
2. Validate result — use the exact line for the resolved profile from [case-commands.md § Phase 2 gate profile](case-commands.md#phase-2-gate-profile--probe-once-cache-fall-back-to-full-mode). Name the profile so the reader knows what was covered. Surfacing counts is enough; do not dump the full error list unless the user asks.
3. Paths: `caseplan.json`, `tasks.md`, `registry-resolved.json`.
4. Suggested next steps:
   - Straight-through: `Suggested next steps: I'll continue wiring the implementation now; say stop if you want to inspect the case shape first.`
   - Pause-at-preview: `Suggested next steps: publish the case shape for visual review, continue locally without preview, or abort and inspect the files.`

Do not enumerate every task. Studio Web visualization fills that role after publish.

#### Prompt (pause-at-preview branch only)

Use **AskUserQuestion** with three options:

- `Publish for review` — upload the case shape to Studio Web for visual review.
- `Skip publish and continue` — proceed directly to Phase 3.
- `Abort` — stop the skill; leave artifacts in place.

#### On `Publish for review`

1. Run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json` then `uip solution upload "<SolutionDir>" --output json`. Capture full upload response.
2. Parse `DesignerUrl` from response.
3. **MUST emit DesignerUrl as plain-text output to user BEFORE invoking AskUserQuestion**, on its own line:
   `Case shape published. Review at: <DesignerUrl>`

   When the count of stub `wait-for-connector` rules is non-zero, print one further line of its own — do NOT append to the URL line, which would break auto-linking:

   `Connector-bound rules show as unresolved in this preview; they are wired in the next step.`

   Studio Web flags the unresolved connector, so a reviewer who is not told will read it as a defect.

   Never bundle URL only into question body — some renderers display question before surrounding prose, leaving user without URL until after they answer.
4. Print `Suggested next steps: inspect the case shape in Studio Web, then continue implementation here or abort and keep the artifacts for manual review.`
5. Only after URL line and suggested next steps are emitted, invoke **AskUserQuestion** (second prompt): `Continue to implementation` / `Abort`.

If `DesignerUrl` missing from response, dump full upload response to `tasks/upload-response.json`, print path, continue to prompt — user can recover URL from file.

Do not warn user about Studio Web edits being overwritten. Phase 6's re-publish (when chosen) overwrites volatile review-time edits with final local state. User can compare Studio Web state before and after Phase 3 to spot edits they want to preserve.

#### On `Skip publish and continue`

Proceed directly to Phase 3.

#### On `Abort`

1. Dump in-memory issue list to `tasks/build-issues.md` per [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md).
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
   - Trigger ID (from `schema.nodes[]` where `type === "case-management:Trigger"`).
   - Task name → TaskId per stage (from `schema.nodes[<stage>].data.tasks[][]`).
   - Variable name → `var` ID (from top-level `variables.{inputs,outputs,inputOutputs}`).
   - Stub `wait-for-connector` rule → `(scope, stageId, taskId?, ruleId)` — every rule whose `uipath.context` still holds the two `"placeholder"` entries. `taskId` is needed for a task-entry rule (a stage holds many tasks); note `elementId` still uses `stageId` even there. A head start for Step 10.5, which re-scans and owns the skip decision. Scan all four scopes: `nodes[stage].data.entryConditions`, `nodes[stage].data.exitConditions`, task `data.entryConditions`, and `metadata.caseExitRules`.
3. Optionally cross-check against `id-map.json` if JSON-strategy plugins wrote one. `caseplan.json` is source of truth; `id-map.json` is speed-up.

Never trust in-memory maps from Phase 2 without re-reading `caseplan.json` — context may be compacted across hard stop.

> **Phase 2 wrote conditions and SLA — do not rebuild them.** `caseplan.json` at Phase 3 entry already carries every condition rule and `slaRules[]` entry. Phase 3 touches them in exactly two places: Step 10.5 replaces a stub `rule.uipath` in place, and Step 11.5 substitutes `$xref` markers in place. Any Phase 3 write that replaces a whole `entryConditions` / `exitConditions` / `caseExitRules` / `slaRules` array is a defect — it re-derives from `tasks.md` state the build already committed and risks dropping Phase 2 repairs. The repair-preservation contract in [case-editing-operations.md § Per-section batch write contract](case-editing-operations.md#per-section-batch-write-contract--canonical) applies.

### Phase 3 — Execution order

After re-entry:

1. **Connector task detail (Step 9.7)** — for each connector task in `tasks.md`, run plugin's `impl-json.md` detail steps: `case spec --type {activity,trigger} --input-details`, then mint `data.context[]` / `data.inputs[]` / `data.outputs[]` from the populated `caseShape` (placeholder substitution + var/id minting).
2. **Task I/O value binding (all task classes) (Step 9.8)** — per [`plugins/variables/io-binding/impl-json.md`](plugins/variables/io-binding/impl-json.md). Applies to both non-connector and connector tasks. For each task's inputs in `tasks.md` order, write literal, expression, or cross-task reference (resolved to `=vars.<outputReferenceId>` through the common `.id`-based resolver) into `task.data.inputs[i].value`. Connector tasks have `data.inputs[]` schema written in step 1; value binding happens here in step 2, same as non-connector tasks.
3. **Connector-bound condition rule upgrade (Step 10.5)** — for each `wait-for-connector` rule that Phase 2 Step 10 wrote with a stub `uipath`, run `case spec --type trigger --input-details`, replace the stub with the spec-minted block, append the root Connection + FolderKey bindings, and run the rule-scope `bindings_v2` sync. The rule's `id`, `conditionExpression`, scope, and position are already correct from Step 10 — **only `rule.uipath` changes; never rewrite the surrounding conditions array.** Rules whose connector is genuinely `<UNRESOLVED>` keep the stub permanently. Runs after Step 9.7 so rule outputs dedup against connector task outputs already in the pool.
4. **In-expression marker resolution (Step 11.5)** — per [`plugins/variables/io-binding/impl-json.md § In-Expression Marker Resolution`](plugins/variables/io-binding/impl-json.md). After all outputs are minted/deduped, resolve every `vars.$xref('Stage','Task','output')` marker in `caseplan.json` to bare `vars.<outputReferenceId>` through the same resolver in one sink-blind whole-file pass (input payloads, conditions, SLA, connector bodies). Conditions and SLA were authored in Phase 2 with their markers left literal — this pass is where they resolve. Unresolved triple or reference ID → ERROR.
5. **End-of-Phase-3 validator pass** — per [`implementation.md § Step 12`](implementation.md). Run Checks 1-11 (=vars.X resolution, Out-arg producer presence, type mismatch, surviving `$xref` markers, resolved-resource I/O completeness, entry-point schema parity, bindings sidecar parity, output-ID uniqueness, resolved-resource emission and repair preservation, formal-arg slot ID format, resourceKey self-consistency). AskUserQuestion for unresolved references (incl. `$xref` markers), pure orphan Out-args, and unbound required inputs / phantom output fields; option (c)/(d) "continue with best-effort emit" preserves forward progress. Checks 6-11 are non-interactive: on mismatch auto re-run/regenerate/re-mint once where the check permits it; Check 6 logs if still divergent, while Checks 7, 9, 10, and 11 halt before Phase 4 if still divergent. Never HALT otherwise.

Phase 3 produces a `caseplan.json` that should pass authoritative validation. No hard stop (no AskUserQuestion gate) on Phase 3 exit — agent proceeds directly to Phase 4. Sole blockers: Check 7 parity still divergent after regeneration, any Check 9 resolved-resource emission/preservation failure, any Check 10 formal-arg slot id still malformed after the repair pass, or any Check 11 resourceKey still self-inconsistent after the repair pass (halt per [`implementation.md § Step 12`](implementation.md)).

## Phase 4 — Validate

End of detail mutations. Run full-mode validate (omit every skeleton flag — `--skeleton-v2` and `--skeleton` both narrow the profile; full is the default):

```bash
uip maestro case validate "<caseplan.json path>" --output json
```

On success: `{ Result: "Success", Code: "CaseValidate", Data: { File, Status: "Valid" } }` — proceed to Phase 4 dump step.

On failure: output lists `[error]` and `[warning]` entries with path and message. Fix reported issues (usually via targeted re-run of earlier step) and re-run `validate`.

### Retry policy

Up to **3 validation retries** per session. After 3rd failure, halt and ask user with **AskUserQuestion**: show remaining errors and options:

- `Retry with fix` — agent attempts fix, re-runs validate (counter does not reset).
- `Pause for manual edit` — exit skill mid-flight; user edits `caseplan.json` directly and re-runs skill.
- `Abort` — exit; dump `build-issues.md`; leave artifacts in place.

### Dump issue log

After successful validate, write issue list to `tasks/build-issues.md` per [`plugins/logging/impl-json.md`](plugins/logging/impl-json.md), grouped by plugin with summary index. Source of truth for completion report. Write even if zero issues logged (confirms clean build).

On Phase 4 success → proceed to Phase 5.

## Phase 5 — Debug

After Phase 4 success, report results then ask user via **AskUserQuestion**:

- `Run debug session` — run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json` then `uip maestro case debug "<directory>/<solutionName>/<projectName>" --log-level debug --output json`. Streams results.
- `Skip to Publish` — proceed to Phase 6 without debugging.

> **Debug executes case for real — sends emails, posts messages, calls APIs, writes to databases. Only run when user explicitly asks. Never auto-run** (Rule 12).

Requires `uip login`. Uploads to Studio Web, runs in Orchestrator, streams results.

After debug completes, return to Phase 5 prompt so user can re-run or move on. Proceed to Phase 6 only on `Skip to Publish`.

### Report fields (printed before prompt)

1. File path of `caseplan.json`.
2. What was built — summary of stages, tasks, conditions, SLA.
3. Validation status — `validate` pass / remaining warnings.
4. Placeholder tasks + unresolved resources — list every placeholder (TaskId, type, display-name, stage) + external resource user must register (task-type-id / connection-id) + wiring-notes from `tasks.md`. Also list **agents / API workflows built inline** (built as in-solution siblings, already bound) and any **built but unreferenced** (reject case) separately — they need no user action. See [placeholder-tasks.md § Completion-Report Shape](placeholder-tasks.md#completion-report-shape).
5. Missing connections — connector tasks needing IS connections that don't exist yet.
6. Suggested next steps — one short line before the prompt, e.g. `Suggested next steps: run a debug session if you are ready to exercise the case, or skip to publish if validation is enough for now.` If placeholders or missing connections exist, mention fixing/registering those before publish.

### Debug notes

- `uip solution resources refresh` MUST run before debug — syncs resources from `bindings_v2.json` so Studio Web can resolve connector dependencies (Rule 14).
- Debug verifies the build actually runs end-to-end before the user commits to a publish. If debug surfaces a fixable issue, see [Step 13a — Troubleshoot failed case](implementation.md#step-13a--troubleshoot-failed-case) and re-run.
- **Inline-built api-workflow siblings are NOT provisioned by `case debug`** — that task faults with incident `170007` ("job's associated process could not be found") by design; agent siblings do resolve in debug. Verifying that task's runtime needs a full solution deploy (`uip solution pack` → `uip solution publish` → `uip solution deploy run`) — an Orchestrator install, so **offer it via AskUserQuestion, never run it unprompted** (options — `Run full solution deploy` / `Skip (mark debug-unverifiable)`; the Phase 6 no-deploy default applies); if declined, report the task as debug-unverifiable and continue. See [api-workflow/planning.md § Creating an API workflow inline](plugins/tasks/api-workflow/planning.md#creating-an-api-workflow-inline).

## Phase 6 — Publish

After Phase 5 (whether debugged or skipped), prompt via **AskUserQuestion**:

- `Publish to Studio Web` — run `uip solution resources refresh --solution-folder "<SolutionDir>" --output json` then `uip solution upload "<SolutionDir>" --output json`. Print returned `DesignerUrl` on its own line. Exit skill.
- `Done` — exit skill without publishing.

Before this prompt, include `Suggested next steps: publish to Studio Web when you want a designer-visible version, or stop here and use the local artifacts for review/editing.` After a successful publish, print `Suggested next steps: open the Designer URL, verify resources and connections, then run any tenant-side smoke checks you need.` On `Done`, print `Suggested next steps: review caseplan.json/tasks.md locally or update sdd.md and re-run when you want changes.`

### Publish notes

- `uip solution upload` accepts solution directory (folder containing `.uipx`) directly — no intermediate bundling step.
- `uip solution resources refresh` MUST run before upload — syncs resources from `bindings_v2.json` so Studio Web can resolve connector dependencies (Rule 14).
- Do **NOT** run `uip maestro case pack` + `uip solution publish` unless user explicitly asks for Orchestrator deployment. That path puts case directly into Orchestrator, bypassing Studio Web. Default is always Studio Web.

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

1. Dump `build-issues.md`.
2. Print paths.
3. Exit.

No artifact deletion. No rollback. User owns partial state.

## Out of scope

- **Re-ingesting Studio Web edits.** If user edits published placeholder in Studio Web during review, edits are not round-tripped back into local `caseplan.json`. Phase 3 writes on top of local state; Phase 6 re-publish overwrites Studio Web with completed local build.
- **Resuming aborted session.** Re-running skill regenerates `tasks.md` from scratch (Rule 6) and re-executes Phase 2 onwards.

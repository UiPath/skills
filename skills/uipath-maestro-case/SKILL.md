---
name: uipath-maestro-case
description: "Always invoke for `caseplan.json` files. UiPath Case Management authoring (caseplan.json) from sdd.md, or via interview if sdd.md absent. Produces tasks.md plan, writes caseplan.json via per-plugin JSON recipes. Edits an existing caseplan.json via targeted operations (skips planning). For .xaml→uipath-rpa, .flow→uipath-maestro-flow, .bpmn→uipath-maestro-bpmn. For PDD→SDD or complex/multi-product→uipath-planner."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion, TodoWrite, Agent
---

# UiPath Case Management Authoring Assistant

Builds UiPath Case Management definitions from `sdd.md`. Generates `tasks.md` plan, then writes `caseplan.json` directly via per-plugin JSON recipes. CLI is reserved for read-only metadata fetches (registry, validate, debug, tasks describe, case spec) and solution boundary operations (`uip solution init` / `project add` / `upload`).

When `sdd.md` is absent, **Phase 0 interview** generates one interactively (listen → sketch → progressive ask-walk → resolve → approve, with optional HTML preview before handing off). Complex / multi-product cases may still be designed with the same workflow; use `uipath-planner` when the user explicitly requests planning across products.

**Scope:** two journeys — **greenfield** (build a new case from `sdd.md`, user-provided or Phase 0-generated) and **brownfield** (targeted edits to an existing `caseplan.json` — see [references/brownfield.md](references/brownfield.md)). Editing a case that also lives in Studio Web? Brownfield pulls the current server state first (`uip solution download` / `solution project resync`) so re-publish can't silently clobber server-side changes — see [brownfield.md § Pull latest first](references/brownfield.md#pull-latest-first-before-editing).

## When to Use This Skill

- User provides `sdd.md` and wants Case Management project built
- User asks to create new case management project but has no `sdd.md` (Phase 0 interview generates one)
- User asks to create new case management project or definition
- User asks to generate implementation tasks from `sdd.md` or convert spec to plan
- User asks to edit, modify, or update an existing `caseplan.json` (add/remove a stage or task, change a condition, swap a trigger) — targeted edits skip planning; see [references/brownfield.md](references/brownfield.md)
- User asks about case management JSON schema — nodes, transitions, tasks, rules, SLA
- User wants to manage runtime case instances (list, pause, resume, cancel) — see [references/case-commands.md](references/case-commands.md)

**Do not use for:** `.xaml` → `uipath-rpa`. `.flow` → `uipath-maestro-flow`. Standalone agents/APIs/processes outside case context → corresponding UiPath skill.

## Critical Rules

1. **Phase 0 interview when `sdd.md` absent.** Generate `sdd.md` via a guided interview (listen → sketch → progressive ask-walk → resolve → approve); output requires explicit user approval (Approve hard-stop) before treating as Rule 2 input. Never overwrite an existing `sdd.md`.
2. **sdd.md is sole input post-Phase-0.** After Phase 0 approval (or when user-provided), trust as written. Skill does not validate or gap-fill. If ambiguous, use AskUserQuestion — never infer silently.
3. **PHASE 1 HARD GATE — refresh registry before planning.** Run `uip login status --output json`, then `uip maestro case registry pull`, before cache inspection, carryover reuse, resource resolution, or any Phase 1 artifact write. Trust the SDD as written; the pull refreshes the local discovery cache and does not validate or override the SDD. **Cache-state rule:** before a successful pull, a missing cache directory/file is a failed refresh precondition — never a zero-match result. Only after a successful pull may an empty exact-name match set (or a still-absent type index) enter the normal empty-lookup flow. Login/pull failure → surface it and stop Phase 1. Discovery reads `~/.uip/case-resources/<type>-index.json` directly because `registry search` has known gaps (esp. action-apps). See [references/registry-discovery.md](references/registry-discovery.md).
4. **`--output json` on every parsed read.**
5. **Follow plugin per node type.** Open matching `planning.md` during planning + `impl-json.md` during execution. Never guess JSON shapes from memory.
6. **`tasks.md` declarative and lossless only.** No shell commands inside. Field names use plain identifiers (e.g., `type:`, `displayName:`, `lane:`), not CLI flag syntax. One T-entry per sdd.md declaration — every stage, task, trigger, condition, SLA rule, **variable, and argument** gets own T-number, even when value looks like default (`current-stage-entered`, `case-entered`, `exit-only`, `is-interrupting: false`, `runOnlyOnce: true`, `marks-stage-complete: true`). Never group, never silently omit. Preserve every SDD Inputs row with its declared binding mode and value. A JSON object literal stays literal through both handoffs: record the exact JSON in `tasks.md`, then write either the native object or its JSON-encoded string to `input.value`; never add `=js:` or `=jsonString:` unless the SDD itself explicitly uses that prefix. Project every task/rule Outputs table row through the common grammar in [`plugins/variables/io-binding/planning.md`](references/plugins/variables/io-binding/planning.md#sdd-table-to-tasksmd-projection-mandatory), then preserve each resulting `outputs:` item **with its operator and both operands unchanged**. SDD Outputs rows require `->` or `=`; a bare `tasks.md` output is generated only from resolved-schema discovery and is never authored as an SDD row. SDD table placeholders such as a `—` Field are not operands and never appear in `tasks.md`. In particular, `greeting -> greeting` is NOT equivalent to schema-discovered bare `greeting`: the former extracts into the predeclared case variable and requires `originalVar`; the latter auto-mints a task-local output. Never simplify an equal-name `->` row. **When an sdd.md row's format is unrecognized, ambiguous, or cannot be categorized — invoke AskUserQuestion before skipping. Silent omission is forbidden.** Always regenerate from scratch (greenfield/planning only — brownfield targeted edits mutate in place and preserve IDs; see [references/brownfield.md](references/brownfield.md)). See [`references/planning.md` §4.0](references/planning.md).
7. **`tasks.md` gate — auto-approved by default, opt-in stop.** Phase 1 auto-proceeds into Phase 2 Prototyping with no AskUserQuestion sign-off; treat the plan as approved. **Stop after `tasks.md` only when the request explicitly asked for a plan-only / review-first run** (e.g. "just the plan", "Phase 1 only", "stop after tasks.md for review", "don't build the case yet") — then report the plan and do NOT proceed to Phase 2. Re-read `tasks.md` before executing.
8. **Unresolved resource → placeholder, never fabricate IDs.** Keep `<UNRESOLVED: ...>` markers in `tasks.md`. Placeholder **task**: node with `type` + `displayName` + structural fields, `data: {}`; conditions still reference the TaskId. Placeholder **event trigger**: node with render fields + `data.uipath: { serviceType: "Intsvc.EventTrigger" }` only (no other `data.uipath` keys); `entry-points.json` entry appended. No trigger-edge is created (Rule 20). See [references/placeholder-tasks.md](references/placeholder-tasks.md) and [references/plugins/triggers/event/impl-json.md § Placeholder fallback](references/plugins/triggers/event/impl-json.md).
9. **Persist every registry resolution to `registry-resolved.json`** — one object per task with exact keys `stage`, `task`, `taskType`, `cacheFile`, `searchQuery`, `matches`, `selected`, and `rationale` (plus resolved I/O/review metadata when applicable). `stage` + `task` associate the audit entry to one SDD declaration; `cacheFile` is the basename actually searched; `matches` is the full exact-name match set from the cache refreshed in Rule 3, not a summary. Use the authoritative SDD fields as the search and selection contract; record `selected` from that match set, or `null` after a genuine empty lookup.
10. **Cross-task refs:** plan as `"Stage Name"."Task Name".output_name`. Resolve both whole-value `<-` and in-expression `$xref` through the common output-reference-ID algorithm in [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md#output-reference-id-authoritative): use the source output's `.id`; only a custom `=` output, which intentionally has no `.id`, resolves through its verified root companion's `.id`. Never use a reassigned output's `.var` as the source reference ID — it points at the target Case variable and can differ from the collision-safe source `.id`. Discover output names via `uip maestro case spec` (connector tasks) or `uip maestro case tasks describe` (non-connector tasks) — never fabricate. **Inside** a larger `=js:` expression (composite payload, condition, SLA), use the in-expression marker `vars.$xref('Stage','Task','output')` instead — resolved at Step 11.5. See [references/bindings-and-expressions.md](references/bindings-and-expressions.md) and [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md).
11. **HARD STOP between Phase 2 (Prototyping) and Phase 3 (Implementation) — unconditional, every run.** Run `validate --skeleton` (structural checks only — skips tasks/SLAs/escalations/entry-exit rules), surface counts, present AskUserQuestion: `Publish for review` / `Skip publish and continue` / `Abort`. Do NOT halt on Phase 2 validate errors — advisory only; user inspects via `Abort`. Never skip prompt for auto mode, non-interactive mode, prior approval. If harness forbids prompts, halt with error. **On `Publish for review`: print `DesignerUrl` as plain-text output BEFORE invoking the second AskUserQuestion — never embed URL only inside question body.** Additional hard stops gate Phase 4 retry exhaustion (`Retry with fix` / `Pause for manual edit` / `Abort`), Phase 5 entry (`Run debug session` / `Skip to Publish`), and Phase 6 entry (`Publish to Studio Web` / `Done`). Full contract in [`references/phased-execution.md`](references/phased-execution.md).
12. **Never run `uip maestro case debug` automatically.** Executes case for real — emails, messages, API calls. Explicit user consent only.
13. **All skill artifacts: Read + Write/Edit only.** Applies to `caseplan.json`, `sdd.md`, `sdd.draft.md`, `tasks.md`, `tasks/registry-resolved.json`, `tasks/trigger-spec-cache.json`, `tasks/spec-cache.<elementId>.json`, `bindings_v2.json`, `id-map.json`, `entry-points.json`, `build-issues.md`. No `python`, `node`, `jq`, `sed`, `awk`, or scripts that open/parse/modify/save these files. **Specifically forbidden** (common slip): `node -e "...fs.writeFileSync..."`, `node -e "...fs.readFileSync..."`, `node -e "..." > <artifact>`, `jq '...' <artifact> > <artifact>`, `python -c "...open(...,'w')..."`, `sed -i`, `awk -i inplace`, or any shell redirection (`>`, `>>`, `| tee`) onto a skill artifact regardless of interpreter. **Writing a helper script under `/tmp` or anywhere else to assemble a skill artifact is also forbidden** — the build-assembler pattern (`/tmp/build-caseplan.js`, `/tmp/gen-tasks.py`, etc.) is the same Rule 13 violation as inline `node -e`, regardless of "mechanical copy" or "avoid Read+Write churn" framing. If `caseplan.json` exceeds ~30KB and a single Write feels too large, split into the Phase-2-skeleton-then-Phase-3-fill cadence (per [case-editing-operations.md § Per-section batch write contract](references/case-editing-operations.md#per-section-batch-write-contract--canonical)) — never via helper script. **The `node -e ... fs.*` ban is not scoped to the artifact list — it applies to ALL file reads in this skill, including resource cache reads from `~/.uip/case-resources/`. Use `cat ... | python3 -c "..."` or the `Read` tool for cache lookups.** Bash subprocesses OK ONLY for UUID v4 generation (`node -e "console.log(crypto.randomUUID())"` for `operate.json.projectId` and `entry-points.json` `uniqueId` — subprocess MUST NOT `require('fs')` or use redirection), CLI metadata fetches, validate, debug, and solution scaffold/upload. **Prefixed IDs (`Stage_`, `t`, `Rule_`, etc.) are picked inline by the agent — no subprocess.** See [references/case-editing-operations.md § Tool usage](references/case-editing-operations.md#tool-usage--mandatory).
14. **Bindings sidecar parity is an unconditional Phase 3 exit check.** Before Phase 4, run Step 12 Check 7 even when publish, debug, and `uip solution resources refresh` are skipped. Compare `bindings_v2.json.resources[]` with the complete projection of top-level `caseplan.json.bindings[]`; on mismatch, regenerate once and re-check, then halt if it still differs. Repeat Check 7 before every `resources refresh`. Always run `resources refresh` before `uip solution upload` or `uip maestro case debug` so Studio Web can resolve dependencies.
15. **Never auto-invoke `uipath-planner`.** If the user asks for planning across products, print a plain-text suggestion of the skill name; the user re-invokes it manually. No tool-call cross-skill handoff.
16. **Caseplan task `type` enum is closed — 9 values, schema-kebab.** Any task node written into `caseplan.json` MUST have `type` exactly one of: `process` | `agent` | `rpa` | `action` | `api-workflow` | `case-management` | `execute-connector-activity` | `wait-for-connector` | `wait-for-timer`. **Never** write the plugin folder name (`connector-activity`, `connector-trigger`) or the CLI `--type` flag value into the JSON node — those name the planning artifacts, not the schema. Never write `external-agent`, `external-workflow`, `document-extraction`, `flow-process`, `wait-for-event`, or any hallucinated value — there is no plugin to back them. `external-agent`, `external-workflow`, `document-extraction`, and `flow-process` are **not supported yet**. See [references/case-schema.md § Task type](references/case-schema.md) and the Plugin Index naming-asymmetry table below.
17. **Empty registry lookup → AskUserQuestion BEFORE any placeholder fallback.** When a planning-phase lookup returns 0 matches, present AskUserQuestion per lookup-batch (one prompt, not per-task) BEFORE any placeholder T-entry or per-plugin Unresolved Fallback, with options: (a) `Force pull and re-resolve` — loops back for still-empty; (b) `Use placeholders for all`; (c) `Create missing resources inline` — shown ONLY when ≥1 still-empty is creatable (an `agent` or an `api-workflow`) AND the CLI supports `registry --local`. **Create covers agents and API workflows only, gate-selected only** (never from SDD content alone; agent → `uipath-agents`, api-workflow → `uipath-api-workflow`); unselected + non-creatable empties (regular RPA process, action, case-management, connectors, agentic processes) → placeholder; the option is suppressed when `--local` is absent. Do NOT pre-judge via resource-name heuristics — the user's call. The gate and Select **group empties by `(name, type)`** (one row per resource, usages listed — non-creatable ones show only at the gate, annotated `placeholder only`); create-selected resources merge or split at [registry-discovery § 1c](references/registry-discovery.md#1c--dedup-the-selected-builds-one-resource-per-name-and-type) by I/O (identical-I/O usages → one build; differing → later renamed, anchor keeps the name; the SDD cell is updated only with user permission — never non-interactively). Placeholder fallback is valid only after `Use placeholders for all`. Build/register/verify mechanics live in [references/registry-discovery.md § Create-on-Missing](references/registry-discovery.md#create-on-missing-build-and-rediscovery) (gate detail: [§ MUST Confirm](references/registry-discovery.md#must-confirm-before-placeholder-fallback)).
18. **Layout state lives in top-level `layout`, not on the node/edge.** Do NOT emit node-level `position`, `style`, `measured`, `width`, `height`, `zIndex`. Do NOT compute stage `position.x = 100 + count * 500`. Do NOT emit edge `data.waypoints`. Emit top-level `layout: {}` (empty object) — FE auto-layouts on canvas load. The frontend's `transformCaseInMemoryJsonToDiskJson` strips these fields anyway when round-tripping through canvas; emitting them is harmless on read but wastes tokens. See [`references/case-editing-operations.md`](references/case-editing-operations.md).
19. **Generated output IDs use one global namespace.** Run [Step 12 Check 8](references/implementation.md#step-12--end-of-phase-3-validator-pass) once at Phase 3 exit; it is the mandatory uniqueness check. Do not enter Phase 4 until it passes, and do not substitute `uip maestro case validate` for it.
20. **Edges retired — `schema.edges` stays `[]`.** Never author a `TriggerEdge`/`Edge` object, for any node. Stage-to-stage flow is condition-driven (target stage's `entryConditions`, plus source `exitConditions` when it diverges); case start is the first stage's `case-entered` entry condition, not a Trigger→stage edge. FE auto-derives canvas connectors from conditions. Edge shapes exist only as a read-only appendix in [references/case-schema.md § Appendix](references/case-schema.md#appendix--edge-shapes-read-only--never-author) for reading canvas-round-tripped files.

## Routing — greenfield vs brownfield

| Condition | Journey |
|---|---|
| New case, or `sdd.md` provided, or no `caseplan.json` yet, or user asks to (re)build from a spec | **Greenfield** — Phase 0→6 below |
| `caseplan.json` exists AND intent is a targeted edit ("add a stage", "remove task X", "change a condition", "swap the trigger") | **Brownfield** — skip Phase 0→6, go to [references/brownfield.md](references/brownfield.md) |

Brownfield bypasses planning, prototyping, and their hard stops; it still honors the debug-consent gate (Rule 12) and reuses the Phase 5 / Phase 6 contracts.

## Workflow

Up to seven hard stops (Phase 0 + Phase 1 review-on-request + Phase 2 second prompt + Phase 4 conditional): **Phase 0** (interview → sdd.md, only when sdd.md absent) → approve → **Phase 1 Planning** (sdd.md → tasks.md) → auto-proceed (stop for review only when the request asks) → **Phase 2 Prototyping** (placeholder) → publish-for-review stop → continue-after-publish stop (publish branch only) → **Phase 3 Implementation** (detail) → **Phase 4 Validate** (retry-cap stop on 3rd failure) → **Phase 5 Debug** (Run vs Skip-to-Publish stop) → **Phase 6 Publish** (Publish vs Done stop).

### Kickoff — set dev expectations first

Before any planning or build work, present the flow once so the dev knows the steps and where they'll be asked to decide. Emit the matching block below verbatim in tone (adjust wording to fit context; keep the checkpoint markers). Present ONCE per run — at Phase 0 start if the interview runs, else at Phase 1 start. Allow-listed standalone text block (Anti-patterns token cap); do not repeat it at later phases.

**Greenfield** (building a new case):

> Here's how I'll build this case, and where I'll stop for your call:
> - **Planning** — I draft a task plan from the spec. **You approve it** before I build anything.
> - **Prototyping** — I build the case skeleton (stages, tasks, triggers — no wiring yet). **You choose:** publish it to Studio Web for a visual review, or continue.
> - **Implementation** — I wire task inputs/outputs, conditions, and SLAs.
> - **Validate** — I run validation and fix errors.
> - **Debug** (optional) — **you choose** whether to run the case for real (live emails / API calls).
> - **Publish** (optional) — **you choose** whether to upload to Studio Web.

When Phase 0 runs, prefix one line: "First I'll interview you to produce the spec (`sdd.md`), which you approve before planning."

**Brownfield** (editing an existing case): present the short version at entry — see [references/brownfield.md](references/brownfield.md).

### Phase 0 — Interview (conditional)

Triggered when `sdd.md` absent at resolved path. Read [references/phase-0-interview.md](references/phase-0-interview.md) for the interview modes (listen → sketch → progressive ask-walk → resolve → approve), resumption, and HTML preview offer. Produces:

> **Read budget for Phase 0.** Read `phase-0-interview.md`, `references/sdd-generation-rules.md` (the mental model + task-type reasoning the progressive walk relies on), and `assets/templates/sdd-template.md` to begin the interview. Do NOT preload plugin `impl-json.md` files — those are needed only in Phase 2/3 and pulled in just-in-time per T-entry.

- `sdd.md` — generated against `assets/templates/sdd-template.md`
- `tasks/registry-resolved.json` — per-task registry resolutions
- `sdd.draft.md` — intermediate, deleted at approval
- `sdd-viewer.html` — optional, rendered from `assets/templates/sdd-viewer.html` when user accepts the preview offer; Phase 1 ignores it

If `sdd.md` already exists: skip Phase 0, hand to Phase 1 unchanged.

### Phase 1 — Planning

Read [references/planning.md](references/planning.md). Produces:

- `tasks/tasks.md` — T-numbered entries (stages → tasks → conditions → SLA)
- `tasks/registry-resolved.json` — audit trail
- When the user picks **Create** at the Rule 17 gate, Phase 1 also builds the selected agent(s) / API workflow(s) as in-solution siblings (one sub-agent per resource — `uipath-agents` for agents, `uipath-api-workflow` for API workflows), registers them (`uip solution project add` + `resources refresh`), and binds them as resolved tasks. Registration and `--local` rediscovery need an enclosing solution `.uipx`, so the Create flow **first ensures the solution exists** (`uip solution init` if absent — Phase 2 Step 6.0 then skips its own `init`). See [references/registry-discovery.md § Create-on-Missing](references/registry-discovery.md#create-on-missing-build-and-rediscovery).

> **`tasks/` is created at the working root, adjacent to `sdd.md` — NEVER inside the solution/project folder (`<Solution>/`).** This holds regardless of where the case file lives: `caseplan.json` sits at `<Solution>/<Project>/caseplan.json`, but the planning artifacts (`tasks.md`, `registry-resolved.json`) stay next to `sdd.md` at the root.

Auto-proceed to Phase 2 (re-read `tasks.md` first) — plan treated as approved. Stop after `tasks.md` only if the request explicitly asked for a plan-only / review-first run (Rule 7).

### Phase 2 — Prototyping

Read [references/implementation.md](references/implementation.md) + [references/phased-execution.md](references/phased-execution.md). Builds structural shape only:

1. Solution + project + root case (Step 6)
2. Triggers — manual / timer / event, including placeholder event triggers per Rule 8 (Step 6.1)
3. Global variables + arguments (Step 6.2) — including In arguments whose `elementId` references the `TriggerId` (captured in Step 6.1) of the trigger named by the row's `sourceTriggers`, or the primary trigger when blank
4. Refresh entry-points.json input/output from the declared In/Out args (Step 6.3) — per [`references/entry-points-sync.md`](references/entry-points-sync.md)
5. Stages (Step 7)
6. Tasks — shape only (Step 9): non-connector with full `data.inputs[]` schema + empty values; connector with `typeId` + `connectionId` only (no `case spec`); unresolved as placeholders per Rule 8
7. Informational validate (Step 9.5.1) — do NOT halt on errors/warnings
8. **HARD STOP** (Step 9.5.2–9.5.5): `Publish for review` / `Skip publish and continue` / `Abort`. On `Publish`: `uip solution resources refresh --solution-folder <SolutionDir> --output json` then `uip solution upload`, print DesignerUrl, AskUserQuestion: `Continue to implementation` / `Abort`. On `Abort`: dump `build-issues.md`, exit (no cleanup).

### Phase 3 — Implementation

Re-read `tasks.md` AND `caseplan.json` (Step 9.6). Then:

1. Connector schema + defaults (Step 9.7) — `is resources/triggers describe`
2. I/O binding all task classes (Step 9.8) — per [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md)
3. Conditions all 4 scopes (Step 10)
4. SLA + escalation (Step 11)
5. In-expression `vars.$xref` marker resolution (Step 11.5) — per [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md)

No hard stop on Phase 3 exit — proceed directly to Phase 4.

### Phase 4 — Validate

1. Run Step 12 once at the Phase 3 → Phase 4 boundary. It performs Checks 1–8, including bindings sidecar parity (Check 7) and global output-ID uniqueness (Check 8).
2. After all Step 12 checks pass, run full `uip maestro case validate`. Retry up to 3×; on 3rd failure **HARD STOP** AskUserQuestion: `Retry with fix` / `Pause for manual edit` / `Abort`
3. Dump `build-issues.md` (Step 12.1)

### Phase 5 — Debug

Completion report + **HARD STOP** AskUserQuestion (Step 13): `Run debug session` / `Skip to Publish`. On `Run`: `uip solution resources refresh` then `uip maestro case debug` (never auto-run — Rule 12). Loop on completion until `Skip to Publish`.

### Phase 6 — Publish

**HARD STOP** AskUserQuestion (Step 14): `Publish to Studio Web` / `Done`. On `Publish`: `uip solution resources refresh` then `uip solution upload`, print DesignerUrl (Step 15). Exit on either choice.

## Reference Navigation

| I need to... | Read |
|---|---|
| Generate sdd.md interactively when none provided | [references/phase-0-interview.md](references/phase-0-interview.md) |
| Plan tasks from sdd.md | [references/planning.md](references/planning.md) |
| Execute tasks.md into a case | [references/implementation.md](references/implementation.md) |
| Edit an existing caseplan.json (targeted edits) | [references/brownfield.md](references/brownfield.md) |
| Phase 2 → 3 → 4 → 5 → 6 split + hard stop contracts | [references/phased-execution.md](references/phased-execution.md) |
| Cross-cutting edit mechanics (IDs, anchoring, batch contract) | [references/case-editing-operations.md](references/case-editing-operations.md) |
| Case JSON schema | [references/case-schema.md](references/case-schema.md) |
| Surviving CLI commands (registry, validate, debug, runtime) | [references/case-commands.md](references/case-commands.md) |
| Troubleshoot a failed case | [references/troubleshooting-guide.md](references/troubleshooting-guide.md) |
| Resolve task types from registry | [references/registry-discovery.md](references/registry-discovery.md) |
| Wire inputs/outputs + cross-task refs + expression prefixes | [references/bindings-and-expressions.md](references/bindings-and-expressions.md) |
| Configure connector activity / trigger / event | [references/connector-integration.md](references/connector-integration.md) |
| Construct `case spec --input-details` JSON | [references/case-spec-input-details.md](references/case-spec-input-details.md) |
| Placeholder tasks for unresolved resources | [references/placeholder-tasks.md](references/placeholder-tasks.md) |
| Sync bindings_v2.json + connection resources | [references/bindings-v2-sync.md](references/bindings-v2-sync.md) |
| Refresh entry-points.json input/output from In/Out args | [references/entry-points-sync.md](references/entry-points-sync.md) |

### Plugin Index

**Structural:**

| Plugin | Scope |
|--------|-------|
| [case](references/plugins/case/planning.md) | Root case (T01) |
| [stages](references/plugins/stages/planning.md) | Regular (primary) and secondary stages |
| [sla](references/plugins/sla/planning.md) | Default SLA, conditional rules, escalation |
| [global-vars](references/plugins/variables/global-vars/planning.md) | Case variables and arguments |
| [io-binding](references/plugins/variables/io-binding/planning.md) | Task I/O wiring, cross-task refs |
| [logging](references/plugins/logging/impl-json.md) | Shared issue log |

**Tasks** (`references/plugins/tasks/`):

> **Naming asymmetry — read carefully.** Three names exist for connector + timer tasks. Pick the right one by column. Schema-kebab is the only value that goes into `caseplan.json` `type` (Rule 16).

| sdd.md `Type:` value / caseplan.json `type` (schema-kebab) | Plugin folder | CLI `--type` flag (`tasks describe`) |
|---|---|---|
| `process` | [process](references/plugins/tasks/process/planning.md) | `process` |
| `agent` | [agent](references/plugins/tasks/agent/planning.md) | `agent` |
| `rpa` | [rpa](references/plugins/tasks/rpa/planning.md) | `rpa` |
| `action` | [action](references/plugins/tasks/action/planning.md) | `action` |
| `api-workflow` | [api-workflow](references/plugins/tasks/api-workflow/planning.md) | `api-workflow` |
| `case-management` | [case-management](references/plugins/tasks/case-management/planning.md) | `case-management` |
| `execute-connector-activity` | [connector-activity](references/plugins/tasks/connector-activity/planning.md) | `connector-activity` |
| `wait-for-connector` | [connector-trigger](references/plugins/tasks/connector-trigger/planning.md) | `connector-trigger` |
| `wait-for-timer` | [wait-for-timer](references/plugins/tasks/wait-for-timer/planning.md) | `wait-for-timer` (no CLI describe needed) |

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

> **Connector-bound rules:** a `wait-for-connector` rule in any condition scope must carry the connector configuration under `rule.uipath` (built from `case spec --type trigger`, like the connector-trigger task) — bare connector rules are invalid in Studio Web and are NOT caught by CLI `validate`. See [connector-trigger-common.md § Target: connector-bound condition rule](references/connector-trigger-common.md#target-connector-bound-condition-rule).

## Anti-patterns

- **Do NOT leave a regular stage without an entry condition.** With edges retired (Rule 20), stage entry conditions are the sole reachability contract. Every regular stage needs ≥1 `stage-entry-conditions` rule naming a reachable predecessor; the first stage carries `case-entered`. A stage with no entry condition is orphaned and unreachable.
- **Do NOT validate after each T-entry.** Intermediate states expected invalid. Run `validate` once at end of Phase 2 (informational) and once in Phase 4 (authoritative).
- **`tasks.md` (Phase 1) uses per-section batched Edit-append — NOT per-T-entry, NOT one mega-Write.** One Read + N Edit-appends per section (§4.2.1 vars, §4.3 triggers, §4.4 stages, §4.6 tasks, §4.7 conditions, §4.8 SLA). No re-Read between sibling Edits. **HARD CAP:** after §4.0a Step 1 Seed Write (<1KB header), single Write of whole `tasks.md` is FORBIDDEN regardless of size. Single Edit-append payload >30KB also FORBIDDEN — split per section even if cumulative payload exceeds 30KB. A 96KB tasks.md Write costs ~360s in one turn (20% of session); section-batched Edit-appends spread across ~7 turns of ~50s. TaskUpdate per T-entry preserves audit trail. Recovery on interruption: re-Read `tasks.md`, resume from next un-applied T-entry. See [planning.md § 4.0a](references/planning.md).
- **`caseplan.json` (Phase 2 + 3) uses per-section batched writes — NOT per-T-entry.** One Read at section entry + one validate at section end. Tool primitive scales with section size: **<10 T-entries** → N Edits (one per T-entry, no re-Read between siblings); **≥10 T-entries** → may use single whole-section Write covering the section's nodes array at once, AFTER composing complete section state in reasoning. Untouched siblings (other sections, root fields) MUST be preserved verbatim from the Read — drop nothing. TaskUpdate per T-entry preserves audit trail regardless of write granularity. CLI-gated sections (Phase 2 §4.6 non-connector `tasks describe`, Phase 3 §9.7 connector `case spec`) use gather-then-write. Recovery on interruption: re-Read both files, resume from next un-applied T-entry. Full contract in [case-editing-operations.md § Per-section batch write contract](references/case-editing-operations.md#per-section-batch-write-contract--canonical) and [implementation.md § Per-plugin execution](references/implementation.md).
- **Do NOT emit standalone text-only assistant turns between tool calls.** Status/progress text MUST share its turn with the next `tool_use` (text block + tool_use block in the same assistant content array). Standalone narration turns each pay full inference latency + prompt cache replay (~5s + ~250K cache-read tokens per turn) for no incremental progress. Cap inline status to ≤1 sentence / ~20 tokens. Per-T-entry audit lives in TaskUpdate, NOT in narration.
  - **HARD TOKEN CAP on any single text block: 200 tokens, no exceptions outside the allow-list below.** Allow-listed text blocks (the once-per-run kickoff flow overview, hard-stop AskUserQuestion preambles, Phase 5/6 completion reports, `Publish for review` DesignerUrl print, post-validate result summaries) get a higher ceiling of **500 tokens** — never higher. A text block >200 tokens outside the allow-list, or >500 tokens inside it, is a planning monologue, regardless of content or framing.
  - **Forbidden announcement verbs.** Text blocks (bundled or standalone) starting with `Building`, `Composing`, `Writing`, `Drafting`, `Generating`, `Now I'll`, `Next:`, `Next step:`, `Approach:`, `Strategy:`, `Plan:`, `Caveman push:`, `Big single Write:`, `Let me`, or any other narration of the imminent tool call are FORBIDDEN regardless of length. The tool_use input shows what is being built — restating it in prose is pure cost. If the agent feels the urge to write `Composing Phase 2 caseplan.json — trigger + 64 variables + 10 stages`, it must instead invoke the Write directly with that content as the file body.
  - **Allow-listed exceptions** (may stand alone, capped at 500 tokens): the once-per-run kickoff flow overview, hard-stop AskUserQuestion preambles, final completion reports (Phase 5/6 exit), Phase 2 `Publish for review` DesignerUrl print (Rule 11), and post-validate result summaries (`N errors, M warnings — fixing X` is fine; `Composing fix for ...` is not). Everything else bundles or omits.
- **Sequential task toggle matches the frontend.** `runs-sequentially` is a task entry rule, not a stage flag and not a lane marker. Preserve the ordered tasks in the stage's `data.tasks` structure and write one `entryConditions` entry containing only `rules: [[{ "rule": "runs-sequentially" }]]` for every task selected as sequential. The first task's rule means current-stage-entered; each later task's rule means the preceding task completes. Do not add `current-stage-entered` alongside the sequential rule. `data.tasks` grouping is structural/layout state; never use lane-sharing to express sequence.
- **Task mode is a semantic choice, not a visual layout choice.** Map the frontend task selector as follows: `sequential` → one `runs-sequentially` entry rule per task in declaration order; `event-triggered` → an event/condition-driven task (use `wait-for-connector` for an external connector event, or the explicitly authored condition; never infer sequentiality); `manually-triggered` / `adhoc` → one `adhoc` entry rule, `isRequired: false`, started by a user from the Case App, with no additional entry events. Never model an adhoc task as event-triggered or sequential, and never add `adhoc` to a stage-entry condition.
- **Secondary stages are interrupting exception lanes, not inline primary stages.** Use the same `case-management:Stage` node with `data.stageType: "secondary"`; set `isRequired: false`, give it a condition-driven entry, and use it for exception, optional, rework, or special handling that may be entered while the main case is active. Secondary stages cannot be connected to other stages as a normal flow edge; a returning lane completes with `return-to-origin` and must be interrupting. Do not count a secondary stage in the happy-path `required-stages-completed` completion set.
- **Case completion is a root rule, separate from stage completion.** The case must have at least one `metadata.caseExitRules[]` entry with `marksCaseComplete: true` (normally `required-stages-completed`). A stage exit with `marksStageComplete: true` only completes that stage; it does not close the case. Non-completing outcomes such as rejection or withdrawal use separate case-exit rules with `marksCaseComplete: false`.
- **Do NOT edit the auto-generated `caseplan.json.bpmn`.** Regenerated by validate/pack, will be overwritten. Author only `caseplan.json`.
- **Case file is flat at `<Solution>/<Project>/caseplan.json` — never under `content/`.** `content/` is the packed `.nupkg` layout (`package-descriptor.json`), not on-disk. Never `mkdir content` or author the root caseplan via `uip maestro case cases add` — write `caseplan.json` directly ([impl-json.md](references/plugins/case/impl-json.md)).
- **Do NOT fabricate expression syntax for conditional SLA rules.** Describe condition in natural language; execution phase determines exact form.
- **Do NOT place `tasks/` inside the solution or project directory.** `tasks/` (and its `tasks.md`, `registry-resolved.json`) lives next to `sdd.md` at the working root — NOT inside `<Solution>/` or `<Solution>/<Project>/`. The case file path (`<Solution>/<Project>/caseplan.json`) does NOT root the planning artifacts; they track `sdd.md`, not `caseplan.json`.
- **Do NOT invoke other skills automatically — except the inline-create path.** If case needs a regular RPA process / action / child case / connector / agentic process that doesn't exist, emit placeholder task (Rule 8) and list missing resources in completion report; on-demand creation of those kinds is a future milestone. **Exception (agent + API workflow):** when the user picks `Create` at the Rule 17 gate, the skill builds the missing agent / API workflow inline by spawning a sub-agent that invokes `uipath-agents` (agent) or `uipath-api-workflow` (API workflow) — gate-selected only, never from SDD content alone. The `uipath-planner` handoff stays plain-text (Rule 15).

> **Trouble?** Use `/uipath-feedback` to send report.

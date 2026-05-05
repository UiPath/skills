---
name: uipath-maestro-case
description: "UiPath Case Management authoring (caseplan.json) from sdd.md, or via lightweight interview if sdd.md absent. Produces tasks.md plan, writes caseplan.json via per-plugin JSON recipes. For .xaml→uipath-rpa, .flow→uipath-maestro-flow. For PDD→SDD or complex/multi-product→uipath-solution-design."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, AskUserQuestion
---

# UiPath Case Management Authoring Assistant

> **Preview** — skill is under active development; surface and behavior may change.

Builds UiPath Case Management definitions from `sdd.md`. Generates `tasks.md` plan, then writes `caseplan.json` directly via per-plugin JSON recipes. CLI is reserved for read-only metadata fetches (registry, validate, debug, tasks describe, is describe) and solution boundary operations (`uip solution new` / `project add` / `upload`).

When `sdd.md` is absent, **Phase 0 interview** generates one interactively from a lightweight 4-round Q&A (open describe → skeleton + gap-fill → registry resolution → review). Complex / multi-product cases redirect to `uipath-solution-design` — see [references/phase-0-interview.md § Thresholds](references/phase-0-interview.md#thresholds) for caps.

**Scope:** new case from `sdd.md` (user-provided or Phase 0-generated). Modifying existing case not supported (no remote fetch tooling).

## When to Use This Skill

- User provides `sdd.md` and wants Case Management project built
- User asks to create new case management project but has no `sdd.md` (Phase 0 interview generates one)
- User asks to create new case management project or definition
- User asks to generate implementation tasks from `sdd.md` or convert spec to plan
- User asks about case management JSON schema — nodes, edges, tasks, rules, SLA
- User wants to manage runtime case instances (list, pause, resume, cancel) — see [references/case-commands.md](references/case-commands.md)

**Do not use for:** `.xaml` → `uipath-rpa`. `.flow` → `uipath-maestro-flow`. Standalone agents/APIs/processes outside case context → corresponding UiPath skill.

## Critical Rules

1. **Phase 0 interview when `sdd.md` absent.** Generate `sdd.md` via 4-round lightweight Q&A; output requires explicit user approval (Round 4 hard-stop) before treating as Rule 2 input. Apply complexity thresholds — soft-redirect to `uipath-solution-design` on breach. Never overwrite an existing `sdd.md`. See [references/phase-0-interview.md § Thresholds](references/phase-0-interview.md#thresholds).
2. **sdd.md is sole input post-Phase-0.** After Phase 0 approval (or when user-provided), trust as written. Skill does not validate or gap-fill. If ambiguous, use AskUserQuestion — never infer silently.
3. **Run `uip maestro case registry pull` before planning.** Discovery reads cache files at `~/.uipcli/case-resources/<type>-index.json` directly. `registry search` has known gaps (esp. action-apps). See [references/registry-discovery.md](references/registry-discovery.md).
4. **`--output json` on every parsed read.**
5. **Follow plugin per node type.** Open matching `planning.md` during planning + `impl-json.md` during execution. Never guess JSON shapes from memory.
6. **`tasks.md` declarative only.** No shell commands inside. Field names use plain identifiers (e.g., `type:`, `displayName:`, `lane:`), not CLI flag syntax. One T-entry per sdd.md declaration — every stage, edge, task, trigger, condition, SLA rule, **variable, and argument** gets own T-number, even when value looks like default (`current-stage-entered`, `case-entered`, `exit-only`, `is-interrupting: false`, `runOnlyOnce: true`, `marks-stage-complete: true`). Never group, never silently omit. **When an sdd.md row's format is unrecognized, ambiguous, or cannot be categorized — invoke AskUserQuestion before skipping. Silent omission is forbidden.** Always regenerate from scratch. See [`references/planning.md` §4.0](references/planning.md).
7. **HARD STOP after `tasks.md`.** AskUserQuestion: `Approve and proceed` / `Request changes`. Re-read `tasks.md` before executing.
8. **Unresolved resource → skeleton, never fabricate IDs.** Keep `<UNRESOLVED: ...>` markers in `tasks.md`. Skeleton **task**: node with `type` + `displayName` + structural fields, `data: {}`; conditions still reference the TaskId. Skeleton **event trigger**: node with render fields + `data.uipath: { serviceType: "Intsvc.EventTrigger" }` only (no other `data.uipath` keys); `entry-points.json` entry appended; trigger-edge to first stage created. See [references/skeleton-tasks.md](references/skeleton-tasks.md) and [references/plugins/triggers/event/impl-json.md § Skeleton fallback](references/plugins/triggers/event/impl-json.md).
9. **Persist every registry resolution to `registry-resolved.json`** — search query, all matches, selected result, rationale.
10. **Cross-task refs:** `"Stage Name"."Task Name".output_name` in planning, resolve to `=vars.<outputVarId>` at execution by reading source's `var` field. Discover output names via `uip maestro case tasks describe` — never fabricate. See [references/bindings-and-expressions.md](references/bindings-and-expressions.md) and [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md).
11. **HARD STOP between Phase 2 (Prototyping) and Phase 3 (Implementation) — unconditional, every run.** Run informational `validate` (no `--mode`), surface counts, present AskUserQuestion: `Publish for review` / `Skip publish and continue` / `Abort`. Do NOT halt on Phase 2 validate errors — unbound inputs/missing conditions/missing SLA expected. Never skip prompt for auto mode, non-interactive mode, prior approval. If harness forbids prompts, halt with error. **On `Publish for review`: print `DesignerUrl` as plain-text output BEFORE invoking the second AskUserQuestion — never embed URL only inside question body.** Additional hard stops gate Phase 4 retry exhaustion (`Retry with fix` / `Pause for manual edit` / `Abort`), Phase 5 entry (`Run debug session` / `Skip to Publish`), and Phase 6 entry (`Publish to Studio Web` / `Done`). Full contract in [`references/phased-execution.md`](references/phased-execution.md).
12. **Never run `uip maestro case debug` automatically.** Executes case for real — emails, messages, API calls. Explicit user consent only.
13. **All skill artifacts: Read + Write/Edit only.** Applies to `caseplan.json`, `sdd.md`, `sdd.draft.md`, `tasks.md`, `tasks/registry-resolved.json`, `bindings_v2.json`, `id-map.json`, `entry-points.json`, `build-issues.md`. No `python`, `node`, `jq`, `sed`, `awk`, or scripts that open/parse/modify/save these files. **Specifically forbidden** (common slip): `node -e "...fs.writeFileSync..."`, `node -e "...fs.readFileSync..."`, `node -e "..." > <artifact>`, `jq '...' <artifact> > <artifact>`, `python -c "...open(...,'w')..."`, `sed -i`, `awk -i inplace`, or any shell redirection (`>`, `>>`, `| tee`) onto a skill artifact regardless of interpreter. Bash subprocesses OK ONLY for UUID v4 generation (`node -e "console.log(crypto.randomUUID())"` for `operate.json.projectId` and `entry-points.json` `uniqueId` — subprocess MUST NOT `require('fs')` or use redirection), CLI metadata fetches, validate, debug, and solution scaffold/upload. **Prefixed IDs (`Stage_`, `t`, `Rule_`, etc.) are picked inline by the agent — no subprocess.** See [references/case-editing-operations.md § Tool usage](references/case-editing-operations.md#tool-usage--mandatory).
14. **Always run `uip solution resource refresh` before `uip solution upload` or `uip maestro case debug`** — syncs resources from `bindings_v2.json` so Studio Web can resolve connector dependencies.
15. **Never auto-invoke `uipath-solution-design`.** On Phase 0 threshold breach or stuck-round detection, print plain-text suggestion of the skill name. User re-invokes manually. No tool-call cross-skill handoff.
16. **Caseplan task `type` enum is closed — 9 values, schema-kebab.** Any task node written into `caseplan.json` MUST have `type` exactly one of: `process` | `agent` | `rpa` | `action` | `api-workflow` | `case-management` | `execute-connector-activity` | `wait-for-connector` | `wait-for-timer`. **Never** write the plugin folder name (`connector-activity`, `connector-trigger`) or the CLI `--type` flag value into the JSON node — those name the planning artifacts, not the schema. Never write `external-agent`, `wait-for-event`, or any hallucinated value — there is no plugin to back them. See [references/case-schema.md § Task type](references/case-schema.md) and the Plugin Index naming-asymmetry table below.
17. **Schema version: default v19, opt-in v20, alpha-tenant forced v20.** Skill emits v19 (`{ root, nodes, edges }`) by default. Emits v20 (`{ id, version: "20.0.0", name, metadata, bindings, variables, nodes, edges, layout }`) when ANY of: (a) **Tenant override** — Phase 1 Step 1's `uip login status --output json` returns `Data.UIPATH_URL == "https://alpha.uipath.com"` (exact case-sensitive match). Forces v20 regardless of user prompt; cannot be downgraded by prompt phrasing. (b) **Prompt phrase** — the user message that activated the skill contains one of these case-insensitive substrings: `v20 schema`, `schema v20`, `use v20`, `emit v20`, `generate v20`, `unified schema`, `schema 20.0.0`. Resolution order is (a) before (b); first match wins. **Detection scope for (b) is the activating message only** — never infer from sdd.md content, file paths, or any subsequent message. **Detection scope for (a) is the Step 1 login-status response only** — do not re-query mid-build. When v20 is selected by either path, Phase 1 Step 2 writes `Schema: v20` as the first non-comment line of `tasks.md`; otherwise writes `Schema: v19`. Re-entry protocol re-reads this header to recover the choice across hard stops. caseplan.json self-identifies via its top-level `version` literal. **Mid-flight schema switch forbidden** — user must re-run from Phase 1 (Rule 6 regenerate-from-scratch applies); changing tenant or prompt mid-build does not re-flip the header. v20 mode softens Phase 4 to informational (no retry-cap hard stop) and prints downstream-CLI-may-reject warnings before Phase 5/6 prompts. See [`references/phased-execution.md` § v20 mode](references/phased-execution.md) and [`references/case-schema.md` § Top-level shape](references/case-schema.md).
18. **v20 layout-strip — node/edge layout state lives in top-level `layout`, not on the node/edge.** In v20 mode, do NOT emit node-level `position`, `style`, `measured`, `width`, `height`, `zIndex`. Do NOT compute stage `position.x = 100 + count * 500`. Do NOT emit edge `data.waypoints`. Emit top-level `layout: {}` (empty object) — FE auto-layouts on canvas load. The frontend's `transformCaseInMemoryJsonToDiskJson` strips these fields anyway when round-tripping through canvas; emitting them is harmless on read but wastes tokens. v19 mode preserves all current render-field rules (Pre-flight Checklist Items 3, 4 in [`references/case-editing-operations.md`](references/case-editing-operations.md)). See [`references/case-editing-operations.md` § v20 layout-strip](references/case-editing-operations.md).

## Workflow

Up to six hard stops (Phase 0 + Phase 4 conditional): **Phase 0** (interview → sdd.md, only when sdd.md absent) → approve → **Phase 1 Planning** (sdd.md → tasks.md) → approve → **Phase 2 Prototyping** (skeleton) → publish-for-review stop → **Phase 3 Implementation** (detail) → **Phase 4 Validate** (retry-cap stop on 3rd failure) → **Phase 5 Debug** (Run vs Skip-to-Publish stop) → **Phase 6 Publish** (Publish vs Done stop).

### Phase 0 — Interview (conditional)

Triggered when `sdd.md` absent at resolved path. Read [references/phase-0-interview.md](references/phase-0-interview.md) for round structure, thresholds, soft-redirect contract, and resumption. Produces:

- `sdd.md` — generated via 4-round Q&A, fills `assets/templates/sdd-template.md`
- `tasks/registry-resolved.json` — per-task registry resolutions from Round 3
- `sdd.draft.md` — intermediate, deleted on approval

If `sdd.md` already exists: skip Phase 0, hand to Phase 1 unchanged.

### Phase 1 — Planning

Read [references/planning.md](references/planning.md). Produces:

- `tasks/tasks.md` — T-numbered entries (stages → edges → tasks → conditions → SLA)
- `tasks/registry-resolved.json` — audit trail

HARD STOP: AskUserQuestion approval. Loop on `Request changes`.

### Phase 2 — Prototyping

Read [references/implementation.md](references/implementation.md) + [references/phased-execution.md](references/phased-execution.md). Builds structural shape only:

1. Solution + project + root case (Step 6)
2. Triggers — manual / timer / event, including skeleton event triggers per Rule 8 (Step 6.1)
3. Global variables + arguments (Step 6.2) — including In arguments whose `elementId` references a `TriggerId` captured in Step 6.1
4. Stages (Step 7), edges (Step 8)
5. Tasks — shape only (Step 9): non-connector with full `data.inputs[]` schema + empty values; connector with `typeId` + `connectionId` only (no `is describe`); unresolved as skeletons per Rule 8
6. Informational validate (Step 9.5.1) — do NOT halt on errors/warnings
7. **HARD STOP** (Step 9.5.2–9.5.5): `Publish for review` / `Skip publish and continue` / `Abort`. On `Publish`: `uip solution resource refresh --solution-folder <SolutionDir> --output json` then `uip solution upload`, print DesignerUrl, AskUserQuestion: `Continue to phase 3` / `Abort`. On `Abort`: dump `build-issues.md`, exit (no cleanup).

### Phase 3 — Implementation

Re-read `tasks.md` AND `caseplan.json` (Step 9.6). Then:

1. Connector schema + defaults (Step 9.7) — `is resources/triggers describe`
2. I/O binding all task classes (Step 9.8) — per [`plugins/variables/io-binding/impl-json.md`](references/plugins/variables/io-binding/impl-json.md)
3. Conditions all 4 scopes (Step 10)
4. SLA + escalation (Step 11)

No hard stop on Phase 3 exit — proceed directly to Phase 4.

### Phase 4 — Validate

1. Full validate (Step 12). Retry up to 3×; on 3rd failure **HARD STOP** AskUserQuestion: `Retry with fix` / `Pause for manual edit` / `Abort`
2. Dump `build-issues.md` (Step 12.1)

### Phase 5 — Debug

Completion report + **HARD STOP** AskUserQuestion (Step 13): `Run debug session` / `Skip to Publish`. On `Run`: `uip solution resource refresh` then `uip maestro case debug` (never auto-run — Rule 12). Loop on completion until `Skip to Publish`.

### Phase 6 — Publish

**HARD STOP** AskUserQuestion (Step 14): `Publish to Studio Web` / `Done`. On `Publish`: `uip solution resource refresh` then `uip solution upload`, print DesignerUrl (Step 15). Exit on either choice.

## Reference Navigation

| I need to... | Read |
|---|---|
| Generate sdd.md interactively when none provided | [references/phase-0-interview.md](references/phase-0-interview.md) |
| Plan tasks from sdd.md | [references/planning.md](references/planning.md) |
| Execute tasks.md into a case | [references/implementation.md](references/implementation.md) |
| Phase 2 → 3 → 4 → 5 → 6 split + hard stop contracts | [references/phased-execution.md](references/phased-execution.md) |
| Schema v19 vs v20 (Rules 17, 18) — mapping, layout-strip, mode behavior | [references/case-schema.md § Top-level shape](references/case-schema.md), [references/phased-execution.md § v20 mode](references/phased-execution.md) |
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

## Anti-patterns

- **Do NOT leave stages without an inbound edge.** Orphaned and unreachable. Every stage needs ≥1 inbound edge from Trigger or another stage.
- **Do NOT validate after each T-entry.** Intermediate states expected invalid. Run `validate` once at end of Phase 2 (informational) and once in Phase 4 (authoritative).
- **Do NOT batch multiple T-entries into one JSON write.** Each T-entry: own Read → mutate → Write cycle. Composing large in-memory JSON across stages/edges/tasks hides intermediate state, breaks review.
- **Do NOT place multiple tasks in same lane.** FE renders same-lane tasks stacked — unreadable. Each task own `lane` index in `stageNode.data.tasks[laneIndex][]`. Lane is layout only, no execution semantics.
- **Do NOT edit `content/*.bpmn`.** Auto-generated, will be overwritten. Edit `content/*.json` only.
- **Do NOT fabricate expression syntax for conditional SLA rules.** Describe condition in natural language; execution phase determines exact form.
- **Do NOT invoke other skills automatically.** If case needs process/agent/action that doesn't exist, emit skeleton task (Rule 8) and list missing resources in completion report. On-demand resource creation is future milestone.

> **Trouble?** Use `/uipath-feedback` to send report.
